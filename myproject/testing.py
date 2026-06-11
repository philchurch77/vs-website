"""Test helpers shared across app test suites."""
from types import SimpleNamespace


def make_fake_runner(deltas):
    """Build a stand-in for agents.Runner that streams the given deltas.

    Mirrors the surface the views rely on: Runner.run_streamed(agent, input=...)
    returns an object whose stream_events() async-generates raw_response_event
    items carrying a .data.delta attribute. No OpenAI calls are made.
    """

    class _Result:
        async def stream_events(self):
            for delta in deltas:
                yield SimpleNamespace(
                    type="raw_response_event",
                    data=SimpleNamespace(delta=delta),
                )

    class _Runner:
        @staticmethod
        def run_streamed(agent, input):
            return _Result()

    return _Runner
