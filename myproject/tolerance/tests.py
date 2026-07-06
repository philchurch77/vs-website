import json
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Observation, WeeklyMap
from .views import _build_trend_data

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
        payload = {"day_name": "Monday", "time_slot": "Lesson 1", "state": "GREEN"}
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
        payload = {"day_name": "Monday", "time_slot": "Lesson 1", "state": "GREEN"}
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

    def test_api_endpoints_reject_get(self):
        for name in ("api_save_observation", "api_save_support_plan", "api_save_visible_slots"):
            response = self.client.get(reverse(f"tolerance:{name}", args=[self.wmap.pk]))
            self.assertEqual(response.status_code, 405, name)

    def test_observation_round_trip_persists_fields(self):
        payload = {
            "day_name": "Tuesday",
            "time_slot": "Lesson 1",
            "state": "RED",
            "observed_behaviours": ["Shouting"],
            "possible_triggers": ["Transition"],
            "adult_responses": ["Use calm tone"],
            "response_helpfulness": "YES",
            "notes": "Settled after five minutes",
        }
        response = self.client.post(
            reverse("tolerance:api_save_observation", args=[self.wmap.pk]),
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        obs = Observation.objects.get(weekly_map=self.wmap, day_name="Tuesday", time_slot="Lesson 1")
        self.assertEqual(obs.state, "RED")
        self.assertEqual(obs.observed_behaviours, ["Shouting"])
        self.assertEqual(obs.adult_responses, ["Use calm tone"])
        # Saved observation feeds the returned summary
        self.assertEqual(response.json()["summary"]["counts"]["red"], 1)

    def test_invalid_slot_rejected(self):
        payload = {"day_name": "Tuesday", "time_slot": "Not a real slot", "state": "RED"}
        response = self.client.post(
            reverse("tolerance:api_save_observation", args=[self.wmap.pk]),
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_invalid_state_rejected(self):
        payload = {"day_name": "Tuesday", "time_slot": "Lesson 1", "state": "PURPLE"}
        response = self.client.post(
            reverse("tolerance:api_save_observation", args=[self.wmap.pk]),
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_out_of_vocab_values_rejected(self):
        for field in ("observed_behaviours", "possible_triggers", "adult_responses"):
            payload = {
                "day_name": "Tuesday", "time_slot": "Lesson 1", "state": "RED",
                field: ["Not a real option"],
            }
            response = self.client.post(
                reverse("tolerance:api_save_observation", args=[self.wmap.pk]),
                data=json.dumps(payload),
                content_type="application/json",
            )
            self.assertEqual(response.status_code, 400, field)
        self.assertFalse(Observation.objects.filter(weekly_map=self.wmap).exists())

    def test_create_map_redirects_to_detail(self):
        response = self.client.post(reverse("tolerance:dashboard"), {
            "pupil_name": "New Pupil",
            "week_commencing": "2026-06-08",
        })
        wmap = WeeklyMap.objects.get(pupil_name="New Pupil")
        self.assertRedirects(response, reverse("tolerance:weekly_map_detail", args=[wmap.pk]))

    def test_create_map_with_bad_date_shows_error(self):
        response = self.client.post(reverse("tolerance:dashboard"), {
            "pupil_name": "New Pupil",
            "week_commencing": "not-a-date",
        })
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context["create_error"])
        self.assertFalse(WeeklyMap.objects.filter(pupil_name="New Pupil").exists())

    def test_owner_can_delete_own_map(self):
        response = self.client.post(reverse("tolerance:delete_weekly_map", args=[self.wmap.pk]))
        self.assertRedirects(response, reverse("tolerance:dashboard"))
        self.assertFalse(WeeklyMap.objects.filter(pk=self.wmap.pk).exists())


# ── Trend view tests ──────────────────────────────────────────────────────────

def _add_obs(wmap, user, day, slot, state):
    return Observation.objects.create(
        weekly_map=wmap, day_name=day, time_slot=slot, state=state, created_by=user,
    )


class TrendDataShapeTests(TestCase):
    """The trend payload must carry exactly the fields the SVG renderer reads."""

    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="pass")
        self.wmap = WeeklyMap.objects.create(
            pupil_name="Trend Pupil",
            week_commencing=date(2026, 6, 8),  # a Monday
            recorded_by=self.owner,
        )

    def test_empty_when_no_observations(self):
        self.assertEqual(_build_trend_data(self.wmap), [])

    def test_grey_and_weekly_summary_excluded(self):
        # GREY (not observed) and the weekly-summary placeholder must not appear
        _add_obs(self.wmap, self.owner, "Monday", "Lesson 1", "GREY")
        _add_obs(self.wmap, self.owner, "Monday", "Weekly summary", "GREEN")
        self.assertEqual(_build_trend_data(self.wmap), [])

    def test_single_session_day_builds_one_record(self):
        _add_obs(self.wmap, self.owner, "Monday", "Lesson 1", "GREEN")
        data = _build_trend_data(self.wmap)
        self.assertEqual(len(data), 1)
        rec = data[0]
        # Every key the template JS reads must be present
        for key in ("date", "day", "week", "pk", "is_current", "entries"):
            self.assertIn(key, rec, f"missing key {key}")
        self.assertEqual(rec["day"], "Mon")
        self.assertEqual(rec["date"], "2026-06-08")
        self.assertEqual(rec["week"], "2026-06-08")
        self.assertEqual(rec["pk"], self.wmap.pk)
        self.assertTrue(rec["is_current"])
        self.assertEqual(rec["entries"], [{"slot": "Lesson 1", "state": "GREEN"}])

    def test_entries_sorted_by_slot_order(self):
        # Saved out of order, but entries should follow the school-day slot order
        _add_obs(self.wmap, self.owner, "Monday", "Lunch", "BLUE")
        _add_obs(self.wmap, self.owner, "Monday", "Lesson 1", "GREEN")
        _add_obs(self.wmap, self.owner, "Monday", "Registration/start of day", "RED")
        data = _build_trend_data(self.wmap)
        slots = [e["slot"] for e in data[0]["entries"]]
        self.assertEqual(slots, ["Registration/start of day", "Lesson 1", "Lunch"])

    def test_one_record_per_recorded_day_ordered(self):
        _add_obs(self.wmap, self.owner, "Wednesday", "Lesson 1", "GREEN")
        _add_obs(self.wmap, self.owner, "Monday", "Lesson 1", "RED")
        data = _build_trend_data(self.wmap)
        self.assertEqual([r["day"] for r in data], ["Mon", "Wed"])
        self.assertEqual(data[0]["date"], "2026-06-08")
        self.assertEqual(data[1]["date"], "2026-06-10")

    def test_multiple_weeks_same_pupil_combine_oldest_first(self):
        older = WeeklyMap.objects.create(
            pupil_name="Trend Pupil",
            week_commencing=date(2026, 6, 1),
            recorded_by=self.owner,
        )
        _add_obs(older, self.owner, "Monday", "Lesson 1", "GREEN")
        _add_obs(self.wmap, self.owner, "Monday", "Lesson 1", "RED")
        data = _build_trend_data(self.wmap)
        self.assertEqual(len(data), 2)
        # oldest week first
        self.assertEqual(data[0]["week"], "2026-06-01")
        self.assertEqual(data[1]["week"], "2026-06-08")
        # is_current flags the week the user is viewing, not the older one
        self.assertFalse(data[0]["is_current"])
        self.assertTrue(data[1]["is_current"])


class TrendIsolationTests(TestCase):
    """Trend data must never blend across users, even with the same pupil name."""

    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="pass")
        self.other = User.objects.create_user(username="other", password="pass")
        self.owner_map = WeeklyMap.objects.create(
            pupil_name="Jamie",
            week_commencing=date(2026, 6, 8),
            recorded_by=self.owner,
        )
        # A different user happens to record a pupil with the SAME name
        self.other_map = WeeklyMap.objects.create(
            pupil_name="Jamie",
            week_commencing=date(2026, 6, 8),
            recorded_by=self.other,
        )
        _add_obs(self.owner_map, self.owner, "Monday", "Lesson 1", "GREEN")
        _add_obs(self.other_map, self.other, "Tuesday", "Lesson 2", "RED")

    def test_trend_does_not_leak_other_users_same_named_pupil(self):
        data = _build_trend_data(self.owner_map)
        # Only the owner's single Monday record — never the other user's Tuesday
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["day"], "Mon")
        self.assertEqual(data[0]["pk"], self.owner_map.pk)
        all_pks = {r["pk"] for r in data}
        self.assertNotIn(self.other_map.pk, all_pks)

    def test_save_endpoint_returns_owner_scoped_trend(self):
        # Saving via the API returns a trend that reflects only the owner's data
        self.client.login(username="owner", password="pass")
        payload = {"day_name": "Wednesday", "time_slot": "Lesson 3", "state": "BLUE"}
        response = self.client.post(
            reverse("tolerance:api_save_observation", args=[self.owner_map.pk]),
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        trend = response.json()["trend"]
        days = sorted(r["day"] for r in trend)
        self.assertEqual(days, ["Mon", "Wed"])  # never "Tue" from the other user
        for r in trend:
            self.assertIn(r["pk"], {self.owner_map.pk})

    def test_intruder_save_does_not_return_trend(self):
        self.client.login(username="other", password="pass")
        payload = {"day_name": "Monday", "time_slot": "Lesson 1", "state": "GREEN"}
        response = self.client.post(
            reverse("tolerance:api_save_observation", args=[self.owner_map.pk]),
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)

    def test_detail_context_trend_is_owner_scoped(self):
        self.client.login(username="owner", password="pass")
        response = self.client.get(
            reverse("tolerance:weekly_map_detail", args=[self.owner_map.pk])
        )
        self.assertEqual(response.status_code, 200)
        trend = response.context["trend_data"]
        self.assertEqual(len(trend), 1)
        self.assertEqual(trend[0]["pk"], self.owner_map.pk)


class TrendDetailRenderTests(TestCase):
    """The detail page must render with the trend payload embedded, empty or not."""

    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="pass")
        self.client.login(username="owner", password="pass")

    def test_empty_pupil_page_renders_without_crash(self):
        wmap = WeeklyMap.objects.create(
            pupil_name="No Data Pupil",
            week_commencing=date(2026, 6, 8),
            recorded_by=self.owner,
        )
        response = self.client.get(reverse("tolerance:weekly_map_detail", args=[wmap.pk]))
        self.assertEqual(response.status_code, 200)
        # Empty trend should be embedded as an empty JSON array for the JS to read
        self.assertContains(response, 'id="wot-trend-data"')
        self.assertEqual(response.context["trend_data"], [])

    def test_populated_pupil_page_embeds_trend(self):
        wmap = WeeklyMap.objects.create(
            pupil_name="Has Data Pupil",
            week_commencing=date(2026, 6, 8),
            recorded_by=self.owner,
        )
        _add_obs(wmap, self.owner, "Monday", "Lesson 1", "GREEN")
        response = self.client.get(reverse("tolerance:weekly_map_detail", args=[wmap.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["trend_data"]), 1)
