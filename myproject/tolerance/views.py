from datetime import date

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from .models import DailyCheckIn, Keyword
from .utils import compute_zone_summary


@login_required
def dashboard(request):
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


