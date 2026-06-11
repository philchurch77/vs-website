import json
import re

from django.contrib.auth.decorators import login_required
from django.db.models import Max
from django.http import HttpResponse, JsonResponse, StreamingHttpResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.utils.crypto import get_random_string
from django.views.decorators.csrf import csrf_exempt

from myproject.core.models import ChatTurn
from myproject.core.sessions import get_or_create_session_id
from myproject.core.streaming import stream_agent_deltas
from .agents import build_toolkit_agent
from .models import Flashcard

TOOL = ChatTurn.TOOL_FLASHCARDS
SESSION_KEY = "flashcards_chat_session_id"


def _user_chat_sessions(user, limit=None):
    """Past sessions for the history sidebar, newest first, with display titles."""
    sessions = (
        ChatTurn.objects
        .filter(tool=TOOL, user=user)
        .values("session_id")
        .annotate(last_message=Max("timestamp"))
        .order_by("-last_message")
    )
    if limit:
        sessions = sessions[:limit]

    sessions = list(sessions)
    for session in sessions:
        title_turn = ChatTurn.objects.filter(
            tool=TOOL, session_id=session["session_id"], user=user, role="title"
        ).first()
        if title_turn:
            session["title"] = title_turn.content
            continue
        first = (
            ChatTurn.objects
            .filter(tool=TOOL, session_id=session["session_id"], user=user)
            .exclude(role="title")
            .order_by("timestamp")
            .first()
        )
        session["title"] = (
            (first.content[:47] + "...") if first and len(first.content) > 50
            else first.content if first else "Untitled"
        )
    return sessions


@csrf_exempt
@login_required
def stream_flashcards(request):
    if request.method != "POST":
        return StreamingHttpResponse("Method Not Allowed", status=405)

    try:
        data = json.loads(request.body)
        message = data.get("message", "").strip()
        session_id = get_or_create_session_id(request, SESSION_KEY)

        chat_history = list(
            ChatTurn.objects
            .filter(tool=TOOL, user=request.user, session_id=session_id)
            .exclude(role="title")
            .order_by("timestamp")
            .values("role", "content")
        )
        chat_history.append({"role": "user", "content": message})

        toolkit_agent = build_toolkit_agent()

        def save_turns(full_response):
            ChatTurn.objects.create(
                tool=TOOL, user=request.user, session_id=session_id,
                role="user", content=message,
            )
            ChatTurn.objects.create(
                tool=TOOL, user=request.user, session_id=session_id,
                role="assistant", content=full_response,
            )

        return StreamingHttpResponse(
            stream_agent_deltas(
                toolkit_agent,
                [{"role": "system", "content": toolkit_agent.instructions}, *chat_history],
                on_complete=save_turns,
            ),
            content_type="text/plain",
        )

    except Exception:
        # Never echo exception detail to the client — it can contain
        # internal paths or fragments of the failed request.
        return StreamingHttpResponse("⚠️ Error: something went wrong. Please try again.", content_type="text/plain", status=500)


@login_required
def flashcards_page(request):
    # New chat: clear previous
    if request.GET.get("new") == "1":
        request.session["selected_flashcard_ids"] = []
        request.session[SESSION_KEY] = get_random_string(32)
        request.session.modified = True
        return redirect("flashcards:flashcards_page")

    # Load existing chat
    session_id = request.GET.get("session_id") or request.session.get(SESSION_KEY)
    request.session[SESSION_KEY] = session_id

    messages = []
    selected_ids = []

    if session_id:
        chat_turns = ChatTurn.objects.filter(
            tool=TOOL, session_id=session_id, user=request.user
        ).exclude(role="title").order_by("timestamp")
        messages = list(chat_turns.values("role", "content"))

        # Try to extract the last assistant response containing flashcard IDs
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

    return render(request, "flashcards/flashcards.html", {
        "messages": messages,
        "flashcards": flashcards,
        "chat_sessions": _user_chat_sessions(request.user),
    })


@login_required
def filtered_flashcards(request):
    selected_ids = request.session.get("selected_flashcard_ids", [])
    flashcards = Flashcard.objects.filter(flashcard_id__in=selected_ids).order_by("sort_order") if selected_ids else Flashcard.objects.none()
    html = render_to_string("flashcards/partials/flashcard_list.html", {"flashcards": flashcards})
    return JsonResponse({"html": html})


@login_required
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
def delete_chat_session(request, session_id):
    ChatTurn.objects.filter(tool=TOOL, user=request.user, session_id=session_id).delete()
    # If current session was deleted clear it
    if request.session.get(SESSION_KEY) == session_id:
        request.session[SESSION_KEY] = None
        request.session["selected_flashcard_ids"] = []
    return redirect("flashcards:flashcards_page")


@login_required
def rename_chat_session(request, session_id):
    if not ChatTurn.objects.filter(tool=TOOL, user=request.user, session_id=session_id).exists():
        return JsonResponse({"error": "Session not found"}, status=404)
    data = json.loads(request.body)
    new_title = data.get("title", "").strip()
    if new_title:
        ChatTurn.objects.filter(tool=TOOL, user=request.user, session_id=session_id, role="title").delete()
        ChatTurn.objects.create(tool=TOOL, user=request.user, session_id=session_id, role="title", content=new_title)
        return JsonResponse({"status": "ok"})
    return JsonResponse({"error": "Invalid title"}, status=400)


@login_required
def export_chat_session(request, session_id):
    turns = ChatTurn.objects.filter(tool=TOOL, session_id=session_id, user=request.user).order_by("timestamp")
    lines = [f"{turn.role.upper()}: {turn.content}" for turn in turns]
    response = HttpResponse("\n\n".join(lines), content_type="text/plain")
    response["Content-Disposition"] = f'attachment; filename="chat_{session_id}.txt"'
    return response


@login_required
def chat_history_partial(request):
    chat_sessions = _user_chat_sessions(request.user, limit=20)
    html = render_to_string("flashcards/partials/chat_history_list.html", {"chat_sessions": chat_sessions}, request=request)
    return JsonResponse({"html": html})
