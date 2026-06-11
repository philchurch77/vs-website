import json
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from myproject.testing import make_fake_runner
from .models import ChatTurn, TrainingSummary

User = get_user_model()


class EvaluationAuthTests(TestCase):
    """All evaluation views except reset_chat_session must require login."""

    def setUp(self):
        self.user = User.objects.create_user(username="alice", password="pass")

    def test_chat_page_requires_login(self):
        response = self.client.get(reverse("evaluation:chat_page"))
        self.assertEqual(response.status_code, 302)

    def test_stream_requires_login(self):
        # stream_chatgpt_api is @login_required even though it accepts POSTs from JS
        response = self.client.post(
            reverse("evaluation:stream_chat"),
            data=json.dumps({"message": "hello"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 302)

    def test_chat_session_requires_login(self):
        response = self.client.get(reverse("evaluation:chat_session", args=["fake-session"]))
        self.assertEqual(response.status_code, 302)

    def test_new_chat_session_requires_login(self):
        response = self.client.get(reverse("evaluation:new_chat_session"))
        self.assertEqual(response.status_code, 302)

    def test_chat_history_partial_requires_login(self):
        response = self.client.get(reverse("evaluation:chat_history_partial"))
        self.assertEqual(response.status_code, 302)

    def test_reset_chat_session_is_accessible_without_login(self):
        # reset_chat_session has no @login_required — this test documents the current
        # behaviour. Consider adding @login_required to prevent unauthenticated session resets.
        response = self.client.post(reverse("evaluation:reset_chat_session"))
        self.assertNotEqual(response.status_code, 302)


class EvaluationSessionIsolationTests(TestCase):
    """A user must not be able to read another user's chat history or summaries."""

    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="pass")
        self.intruder = User.objects.create_user(username="intruder", password="pass")
        self.session_id = "owner-eval-session-xyz789"
        ChatTurn.objects.create(user=self.owner, session_id=self.session_id, role="user", content="Private reflection")
        ChatTurn.objects.create(user=self.owner, session_id=self.session_id, role="assistant", content="Private response")
        TrainingSummary.objects.create(
            user=self.owner,
            title="Owner summary",
            school_or_trust="Owner School",
            summary_text="Confidential summary content",
            session_id=self.session_id,
        )

    def test_intruder_cannot_read_owner_chat_session(self):
        # chat_session filters by user=request.user — intruder must see no turns
        self.client.login(username="intruder", password="pass")
        response = self.client.get(reverse("evaluation:chat_session", args=[self.session_id]))
        self.assertEqual(response.status_code, 200)
        self.assertQuerySetEqual(response.context["chat_turns"], ChatTurn.objects.none())

    def test_intruder_cannot_see_owner_summaries_in_chat_page(self):
        # chat_page filters summaries by user=request.user
        self.client.login(username="intruder", password="pass")
        response = self.client.get(reverse("evaluation:chat_page"))
        self.assertEqual(response.status_code, 200)
        for summary in response.context["summaries"]:
            self.assertEqual(summary.user, self.intruder)

    def test_owner_can_see_own_summary(self):
        self.client.login(username="owner", password="pass")
        response = self.client.get(reverse("evaluation:chat_page"))
        self.assertEqual(response.status_code, 200)
        pks = [s.pk for s in response.context["summaries"]]
        self.assertTrue(any(pks))

    def test_history_partial_only_shows_own_summaries(self):
        self.client.login(username="intruder", password="pass")
        response = self.client.get(reverse("evaluation:chat_history_partial"))
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b"Owner summary", response.content)


class EvaluationStreamTests(TestCase):
    """The streaming endpoint must stream agent output and persist both turns."""

    def setUp(self):
        self.user = User.objects.create_user(username="alice", password="pass")
        self.client.login(username="alice", password="pass")

    def _stream(self, message, deltas):
        with patch("myproject.evaluation.views.Runner", make_fake_runner(deltas)):
            response = self.client.post(
                reverse("evaluation:stream_chat"),
                data=json.dumps({"message": message}),
                content_type="application/json",
            )
            return b"".join(response.streaming_content).decode()

    def test_stream_saves_user_and_assistant_turns(self):
        body = self._stream("My training was great", ["Thanks ", "for sharing"])
        self.assertEqual(body, "Thanks for sharing")
        turns = ChatTurn.objects.filter(user=self.user).order_by("timestamp")
        self.assertEqual(turns.count(), 2)
        self.assertEqual(turns[0].role, "user")
        self.assertEqual(turns[0].content, "My training was great")
        self.assertEqual(turns[1].role, "assistant")
        self.assertEqual(turns[1].content, "Thanks for sharing")

    def test_summary_response_creates_training_summary(self):
        body = self._stream(
            "Please summarise",
            ["Lovely work this term!\nEND OF SUMMARY:\nSchool or Trust: Test Academy"],
        )
        self.assertIn("[SUMMARY_SAVED]", body)
        summary = TrainingSummary.objects.get()
        self.assertEqual(summary.user, self.user)
        self.assertEqual(summary.school_or_trust, "Test Academy")
        self.assertIn("Lovely work this term!", summary.summary_text)

    def test_get_is_rejected(self):
        response = self.client.get(reverse("evaluation:stream_chat"))
        self.assertEqual(response.status_code, 405)

    def test_reset_chat_session_responds_ok(self):
        response = self.client.post(reverse("evaluation:reset_chat_session"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")
