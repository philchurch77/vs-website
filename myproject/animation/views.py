import json
import asyncio
import re

from django.http import StreamingHttpResponse, HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.utils.crypto import get_random_string
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string


from agents import Runner
from .agents import animation_agent
from .models import ChatTurn


@csrf_exempt
def reset_chat_session(request):
    request.session["chat_history"] = []
    request.session.pop("chat_session_id", None)
    return JsonResponse({"status": "ok"})


@login_required
def stream_animation_api(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            message = data.get("message", "").strip()
            user = request.user

            # STEP 1: Get or create session ID
            session_id = request.session.get("chat_session_id")
            if not session_id:
                session_id = get_random_string(32)
                request.session["chat_session_id"] = session_id

            # STEP 2: Load or reset session-based chat history
            chat_history = request.session.get("chat_history", [])

            if re.search(r"(?i)i am\b", message) or "start again" in message.lower():
                chat_history = []
                request.session["chat_history"] = chat_history

            # STEP 3: Save user message to DB and session
            ChatTurn.objects.create(
                session_id=session_id,
                role="user",
                content=message,
                user=user
            )
            chat_history.append({"role": "user", "content": message})
            request.session["chat_history"] = chat_history

            def stream_response():
                full_response_holder = {"content": ""}

                async def generate():
                    result = Runner.run_streamed(animation_agent, input=[
                        {"role": "system", "content": animation_agent.instructions},
                        *chat_history
                    ])
                    async for event in result.stream_events():
                        if event.type == "raw_response_event" and hasattr(event.data, "delta"):
                            delta = event.data.delta
                            full_response_holder["content"] += delta
                            yield delta

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                agen = generate()

                def generator():
                    try:
                        while True:
                            chunk = loop.run_until_complete(agen.__anext__())
                            yield chunk
                    except StopAsyncIteration:
                        full_response = full_response_holder["content"]

                        # STEP 4: Save assistant reply
                        ChatTurn.objects.create(
                            session_id=session_id,
                            role="assistant",
                            content=full_response,
                            user=user
                        )
                        chat_history.append({"role": "assistant", "content": full_response})
                        request.session["chat_history"] = chat_history



                    finally:
                        loop.close()

                return generator()

            return StreamingHttpResponse(stream_response(), content_type="text/plain")

        except Exception as e:
            return StreamingHttpResponse(f"⚠️ Error: {str(e)}", content_type="text/plain", status=500)

    return StreamingHttpResponse("Method Not Allowed", status=405)


@login_required
def chat_page(request):
    user = request.user

    # Reset to clean chat session
    chat_turns = []
    request.session["chat_session_id"] = None
    request.session["chat_history"] = []

    return render(request, "animation/animationchat.html", {
        "chat_turns": chat_turns
    })


@login_required
def chat_session(request, session_id):
    user = request.user
    chat_turns = ChatTurn.objects.filter(session_id=session_id, user=user).order_by("timestamp")

    # Restore session state
    request.session["chat_session_id"] = session_id
    request.session["chat_history"] = [
        {"role": turn.role, "content": turn.content} for turn in chat_turns
    ]

    return render(request, "animation/animationchat.html", {
        "chat_turns": chat_turns
    })


@login_required
def new_chat_session(request):
    request.session["chat_session_id"] = get_random_string(32)
    request.session["chat_history"] = []
    return redirect("animation:chat_page")


