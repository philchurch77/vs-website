import json
from collections import Counter
from datetime import date, timedelta

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Observation, WeeklyMap

# ── Constants ─────────────────────────────────────────────────────────────────

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

WEEKLY_SUMMARY_SLOT = "Weekly summary"

TIME_SLOTS = [
    "Journey to school",
    "Registration/start of day",
    "Lesson 1",
    "Lesson 2",
    "Morning break",
    "Lesson 3",
    "Lesson 4",
    "Lunch",
    "Lesson 5",
    "Lesson 6",
    "End of day",
]

BEHAVIOURS = {
    "GREEN": ["Calm", "Engaged", "Playing", "Communicative", "Smiling", "Learning",
              "Connecting", "Participating", "Curious", "Working independently"],
    "RED":   ["Worried", "Hypervigilant", "Shouting", "Throwing", "Running",
              "Fighting", "High energy", "Screeching", "Looking alarmed",
              "Arguing", "Pushing", "Not-sharing", "Controlling"],
    "BLUE":  ["Disengaged", "Quiet", "Distant", "Flat", "Withdrawn", "Sad",
              "Tired", "Frozen", "Zoning out", "Glazed", "Collapse", "Curling up"],
}

TRIGGERS = [
    "Change in routine", "Transition", "Peer conflict", "Bullying / social difficulty",
    "Demand too high", "Written task", "Testing / assessment", "Sensory overload",
    "Noise", "Hunger", "Tiredness", "Unfamiliar adult", "Feeling unsafe",
    "Being asked to explain what happened", "Unstructured time",
    "Separation from trusted adult", "Learning issues", "Unknown", "Other",
]

RESPONSES = {
    "GREEN": ["Maintain routine", "Praise effort quietly", "Offer choice",
              "Support independence", "Use connection / check-in", "Continue learning task",
              "TA Support", "No adult available"],
    "RED":   ["Keep everyone safe", "Reduce language", "Use calm tone", "Create space",
              "Remove audience", "Offer trusted adult", "Reduce demand",
              "Offer movement break", "Offer quiet space", "Support breathing / grounding",
              "Follow safety plan", "TA Support", "No adult available"],
    "BLUE":  ["Quiet presence", "Gentle check-in", "Trusted adult nearby", "Offer water",
              "Offer tactile object", "Offer comfort item", "Reduce demand",
              "Use simple choices", "Sensory grounding", "Allow time", "TA Support",
              "No adult available"],
}

SUPPORT_PLAN_PROMPTS = [
    ("hardest_times",      "What times of day are hardest for the pupil?"),
    ("above_window",       "What situations seem to push them above their window?"),
    ("below_window",       "What situations seem to push them below their window?"),
    ("return_to_window",   "What helps them return to their window?"),
    ("do_more",            "What should adults do more of?"),
    ("avoid",              "What should adults avoid doing?"),
    ("adjustments",        "What reasonable adjustments are needed next week?"),
    ("when_we_notice",     "When we notice…"),
    ("may_mean",           "We think this may mean…"),
    ("adults_should",      "Adults should…"),
    ("adults_avoid",       "Adults should avoid…"),
    ("review_after",       "Review after…"),
]


# ── Weekly map list / create ───────────────────────────────────────────────────

@login_required
def dashboard(request):
    """Landing page: list all weekly maps; also handles create-new form."""
    if request.method == "POST":
        pupil_name = request.POST.get("pupil_name", "").strip()
        week_commencing_raw = request.POST.get("week_commencing", "")
        class_year = request.POST.get("class_or_year_group", "").strip()
        key_adults = request.POST.get("key_adults", "").strip()
        review_date_raw = request.POST.get("review_date", "") or None

        if pupil_name and week_commencing_raw:
            wmap = WeeklyMap.objects.create(
                pupil_name=pupil_name,
                week_commencing=week_commencing_raw,
                recorded_by=request.user,
                class_or_year_group=class_year,
                key_adults=key_adults,
                review_date=review_date_raw,
            )
            return redirect("tolerance:weekly_map_detail", pk=wmap.pk)

    maps = WeeklyMap.objects.filter(recorded_by=request.user).select_related("recorded_by")
    today = date.today()
    # Default week_commencing to the most recent Monday
    days_since_monday = today.weekday()
    default_wc = today - timedelta(days=days_since_monday)

    return render(request, "tolerance/weekly_map_list.html", {
        "maps": maps,
        "default_wc": default_wc.isoformat(),
    })


