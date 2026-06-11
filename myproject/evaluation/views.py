import json
import re

from django.http import StreamingHttpResponse, HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.utils.crypto import get_random_string
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string

from myproject.core.models import ChatTurn
from myproject.core.sessions import get_or_create_session_id
from myproject.core.streaming import stream_agent_deltas
from .agents import evaluation_agent
from .models import TrainingSummary

TOOL = ChatTurn.TOOL_EVALUATION
SESSION_KEY = "evaluation_chat_session_id"


@csrf_exempt
def reset_chat_session(request):
    # csrf_exempt because sendBeacon (page unload) cannot set headers.
    # Only act for authenticated users so a forged cross-site request
    # cannot disturb anyone's session state.
    if request.user.is_authenticated:
        request.session["chat_history"] = []
        request.session.pop(SESSION_KEY, None)
    return JsonResponse({"status": "ok"})


@login_required
def stream_chatgpt_api(request):
    if request.method != "POST":
        return StreamingHttpResponse("Method Not Allowed", status=405)

    try:
        data = json.loads(request.body)
        message = data.get("message", "").strip()
        user = request.user

        session_id = get_or_create_session_id(request, SESSION_KEY)

        # Session-based chat history, reset when the user starts over
        chat_history = request.session.get("chat_history", [])
        if re.search(r"(?i)i am\b", message) or "start again" in message.lower():
            chat_history = []
            request.session["chat_history"] = chat_history

        # Save user message to DB and session
        ChatTurn.objects.create(
            tool=TOOL, session_id=session_id, role="user", content=message, user=user
        )
        chat_history.append({"role": "user", "content": message})
        request.session["chat_history"] = chat_history

        def on_complete(full_response):
            ChatTurn.objects.create(
                tool=TOOL, session_id=session_id, role="assistant",
                content=full_response, user=user,
            )
            chat_history.append({"role": "assistant", "content": full_response})
            request.session["chat_history"] = chat_history

            if "END OF SUMMARY:" in full_response:
                school_match = re.search(r"(?i)school\s*or\s*trust\s*:\s*(.+)", full_response)
                school_or_trust_clean = school_match.group(1).strip() if school_match else "Unknown"
                title = f"{timezone.now().date().isoformat()} – {school_or_trust_clean}"

                TrainingSummary.objects.create(
                    title=title,
                    school_or_trust=school_or_trust_clean,
                    summary_text=full_response,
                    session_id=session_id,
                    user=user,
                )

                request.session["chat_history"] = []

                # Signal to frontend
                return ["\n[SUMMARY_SAVED]"]

        return StreamingHttpResponse(
            stream_agent_deltas(
                evaluation_agent,
                [{"role": "system", "content": evaluation_agent.instructions}, *chat_history],
                on_complete=on_complete,
            ),
            content_type="text/plain",
        )

    except Exception:
        # Never echo exception detail to the client — it can contain
        # internal paths or fragments of the failed request.
        return StreamingHttpResponse("⚠️ Error: something went wrong. Please try again.", content_type="text/plain", status=500)


@login_required
def chat_page(request):
    user = request.user

    # Reset to clean chat session
    chat_turns = []
    request.session[SESSION_KEY] = None
    request.session["chat_history"] = []

    summaries = TrainingSummary.objects.filter(user=user, session_id__isnull=False).order_by("-created_at")

    return render(request, "evaluation/chat.html", {
        "chat_turns": chat_turns,
        "summaries": summaries
    })


@login_required
def chat_session(request, session_id):
    user = request.user
    chat_turns = ChatTurn.objects.filter(tool=TOOL, session_id=session_id, user=user).order_by("timestamp")

    # Restore session state
    request.session[SESSION_KEY] = session_id
    request.session["chat_history"] = [
        {"role": turn.role, "content": turn.content} for turn in chat_turns
    ]

    summaries = TrainingSummary.objects.filter(user=user, session_id__isnull=False).order_by("-created_at")

    return render(request, "evaluation/chat.html", {
        "chat_turns": chat_turns,
        "summaries": summaries
    })


@login_required
def new_chat_session(request):
    request.session[SESSION_KEY] = get_random_string(32)
    request.session["chat_history"] = []
    return redirect("evaluation:chat_page")


@login_required
def chat_history_partial(request):
    summaries = TrainingSummary.objects.filter(user=request.user).order_by("-created_at")
    html = render_to_string("evaluation/partials/training_chat_history.html", {
        "summaries": summaries
    }, request=request)
    return HttpResponse(html)
