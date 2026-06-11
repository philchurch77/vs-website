from django.test import TestCase
from django.urls import reverse

from .models import TrainingRequest


class TrainingRequestTests(TestCase):
    def _valid_data(self, title="De-escalation training"):
        return {
            "title": title,
            "body": "We would like support with trauma-informed de-escalation.",
            "email": "staff@example-school.org",
        }

    def test_form_renders(self):
        response = self.client.get(reverse("training:training_request"))
        self.assertEqual(response.status_code, 200)

    def test_post_creates_request_and_redirects(self):
        response = self.client.post(
            reverse("training:training_request"), self._valid_data()
        )
        self.assertRedirects(response, reverse("training:training_request"))
        self.assertEqual(TrainingRequest.objects.count(), 1)
        self.assertEqual(TrainingRequest.objects.get().slug, "de-escalation-training")

    def test_duplicate_titles_get_counter_slugs(self):
        self.client.post(reverse("training:training_request"), self._valid_data())
        self.client.post(reverse("training:training_request"), self._valid_data())
        slugs = sorted(TrainingRequest.objects.values_list("slug", flat=True))
        self.assertEqual(slugs, ["de-escalation-training", "de-escalation-training-1"])

    def test_invalid_email_rejected(self):
        data = self._valid_data()
        data["email"] = "not-an-email"
        response = self.client.post(reverse("training:training_request"), data)
        self.assertEqual(response.status_code, 200)  # re-rendered with errors
        self.assertEqual(TrainingRequest.objects.count(), 0)
