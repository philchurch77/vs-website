"""Shared streaming machinery for the AI chat tools.

Both the flashcards and evaluation views stream agent output to the
browser via StreamingHttpResponse. The agents SDK is async; this module
runs the stream inside a dedicated event loop so it can be consumed from
a synchronous response generator. Do not convert the views to
synchronous responses — streaming is a project requirement (CLAUDE.md).
"""
import asyncio

from agents import Runner


def stream_agent_deltas(agent, input_messages, on_complete=None):
    """Yield text deltas from a streamed agent run.

    ``on_complete(full_response)`` is called once the stream finishes —
    use it to persist chat turns. If it returns an iterable of strings,
    those are streamed to the client after the agent output (e.g. a
    "[SUMMARY_SAVED]" marker).
    """

    async def _agen():
        result = Runner.run_streamed(agent, input=input_messages)
        async for event in result.stream_events():
            if event.type == "raw_response_event" and hasattr(event.data, "delta"):
                yield event.data.delta

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    full_response = ""
    try:
        agen = _agen()
        try:
            while True:
                chunk = loop.run_until_complete(agen.__anext__())
                full_response += chunk
                yield chunk
        except StopAsyncIteration:
            if on_complete is not None:
                extra_chunks = on_complete(full_response)
                if extra_chunks:
                    yield from extra_chunks
    finally:
        loop.close()
