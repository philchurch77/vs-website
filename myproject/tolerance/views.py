import json
from collections import Counter
from datetime import date, timedelta

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import DailyCheckIn, Keyword, Observation, WeeklyMap
from .utils import compute_zone_summary

# ── Constants ─────────────────────────────────────────────────────────────────

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

TIME_SLOTS = [
    "Arrival",
    "Registration",
    "Morning lesson 1",
    "Morning lesson 2",
    "Break",
    "Morning lesson 3",
    "Lunch",
    "Afternoon lesson 1",
    "Afternoon lesson 2",
    "Afternoon break / transition",
    "Hometime",
]

BEHAVIOURS = {
    "GREEN": ["Calm", "Engaged", "Playing", "Expressing", "Smiling", "Learning",
              "Connecting", "Participating", "Curious"],
    "RED":   ["Worried", "Hypervigilant", "Shouting", "Throwing", "Running",
              "Fighting", "High energy", "Screeching", "Looking alarmed"],
    "BLUE":  ["Disengaged", "Quiet", "Distant", "Flat", "Withdrawn", "Sad",
              "Tired", "Frozen", "Zoning out", "Glazed", "Collapse", "Curling up"],
}

TRIGGERS = [
    "Change in routine", "Transition", "Peer conflict", "Bullying / social difficulty",
    "Demand too high", "Written task", "Testing / assessment", "Sensory overload",
    "Noise", "Hunger", "Tiredness", "Unfamiliar adult", "Feeling unsafe",
    "Being asked to explain what happened", "Unstructured time",
    "Separation from trusted adult", "Unknown", "Other",
]

RESPONSES = {
    "GREEN": ["Maintain routine", "Praise effort quietly", "Offer choice",
              "Support independence", "Use connection / check-in", "Continue learning task"],
    "RED":   ["Keep everyone safe", "Reduce language", "Use calm tone", "Create space",
              "Remove audience", "Offer trusted adult", "Reduce demand",
              "Offer movement break", "Offer quiet space", "Support breathing / grounding",
              "Follow safety plan"],
    "BLUE":  ["Quiet presence", "Gentle check-in", "Trusted adult nearby", "Offer water",
              "Offer tactile object", "Offer comfort item", "Reduce demand",
              "Use simple choices", "Sensory grounding", "Allow time"],
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

    maps = WeeklyMap.objects.select_related("recorded_by").all()
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
def weekly_map_detail(request, pk):
    wmap = get_object_or_404(WeeklyMap, pk=pk)

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
            "intensity": o.intensity,
            "observed_behaviours": o.observed_behaviours,
            "possible_triggers": o.possible_triggers,
            "adult_responses": o.adult_responses,
            "response_helpfulness": o.response_helpfulness,
            "notes": o.notes,
        }

    return render(request, "tolerance/weekly_map_detail.html", {
        "wmap": wmap,
        "grid": grid,
        "days": DAYS,
        "time_slots": TIME_SLOTS,
        "behaviours_json": json.dumps(BEHAVIOURS),
        "triggers_json": json.dumps(TRIGGERS),
        "responses_json": json.dumps(RESPONSES),
        "support_prompts": SUPPORT_PLAN_PROMPTS,
        "summary": summary,
        "summary_json": json.dumps(summary),
        "support_plan_json": json.dumps(wmap.support_plan or {}),
        "obs_data_json": json.dumps(obs_data),
    })


# ── API: save / update a single observation cell ──────────────────────────────

