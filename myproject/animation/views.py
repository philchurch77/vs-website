
from django.db.models import Max
from django.http import JsonResponse
import re

# Partial for chat history list (session list)
from django.template.loader import render_to_string

from django.contrib.auth.decorators import login_required

@login_required
def chat_history_partial(request):
    chat_sessions = (
        ChatTurn.objects
        .filter(user=request.user)
        .values("session_id")
        .annotate(last_timestamp=Max("timestamp"))
        .order_by("-last_timestamp")[:20]
    )


    def strip_tags(value):
        return re.sub(r'<[^>]*?>', '', value) if value else value

    for session in chat_sessions:
        # Prefer the first assistant message as the summary/title
        first_assistant = (
            ChatTurn.objects
            .filter(session_id=session["session_id"], user=request.user, role="assistant")
            .order_by("timestamp")
            .first()
        )
        if first_assistant and first_assistant.content:
            plain = strip_tags(first_assistant.content)
            session["title"] = (plain[:47] + "...") if len(plain) > 50 else plain
        else:
            # Fallback to first user message
            first_turn = (
                ChatTurn.objects
                .filter(session_id=session["session_id"], user=request.user)
                .order_by("timestamp")
                .first()
            )
            if first_turn and first_turn.content:
                plain = strip_tags(first_turn.content)
                session["title"] = (plain[:47] + "...") if len(plain) > 50 else plain
            else:
                session["title"] = "Untitled"

    html = render_to_string("animation/partials/chat_history_list.html", {"chat_sessions": chat_sessions}, request=request)
    return HttpResponse(html)
import json
import asyncio
import re

from django.http import StreamingHttpResponse, HttpResponse, JsonResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.utils.crypto import get_random_string
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.urls import reverse
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
    session_id = request.session.get("chat_session_id")
    if not session_id:
        from django.utils.crypto import get_random_string
        session_id = get_random_string(32)
        request.session["chat_session_id"] = session_id
    chat_turns = ChatTurn.objects.filter(session_id=session_id, user=user).order_by("timestamp")
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


@login_required
def delete_chat_session(request, session_id):
    ChatTurn.objects.filter(user=request.user, session_id=session_id).delete()
    # If current session was deleted clear it
    if request.session.get("chat_session_id") == session_id:
        request.session["chat_session_id"] = None
        request.session["chat_history"] = []
    return HttpResponseRedirect(reverse("animation:chat_page"))


@login_required
def rename_chat_session(request, session_id):
    data = json.loads(request.body)
    new_title = data.get("title", "").strip()
    if new_title:
        first_turn = ChatTurn.objects.filter(session_id=session_id, user=request.user).order_by("timestamp").first()
        if first_turn:
            first_turn.content = new_title
            first_turn.save()
        return JsonResponse({"status": "ok"})
    return JsonResponse({"error": "Invalid title"}, status=400)


@login_required
def export_chat_session(request, session_id):
    turns = ChatTurn.objects.filter(session_id=session_id, user=request.user).order_by("timestamp")
    lines = [f"{turn.role.upper()}: {turn.content}" for turn in turns]
    response = HttpResponse("\n\n".join(lines), content_type="text/plain")
    response["Content-Disposition"] = f'attachment; filename="animation_chat_{session_id}.txt"'
    return response