# ── Weekly map detail (the main grid) ─────────────────────────────────────────

@login_required
@require_POST
def delete_weekly_map(request, pk):
    wmap = get_object_or_404(WeeklyMap, pk=pk, recorded_by=request.user)
    wmap.delete()
    return redirect("tolerance:dashboard")


@login_required
def weekly_map_detail(request, pk):
    wmap = get_object_or_404(WeeklyMap, pk=pk, recorded_by=request.user)

    # Build a lookup: {(day, slot): observation}
    obs_qs = wmap.observations.all()
    obs_map = {(o.day_name, o.time_slot): o for o in obs_qs}

    # Build grid data structure
    grid = []
    for slot in TIME_SLOTS:
        row = {"slot": slot, "cells": []}
        for day in DAYS:
            obs = obs_map.get((day, slot))
            row["cells"].append({
                "day": day,
                "slot": slot,
                "obs": obs,
                "state": obs.state if obs else "GREY",
            })
        grid.append(row)

    # Summary
    all_obs = list(obs_qs)
    summary = _build_summary(all_obs)

    # Build obs data dict for JS hydration {"{day}:{slot}": {fields...}}
    obs_data = {}
    for o in obs_qs:
        key = f"{o.day_name}:{o.time_slot}"
        obs_data[key] = {
            "state": o.state,
            "observed_behaviours": o.observed_behaviours,
            "possible_triggers": o.possible_triggers,
            "adult_responses": o.adult_responses,
            "response_helpfulness": o.response_helpfulness,
            "notes": o.notes,
            "place": o.place,
            "people_present": o.people_present,
            "incident_time": o.incident_time,
            "abc_before": o.abc_before,
            "abc_during": o.abc_during,
            "abc_after": o.abc_after,
        }

    active_slots = wmap.visible_slots if wmap.visible_slots else TIME_SLOTS

    # Trend data — all weeks for this pupil (same user, same name), oldest first
    peer_weeks = (
        WeeklyMap.objects
        .filter(pupil_name=wmap.pupil_name, recorded_by=wmap.recorded_by)
        .order_by("week_commencing")
        .prefetch_related("observations")
    )
    trend_data = []
    for w in peer_weeks:
        obs_all = list(w.observations.all())
        for i, day in enumerate(DAYS):
            day_date = w.week_commencing + timedelta(days=i)
            obs = [o for o in obs_all if o.day_name == day and o.time_slot in TIME_SLOTS]
            green = sum(1 for o in obs if o.state == "GREEN")
            red   = sum(1 for o in obs if o.state == "RED")
            blue  = sum(1 for o in obs if o.state == "BLUE")
            total = green + red + blue
            if total > 0:
                trend_data.append({
                    "date": str(day_date),
                    "day": day[:3],
                    "week": str(w.week_commencing),
                    "pk": w.pk,
                    "is_current": w.pk == wmap.pk,
                    "green": green,
                    "red": red,
                    "blue": blue,
                    "total": total,
                })

    return render(request, "tolerance/weekly_map_detail.html", {
        "wmap": wmap,
        "grid": grid,
        "days": DAYS,
        "time_slots": TIME_SLOTS,
        "behaviours": BEHAVIOURS,
        "triggers": TRIGGERS,
        "responses": RESPONSES,
        "support_prompts": SUPPORT_PLAN_PROMPTS,
        "summary": summary,
        "support_plan": wmap.support_plan or {},
        "obs_data": obs_data,
        "active_slots": active_slots,
        "weekly_summary_slot": WEEKLY_SUMMARY_SLOT,
        "trend_data": trend_data,
    })


# ── API: save / update a single observation cell ──────────────────────────────

