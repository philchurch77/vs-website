import json
import asyncio
import re
from django.http import StreamingHttpResponse, HttpResponseRedirect, HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.utils.crypto import get_random_string
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.db.models import Max
from django.contrib.auth.decorators import login_required
from django.urls import reverse

from agents import Runner
from .agents import build_toolkit_agent
from .models import ChatTurn, Flashcard


@csrf_exempt
@login_required
def stream_flashcards(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            message = data.get("message", "").strip()

            session_id = request.session.get("chat_session_id")
            if not session_id:
                session_id = get_random_string(32)
                request.session["chat_session_id"] = session_id

            chat_history = list(ChatTurn.objects.filter(session_id=session_id).order_by("timestamp").values("role", "content"))
            chat_history.append({"role": "user", "content": message})

            toolkit_agent = build_toolkit_agent()

            selected_ids = []  # ✅ move ID collection outside the generator

            def sync_stream():
                full_response = ""

                async def generate():
                    result = Runner.run_streamed(toolkit_agent, input=[
                        {"role": "system", "content": toolkit_agent.instructions},
                        *chat_history
                    ])
                    async for event in result.stream_events():
                        if event.type == "raw_response_event" and hasattr(event.data, "delta"):
                            yield event.data.delta

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                try:
                    agen = generate()
                    while True:
                        chunk = loop.run_until_complete(agen.__anext__())
                        full_response += chunk
                        yield chunk
                except StopAsyncIteration:
                    ChatTurn.objects.create(user=request.user, session_id=session_id, role="user", content=message)
                    ChatTurn.objects.create(user=request.user, session_id=session_id, role="assistant", content=full_response)

                    # ✅ Parse flashcard IDs and store in external variable
                    match = re.search(r"\[SELECTED_FLASHCARD_IDS:\s*(.*?)\]", full_response)
                    if match:
                        value = match.group(1).strip()
                        if value.lower() != "none":
                            selected_ids.extend(sorted([
                                int(m.group(1))  # use inner match object `m`
                                for x in value.split(",")
                                if (m := re.search(r"#?(\d+)#?", x.strip()))  # use a new name
                            ]))
                finally:
                    loop.close()

            response = StreamingHttpResponse(sync_stream(), content_type="text/plain")

            # ✅ Store the session AFTER the response generator is returned
            request.session["selected_flashcard_ids"] = selected_ids
            request.session.modified = True

            return response

        except Exception as e:
            return StreamingHttpResponse(f"⚠️ Error: {str(e)}", content_type="text/plain", status=500)

    return StreamingHttpResponse("Method Not Allowed", status=405)

@login_required
def flashcards_page(request):
    # New chat: clear previous
    if request.GET.get("new") == "1":
        request.session["selected_flashcard_ids"] = []
        request.session["chat_session_id"] = get_random_string(32)
        request.session.modified = True
        return redirect("flashcards:flashcards_page")

    # Load existing chat
    session_id = request.GET.get("session_id") or request.session.get("chat_session_id")
    request.session["chat_session_id"] = session_id

    messages = []
    selected_ids = []

    if session_id:
        chat_turns = ChatTurn.objects.filter(session_id=session_id, user=request.user).order_by("timestamp")
        messages = list(chat_turns.values("role", "content"))

        # 🧠 Try to extract the last assistant response containing flashcard IDs
        for turn in reversed(chat_turns):
            if turn.role == "assistant":
                match = re.search(r"\[SELECTED_FLASHCARD_IDS:\s*(.*?)\]", turn.content)
                if match:
                    raw_ids = match.group(1).strip()
                    selected_ids = (
                        [] if raw_ids.lower() == "none" else
                        [int(x.strip()) for x in raw_ids.split(",") if x.strip().isdigit()]
                    )
                break  # only process the latest assistant message

    # Store and use flashcards
    request.session["selected_flashcard_ids"] = selected_ids
    request.session.modified = True

    flashcards = Flashcard.objects.filter(flashcard_id__in=selected_ids).order_by("sort_order") if selected_ids else Flashcard.objects.all().order_by("sort_order")

    # List of past sessions
    chat_sessions = (
        ChatTurn.objects
        .filter(user=request.user)
        .values("session_id")
        .annotate(last_message=Max("timestamp"))
        .order_by("-last_message")
    )

    for session in chat_sessions:
        first = ChatTurn.objects.filter(session_id=session["session_id"], user=request.user).order_by("timestamp").first()
        session["title"] = (first.content[:47] + "...") if first and len (first.content) > 50 else first.content if first else "Untitled"

    return render(request, "flashcards/flashcards.html", {
        "messages": messages,
        "flashcards": flashcards,
        "chat_sessions": chat_sessions
    })

def filtered_flashcards(request):
    selected_ids = request.session.get("selected_flashcard_ids", [])
    flashcards = Flashcard.objects.filter(flashcard_id__in=selected_ids).order_by("sort_order") if selected_ids else Flashcard.objects.none()
    html = render_to_string("flashcards/partials/flashcard_list.html", {"flashcards": flashcards})
    return JsonResponse({"html": html})

def save_flashcard_ids(request):
    try:
        data = json.loads(request.body)
        flashcard_ids = data.get("flashcard_ids", [])
        if isinstance(flashcard_ids, list):
            request.session["selected_flashcard_ids"] = flashcard_ids
            request.session.modified = True
            return JsonResponse({"status": "success"})
        return JsonResponse({"error": "Invalid data"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@login_required
def chat_session(request, session_id):
    chat_turns = ChatTurn.objects.filter(session_id=session_id, user=request.user).order_by("timestamp")
    return render(request, "flashcards/chat_session.html", {"chat_turns": chat_turns})

@login_required
def delete_chat_session(request, session_id):
    ChatTurn.objects.filter(user=request.user, session_id=session_id).delete()
    # If current session was deleted clear it
    if request.session.get("chat_session_id") == session_id:
        request.session["chat_session_id"] = None
        request.session["selected_flaschard_ids"] = []
    return HttpResponseRedirect(reverse("flashcards:flashcards_page"))

@login_required
def rename_chat_session(request, session_id):
    data = json.loads(request.body)
    new_title = data.get("title", "").strip()
    if new_title:
        # Save the new title in a system message (or wherever you want)
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
    response["Content-Disposition"] = f'attachment; filename="chat_{session_id}.txt"'
    return response

@login_required
def chat_history_partial(request):
    chat_sessions = (
        ChatTurn.objects
        .filter(user=request.user)
        .values("session_id")
        .annotate(last_timestamp=Max("timestamp"))
        .order_by("-last_timestamp")[:20]
    )

    for session in chat_sessions:
        first_turn = (
            ChatTurn.objects
            .filter(session_id=session["session_id"], user=request.user)
            .order_by("timestamp")
            .first()
        )
        session["title"] = (
            (first_turn.content[:47] + "...") if first_turn and len(first_turn.content) > 50
            else first_turn.content if first_turn else "Untitled"
        )

    html = render_to_string("flashcards/partials/chat_history_list.html", {"chat_sessions": chat_sessions}, request=request)
    return JsonResponse({"html": html})
