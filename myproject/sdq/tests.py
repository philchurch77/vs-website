from django.test import TestCase
from django.urls import reverse

from .models import SDQResponse


class SDQTests(TestCase):
    def _valid_data(self):
        # 1 ("Somewhat True") is a valid value for every question
        return {f"q{i}": 1 for i in range(1, 26)}

    def test_form_renders(self):
        response = self.client.get(reverse("sdq:sdq_form_view"))
        self.assertEqual(response.status_code, 200)

    def test_scoring_renders_without_persisting(self):
        response = self.client.post(reverse("sdq:sdq_form_view"), self._valid_data())
        self.assertEqual(response.status_code, 200)
        result = response.context["response"]
        self.assertIsNotNone(result)
        # 20 scored questions (25 minus the 5 prosocial items), all answered 1
        self.assertEqual(result.total_score(), 20)
        self.assertEqual(result.prosocial_scale(), 5)
        # CLAUDE.md: SDQ responses are deliberately NOT persisted to the DB
        self.assertEqual(SDQResponse.objects.count(), 0)

    def test_incomplete_submission_shows_no_score(self):
        data = self._valid_data()
        del data["q25"]
        response = self.client.post(reverse("sdq:sdq_form_view"), data)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context["response"])
        self.assertEqual(SDQResponse.objects.count(), 0)
