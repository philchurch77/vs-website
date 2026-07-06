"""Shared streaming machinery for the AI chat tools.

Both the flashcards and evaluation views stream agent output to the
browser via StreamingHttpResponse. This module wraps the Anthropic
Messages API streaming helper so it can be consumed from a synchronous
response generator. Do not convert the views to synchronous responses —
streaming is a project requirement (CLAUDE.md).
"""
import logging
from dataclasses import dataclass

import anthropic

logger = logging.getLogger(__name__)

# Shown to the user if the stream dies mid-reply. Kept generic on purpose.
STREAM_ERROR_MESSAGE = (
    "\n\n⚠️ Sorry — something went wrong while generating this reply. "
    "Please try sending your message again."
)

# Generous headroom for a chat reply without risking truncation mid-answer.
# We always stream, so the SDK's non-streaming timeout guard does not apply.
MAX_TOKENS = 8192

_client = None


def _get_client():
    """Lazily build the Anthropic client.

    Constructed on first use rather than at import time so that
    management commands (migrate, collectstatic in startup.sh) don't
    fail when ANTHROPIC_API_KEY is absent. The key is read from the
    environment by the SDK.
    """
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


@dataclass(frozen=True)
class AgentConfig:
    """A chat agent: its system prompt and the model that answers.

    Replaces the old openai-agents ``Agent`` object. The system prompt
    is passed to the API separately from the conversation history (the
    Anthropic Messages API takes ``system`` as its own parameter).
    """

    system: str
    model: str
    max_tokens: int = MAX_TOKENS


def stream_agent_deltas(agent, messages, on_complete=None):
    """Yield text deltas from a streamed agent run.

    ``agent`` is an :class:`AgentConfig` carrying the system prompt and
    model. ``messages`` is the user/assistant history only — no system
    turn (that is passed separately to the API).

    ``on_complete(full_response)`` is called once the stream finishes —
    use it to persist chat turns. If it returns an iterable of strings,
    those are streamed to the client after the agent output (e.g. a
    "[SUMMARY_SAVED]" marker).

    This generator is consumed after the view has already returned, so
    exceptions here never reach the view's error handling: catch them,
    tell the user, and skip ``on_complete`` (the reply is incomplete).
    Log only the exception — never the message content (CLAUDE.md).
    """
    full_response = ""
    try:
        with _get_client().messages.stream(
            model=agent.model,
            max_tokens=agent.max_tokens,
            system=agent.system,
            messages=messages,
        ) as stream:
            for text in stream.text_stream:
                full_response += text
                yield text
    except Exception:
        logger.exception("AI stream failed")
        yield STREAM_ERROR_MESSAGE
        return

    if on_complete is not None:
        extra_chunks = on_complete(full_response)
        if extra_chunks:
            yield from extra_chunks
