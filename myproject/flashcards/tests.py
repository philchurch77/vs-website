import json
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from myproject.core.models import ChatTurn
from myproject.testing import make_fake_anthropic_client

User = get_user_model()

FLASHCARDS = ChatTurn.TOOL_FLASHCARDS


class FlashcardsAuthTests(TestCase):
    """All flashcard views must require login."""

    def setUp(self):
        self.user = User.objects.create_user(username="alice", password="pass")

    def test_flashcards_page_requires_login(self):
        response = self.client.get(reverse("flashcards:flashcards_page"))
        self.assertEqual(response.status_code, 302)

    def test_delete_session_requires_login(self):
        response = self.client.post(reverse("flashcards:delete_chat_session", args=["fake-session-id"]))
        self.assertEqual(response.status_code, 302)

    def test_export_session_requires_login(self):
        response = self.client.get(reverse("flashcards:export_chat_session", args=["fake-session-id"]))
        self.assertEqual(response.status_code, 302)

    def test_rename_session_requires_login(self):
        response = self.client.post(
            reverse("flashcards:rename_chat_session", args=["fake-session-id"]),
            data=json.dumps({"title": "New title"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 302)

    def test_stream_requires_login(self):
        response = self.client.post(
            reverse("flashcards:stream_flashcards"),
            data=json.dumps({"message": "hello"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 302)


class FlashcardsSessionIsolationTests(TestCase):
    """A user must not be able to read or modify another user's chat sessions."""

    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="pass")
        self.intruder = User.objects.create_user(username="intruder", password="pass")
        self.session_id = "owner-secret-session-abc123"
        ChatTurn.objects.create(tool=FLASHCARDS, user=self.owner, session_id=self.session_id, role="user", content="My private message")
        ChatTurn.objects.create(tool=FLASHCARDS, user=self.owner, session_id=self.session_id, role="assistant", content="Private reply")

    def test_intruder_cannot_delete_owner_session(self):
        # delete filters by user=request.user — owner's turns must survive
        self.client.login(username="intruder", password="pass")
        self.client.post(reverse("flashcards:delete_chat_session", args=[self.session_id]))
        self.assertTrue(ChatTurn.objects.filter(session_id=self.session_id, user=self.owner).exists())

    def test_intruder_cannot_export_owner_session(self):
        # export filters by user=request.user — response must not contain owner's content
        self.client.login(username="intruder", password="pass")
        response = self.client.get(reverse("flashcards:export_chat_session", args=[self.session_id]))
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b"My private message", response.content)

    def test_intruder_cannot_rename_owner_session(self):
        # rename now checks ownership first — intruder must receive 404
        self.client.login(username="intruder", password="pass")
        response = self.client.post(
            reverse("flashcards:rename_chat_session", args=[self.session_id]),
            data=json.dumps({"title": "Hijacked"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)
        self.assertFalse(
            ChatTurn.objects.filter(session_id=self.session_id, role="title", content="Hijacked").exists()
        )

    def test_intruder_cannot_read_owner_session_messages(self):
        # flashcards_page filters messages by user — loading another user's
        # session id must show an empty conversation
        self.client.login(username="intruder", password="pass")
        response = self.client.get(
            reverse("flashcards:flashcards_page"), {"session_id": self.session_id}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["messages"], [])

    def test_history_partial_lists_only_own_sessions(self):
        ChatTurn.objects.create(
            tool=FLASHCARDS, user=self.intruder, session_id="intruder-session", role="user", content="Mine"
        )
        self.client.login(username="intruder", password="pass")
        response = self.client.get(reverse("flashcards:chat_history_partial"))
        self.assertEqual(response.status_code, 200)
        html = response.json()["html"]
        self.assertIn("intruder-session", html)
        self.assertNotIn(self.session_id, html)

    def test_history_partial_excludes_other_tools_sessions(self):
        # An evaluation chat by the same user must not surface in the
        # flashcards history sidebar
        ChatTurn.objects.create(
            tool=ChatTurn.TOOL_EVALUATION, user=self.owner,
            session_id="owner-eval-session", role="user", content="Eval chat",
        )
        self.client.login(username="owner", password="pass")
        response = self.client.get(reverse("flashcards:chat_history_partial"))
        self.assertNotIn("owner-eval-session", response.json()["html"])


class FlashcardsStreamTests(TestCase):
    """The streaming endpoint must stream the agent output and persist both turns."""

    def setUp(self):
        self.user = User.objects.create_user(username="alice", password="pass")
        self.client.login(username="alice", password="pass")
        cache.clear()  # rate-limit counters must not leak between tests

    def _post_message(self, message):
        return self.client.post(
            reverse("flashcards:stream_flashcards"),
            data=json.dumps({"message": message}),
            content_type="application/json",
        )

    def test_stream_saves_user_and_assistant_turns(self):
        with patch(
            "myproject.core.streaming._get_client",
            return_value=make_fake_anthropic_client(["Hello ", "teacher"]),
        ):
            response = self.client.post(
                reverse("flashcards:stream_flashcards"),
                data=json.dumps({"message": "How do I help a dysregulated pupil?"}),
                content_type="application/json",
            )
            body = b"".join(response.streaming_content).decode()

        self.assertEqual(body, "Hello teacher")
        turns = ChatTurn.objects.filter(user=self.user).order_by("timestamp")
        self.assertEqual(turns.count(), 2)
        self.assertEqual(turns[0].role, "user")
        self.assertEqual(turns[0].content, "How do I help a dysregulated pupil?")
        self.assertEqual(turns[1].role, "assistant")
        self.assertEqual(turns[1].content, "Hello teacher")
        self.assertTrue(all(t.tool == FLASHCARDS for t in turns))
        # Both turns share the session id stored in the user's session
        session_id = self.client.session["flashcards_chat_session_id"]
        self.assertTrue(all(t.session_id == session_id for t in turns))

    def test_get_is_rejected(self):
        response = self.client.get(reverse("flashcards:stream_flashcards"))
        self.assertEqual(response.status_code, 405)

    def test_empty_message_rejected(self):
        response = self._post_message("   ")
        self.assertEqual(response.status_code, 400)

    def test_csrf_is_enforced(self):
        # The endpoint is no longer @csrf_exempt: a POST without the token must 403
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.login(username="alice", password="pass")
        response = csrf_client.post(
            reverse("flashcards:stream_flashcards"),
            data=json.dumps({"message": "hello"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)

    def test_rate_limit_returns_429(self):
        with patch("myproject.flashcards.views.RATE_LIMIT_REQUESTS", 2), patch(
            "myproject.core.streaming._get_client",
            return_value=make_fake_anthropic_client(["ok"]),
        ):
            for _ in range(2):
                response = self._post_message("hello")
                b"".join(response.streaming_content)
                self.assertEqual(response.status_code, 200)
            response = self._post_message("one too many")
        self.assertEqual(response.status_code, 429)
        self.assertIn("error", response.json())

    def test_stream_error_keeps_user_turn_and_tells_the_user(self):
        # API failures happen after the view returns; the generator must
        # surface a friendly message and still have the user turn saved.
        with patch(
            "myproject.core.streaming._get_client",
            side_effect=RuntimeError("api down"),
        ):
            response = self._post_message("Help please")
            body = b"".join(response.streaming_content).decode()

        self.assertIn("something went wrong", body)
        turns = ChatTurn.objects.filter(user=self.user)
        self.assertEqual(turns.count(), 1)
        self.assertEqual(turns.first().role, "user")
        self.assertEqual(turns.first().content, "Help please")


class FlashcardsTitleRowTests(TestCase):
    """role='title' rows name a session but must never appear as messages."""

    def setUp(self):
        self.user = User.objects.create_user(username="alice", password="pass")
        self.client.login(username="alice", password="pass")
        self.session_id = "alice-session-1"
        ChatTurn.objects.create(
            tool=FLASHCARDS, user=self.user, session_id=self.session_id,
            role="user", content="First question",
        )

    def test_rename_creates_title_row(self):
        response = self.client.post(
            reverse("flashcards:rename_chat_session", args=[self.session_id]),
            data=json.dumps({"title": "My renamed chat"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            ChatTurn.objects.filter(
                tool=FLASHCARDS, user=self.user, session_id=self.session_id,
                role="title", content="My renamed chat",
            ).exists()
        )

    def test_title_rows_excluded_from_messages(self):
        ChatTurn.objects.create(
            tool=FLASHCARDS, user=self.user, session_id=self.session_id,
            role="title", content="My title",
        )
        response = self.client.get(
            reverse("flashcards:flashcards_page"), {"session_id": self.session_id}
        )
        self.assertEqual(response.status_code, 200)
        roles = [m["role"] for m in response.context["messages"]]
        self.assertNotIn("title", roles)

    def test_page_renders_without_template_syntax_leakage(self):
        # Multi-line {# #} comments are not supported by Django and get
        # rendered as literal text — guard against that regressing
        response = self.client.get(reverse("flashcards:flashcards_page"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "{#")
        self.assertNotContains(response, "{%")

    def test_title_used_in_history_partial(self):
        ChatTurn.objects.create(
            tool=FLASHCARDS, user=self.user, session_id=self.session_id,
            role="title", content="My title",
        )
        response = self.client.get(reverse("flashcards:chat_history_partial"))
        self.assertIn("My title", response.json()["html"])