@login_required
@require_POST
def api_save_observation(request, pk):
    wmap = get_object_or_404(WeeklyMap, pk=pk, recorded_by=request.user)

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "invalid JSON"}, status=400)

    day_name = payload.get("day_name", "")
    time_slot = payload.get("time_slot", "")

    if day_name not in DAYS or (time_slot not in TIME_SLOTS and time_slot != WEEKLY_SUMMARY_SLOT):
        return JsonResponse({"ok": False, "error": "invalid day or time_slot"}, status=400)

    obs, _ = Observation.objects.get_or_create(
        weekly_map=wmap,
        day_name=day_name,
        time_slot=time_slot,
        defaults={"created_by": request.user},
    )

    obs.state = payload.get("state", "GREY")
    obs.observed_behaviours = payload.get("observed_behaviours", [])
    obs.possible_triggers = payload.get("possible_triggers", [])
    obs.adult_responses = payload.get("adult_responses", [])
    obs.response_helpfulness = payload.get("response_helpfulness", "")
    obs.notes = payload.get("notes", "")
    obs.place          = payload.get("place", "")
    obs.people_present = payload.get("people_present", "")
    obs.incident_time  = payload.get("incident_time", "")
    obs.abc_before     = payload.get("abc_before", "")
    obs.abc_during     = payload.get("abc_during", "")
    obs.abc_after      = payload.get("abc_after", "")
    obs.save()

    # Return updated summary
    all_obs = list(wmap.observations.all())
    summary = _build_summary(all_obs)

    return JsonResponse({"ok": True, "summary": summary})


# ── API: save support plan ────────────────────────────────────────────────────

@login_required
@require_POST
def api_save_support_plan(request, pk):
    wmap = get_object_or_404(WeeklyMap, pk=pk, recorded_by=request.user)

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "invalid JSON"}, status=400)

    wmap.support_plan = payload
    wmap.save(update_fields=["support_plan", "updated_at"])
    return JsonResponse({"ok": True})


# ── API: save visible slot selection ─────────────────────────────────────────

@login_required
@require_POST
def api_save_visible_slots(request, pk):
    wmap = get_object_or_404(WeeklyMap, pk=pk, recorded_by=request.user)

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "invalid JSON"}, status=400)

    slots = payload.get("visible_slots", [])
    if not isinstance(slots, list):
        return JsonResponse({"ok": False, "error": "visible_slots must be a list"}, status=400)

    # Store empty list to mean "all slots" — filter to known slots only
    wmap.visible_slots = [s for s in slots if s in TIME_SLOTS]
    wmap.save(update_fields=["visible_slots", "updated_at"])
    return JsonResponse({"ok": True})


# ── Helper: build summary from observations ───────────────────────────────────

def _build_summary(observations):
    # Exclude the weekly-overview placeholder — only real time-slot rows count
    obs = [o for o in observations if o.time_slot != WEEKLY_SUMMARY_SLOT]

    green = [o for o in obs if o.state == "GREEN"]
    red   = [o for o in obs if o.state == "RED"]
    blue  = [o for o in obs if o.state == "BLUE"]
    grey  = [o for o in obs if o.state == "GREY"]

    def top_slots(obs_list, n=3):
        counts = Counter(f"{o.day_name} {o.time_slot}" for o in obs_list)
        return [label for label, _ in counts.most_common(n)]

    all_triggers = []
    all_responses = []
    helpful_responses = []
    for o in obs:
        all_triggers.extend(o.possible_triggers)
        all_responses.extend(o.adult_responses)
        if o.response_helpfulness == "YES":
            helpful_responses.extend(o.adult_responses)

    top_triggers = [t for t, _ in Counter(all_triggers).most_common(5)]
    top_helpful  = [r for r, _ in Counter(helpful_responses).most_common(5)]
    if not top_helpful:
        top_helpful = [r for r, _ in Counter(all_responses).most_common(3)]

    missing_slots = []
    for o in grey:
        missing_slots.append(f"{o.day_name} {o.time_slot}")

    return {
        "regulated_times":   top_slots(green),
        "red_times":         top_slots(red),
        "blue_times":        top_slots(blue),
        "top_triggers":      top_triggers,
        "helpful_responses": top_helpful,
        "missing_count":     len(grey),
        "counts": {
            "green": len(green),
            "red": len(red),
            "blue": len(blue),
            "grey": len(grey),
        },
    }




