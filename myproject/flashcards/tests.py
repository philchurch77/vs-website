import json
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from myproject.testing import make_fake_runner
from .models import ChatTurn

User = get_user_model()


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
        # stream_flashcards is @csrf_exempt but still @login_required
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
        ChatTurn.objects.create(user=self.owner, session_id=self.session_id, role="user", content="My private message")
        ChatTurn.objects.create(user=self.owner, session_id=self.session_id, role="assistant", content="Private reply")

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
            user=self.intruder, session_id="intruder-session", role="user", content="Mine"
        )
        self.client.login(username="intruder", password="pass")
        response = self.client.get(reverse("flashcards:chat_history_partial"))
        self.assertEqual(response.status_code, 200)
        html = response.json()["html"]
        self.assertIn("intruder-session", html)
        self.assertNotIn(self.session_id, html)


class FlashcardsStreamTests(TestCase):
    """The streaming endpoint must stream the agent output and persist both turns."""

    def setUp(self):
        self.user = User.objects.create_user(username="alice", password="pass")
        self.client.login(username="alice", password="pass")

    def _post_message(self, message):
        return self.client.post(
            reverse("flashcards:stream_flashcards"),
            data=json.dumps({"message": message}),
            content_type="application/json",
        )

    def test_stream_saves_user_and_assistant_turns(self):
        with patch(
            "myproject.flashcards.views.Runner", make_fake_runner(["Hello ", "teacher"])
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
        # Both turns share the session id stored in the user's session
        session_id = self.client.session["chat_session_id"]
        self.assertTrue(all(t.session_id == session_id for t in turns))

    def test_get_is_rejected(self):
        response = self.client.get(reverse("flashcards:stream_flashcards"))
        self.assertEqual(response.status_code, 405)


class FlashcardsTitleRowTests(TestCase):
    """role='title' rows name a session but must never appear as messages."""

    def setUp(self):
        self.user = User.objects.create_user(username="alice", password="pass")
        self.client.login(username="alice", password="pass")
        self.session_id = "alice-session-1"
        ChatTurn.objects.create(
            user=self.user, session_id=self.session_id, role="user", content="First question"
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
                user=self.user, session_id=self.session_id, role="title",
                content="My renamed chat",
            ).exists()
        )

    def test_title_rows_excluded_from_messages(self):
        ChatTurn.objects.create(
            user=self.user, session_id=self.session_id, role="title", content="My title"
        )
        response = self.client.get(
            reverse("flashcards:flashcards_page"), {"session_id": self.session_id}
        )
        self.assertEqual(response.status_code, 200)
        roles = [m["role"] for m in response.context["messages"]]
        self.assertNotIn("title", roles)

    def test_title_used_in_history_partial(self):
        ChatTurn.objects.create(
            user=self.user, session_id=self.session_id, role="title", content="My title"
        )
        response = self.client.get(reverse("flashcards:chat_history_partial"))
        self.assertIn("My title", response.json()["html"])
