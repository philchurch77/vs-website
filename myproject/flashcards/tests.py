import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

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
