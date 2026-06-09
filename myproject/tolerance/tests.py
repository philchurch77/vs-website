import json
from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Observation, WeeklyMap

User = get_user_model()


class ToleranceAuthTests(TestCase):
    """Unauthenticated users must be redirected from all tolerance views."""

    def setUp(self):
        self.user = User.objects.create_user(username="alice", password="pass")
        self.wmap = WeeklyMap.objects.create(
            pupil_name="Test Pupil",
            week_commencing=date.today(),
            recorded_by=self.user,
        )

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("tolerance:dashboard"))
        self.assertEqual(response.status_code, 302)

    def test_weekly_map_detail_requires_login(self):
        response = self.client.get(reverse("tolerance:weekly_map_detail", args=[self.wmap.pk]))
        self.assertEqual(response.status_code, 302)

    def test_delete_requires_login(self):
        response = self.client.post(reverse("tolerance:delete_weekly_map", args=[self.wmap.pk]))
        self.assertEqual(response.status_code, 302)

    def test_api_observation_requires_login(self):
        # unauthenticated POST to the observation API must be rejected
        response = self.client.post(
            reverse("tolerance:api_save_observation", args=[self.wmap.pk]),
            data=json.dumps({}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 302)

    def test_api_support_plan_requires_login(self):
        # unauthenticated POST to the support plan API must be rejected
        response = self.client.post(
            reverse("tolerance:api_save_support_plan", args=[self.wmap.pk]),
            data=json.dumps({}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 302)


class ToleranceOwnershipTests(TestCase):
    """A logged-in user must not be able to reach another user's WeeklyMap data."""

    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="pass")
        self.intruder = User.objects.create_user(username="intruder", password="pass")
        self.wmap = WeeklyMap.objects.create(
            pupil_name="Sensitive Pupil",
            week_commencing=date.today(),
            recorded_by=self.owner,
        )

    def test_intruder_cannot_view_weekly_map_detail(self):
        # another user must not be able to read a WeeklyMap they don't own
        self.client.login(username="intruder", password="pass")
        response = self.client.get(reverse("tolerance:weekly_map_detail", args=[self.wmap.pk]))
        self.assertIn(response.status_code, [403, 404])

    def test_intruder_cannot_write_observation(self):
        # another user must not be able to save observations into a WeeklyMap they don't own
        self.client.login(username="intruder", password="pass")
        payload = {"day_name": "Monday", "time_slot": "Arrival", "state": "GREEN"}
        response = self.client.post(
            reverse("tolerance:api_save_observation", args=[self.wmap.pk]),
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertNotEqual(response.status_code, 200)

    def test_intruder_cannot_overwrite_support_plan(self):
        # another user must not be able to overwrite a support plan they don't own
        self.client.login(username="intruder", password="pass")
        response = self.client.post(
            reverse("tolerance:api_save_support_plan", args=[self.wmap.pk]),
            data=json.dumps({"hardest_times": "injected content"}),
            content_type="application/json",
        )
        self.assertNotEqual(response.status_code, 200)

    def test_intruder_cannot_delete_weekly_map(self):
        # delete is already guarded by recorded_by filter — confirm it returns 404
        self.client.login(username="intruder", password="pass")
        response = self.client.post(reverse("tolerance:delete_weekly_map", args=[self.wmap.pk]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(WeeklyMap.objects.filter(pk=self.wmap.pk).exists())

    def test_dashboard_only_shows_own_maps(self):
        # the dashboard must not expose another user's pupil records in the listing
        self.client.login(username="intruder", password="pass")
        response = self.client.get(reverse("tolerance:dashboard"))
        self.assertEqual(response.status_code, 200)
        for wmap in response.context["maps"]:
            self.assertEqual(wmap.recorded_by, self.intruder)


class ToleranceOwnerCanAccessOwnData(TestCase):
    """Sanity checks — the owner can still reach their own data."""

    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="pass")
        self.wmap = WeeklyMap.objects.create(
            pupil_name="Own Pupil",
            week_commencing=date.today(),
            recorded_by=self.owner,
        )
        self.client.login(username="owner", password="pass")

    def test_owner_can_view_own_weekly_map(self):
        response = self.client.get(reverse("tolerance:weekly_map_detail", args=[self.wmap.pk]))
        self.assertEqual(response.status_code, 200)

    def test_owner_can_save_observation(self):
        payload = {"day_name": "Monday", "time_slot": "Arrival", "state": "GREEN"}
        response = self.client.post(
            reverse("tolerance:api_save_observation", args=[self.wmap.pk]),
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["ok"])

    def test_owner_can_save_support_plan(self):
        payload = {"hardest_times": "Mornings"}
        response = self.client.post(
            reverse("tolerance:api_save_support_plan", args=[self.wmap.pk]),
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.wmap.refresh_from_db()
        self.assertEqual(self.wmap.support_plan["hardest_times"], "Mornings")

    def test_owner_map_appears_in_dashboard(self):
        response = self.client.get(reverse("tolerance:dashboard"))
        self.assertEqual(response.status_code, 200)
        pks = [m.pk for m in response.context["maps"]]
        self.assertIn(self.wmap.pk, pks)