@login_required
@require_POST
def api_save_observation(request, pk):
    wmap = get_object_or_404(WeeklyMap, pk=pk)

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "invalid JSON"}, status=400)

    day_name = payload.get("day_name", "")
    time_slot = payload.get("time_slot", "")

    if day_name not in DAYS or time_slot not in TIME_SLOTS:
        return JsonResponse({"ok": False, "error": "invalid day or time_slot"}, status=400)

    obs, _ = Observation.objects.get_or_create(
        weekly_map=wmap,
        day_name=day_name,
        time_slot=time_slot,
        defaults={"created_by": request.user},
    )

    obs.state = payload.get("state", "GREY")
    intensity = payload.get("intensity")
    obs.intensity = int(intensity) if intensity in (1, 2, 3, "1", "2", "3") else None
    obs.observed_behaviours = payload.get("observed_behaviours", [])
    obs.possible_triggers = payload.get("possible_triggers", [])
    obs.adult_responses = payload.get("adult_responses", [])
    obs.response_helpfulness = payload.get("response_helpfulness", "")
    obs.notes = payload.get("notes", "")
    obs.save()

    # Return updated summary
    all_obs = list(wmap.observations.all())
    summary = _build_summary(all_obs)

    return JsonResponse({"ok": True, "summary": summary})


# ── API: save support plan ────────────────────────────────────────────────────

@login_required
@require_POST
def api_save_support_plan(request, pk):
    wmap = get_object_or_404(WeeklyMap, pk=pk)

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "invalid JSON"}, status=400)

    wmap.support_plan = payload
    wmap.save(update_fields=["support_plan", "updated_at"])
    return JsonResponse({"ok": True})


# ── Helper: build summary from observations ───────────────────────────────────

def _build_summary(observations):
    green = [o for o in observations if o.state == "GREEN"]
    red   = [o for o in observations if o.state == "RED"]
    blue  = [o for o in observations if o.state == "BLUE"]
    grey  = [o for o in observations if o.state == "GREY"]

    def top_slots(obs_list, n=3):
        counts = Counter((o.day_name + " " + o.time_slot) for o in obs_list)
        return [label for label, _ in counts.most_common(n)]

    all_triggers = []
    all_responses = []
    helpful_responses = []
    for o in observations:
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


# ── Legacy check-in (preserved) ───────────────────────────────────────────────

@login_required
def checkin_dashboard(request):
    checkin, _ = DailyCheckIn.objects.get_or_create(
        user=request.user,
        date=date.today(),
    )

    keywords = Keyword.objects.all().order_by("label")
    selected = set(checkin.keywords.values_list("id", flat=True))
    selected_keywords = list(checkin.keywords.all())
    summary = compute_zone_summary(selected_keywords)

    return render(request, "tolerance/dashboard.html", {
        "checkin": checkin,
        "keywords": keywords,
        "selected": selected,
        "selected_keywords": selected_keywords,
        "summary": summary,
    })


@login_required
@require_POST
def toggle_keyword(request):
    checkin, _ = DailyCheckIn.objects.get_or_create(
        user=request.user,
        date=date.today(),
    )

    kid = request.POST.get("keyword_id")
    if not kid:
        return JsonResponse({"ok": False, "error": "keyword_id missing"}, status=400)

    try:
        kw = Keyword.objects.get(id=kid)
    except Keyword.DoesNotExist:
        return JsonResponse({"ok": False, "error": "keyword not found"}, status=404)

    if checkin.keywords.filter(id=kw.id).exists():
        checkin.keywords.remove(kw)
    else:
        checkin.keywords.add(kw)

    selected_qs = checkin.keywords.all()

    grouped = {"HYPER": [], "WINDOW": [], "HYPO": []}
    for k in selected_qs:
        grouped.setdefault(k.default_zone, []).append(k.label)

    summary = compute_zone_summary(list(selected_qs))

    return JsonResponse({
        "ok": True,
        "selected_ids": list(selected_qs.values_list("id", flat=True)),
        "grouped": grouped,
        "summary": summary,
    })


@login_required
@require_POST
def save_notes(request):
    checkin, _ = DailyCheckIn.objects.get_or_create(
        user=request.user,
        date=date.today(),
    )

    checkin.notes = request.POST.get("notes", "")
    checkin.save(update_fields=["notes"])

    return JsonResponse({"ok": True})


