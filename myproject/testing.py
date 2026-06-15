"""Test helpers shared across app test suites."""


def make_fake_anthropic_client(deltas):
    """Build a stand-in for anthropic.Anthropic that streams the given deltas.

    Mirrors the surface streaming.stream_agent_deltas relies on:
    ``client.messages.stream(...)`` returns a context manager whose
    ``text_stream`` iterates the deltas. No network calls are made.
    """

    class _Stream:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        @property
        def text_stream(self):
            return iter(deltas)

    class _Messages:
        def stream(self, **kwargs):
            return _Stream()

    class _Client:
        messages = _Messages()

    return _Client()
