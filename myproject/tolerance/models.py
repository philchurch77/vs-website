from django.conf import settings
from django.db import models


class Keyword(models.Model):
    class Zone(models.TextChoices):
        HYPER = "HYPER", "Hyper-arousal"
        WINDOW = "WINDOW", "Window of tolerance"
        HYPO = "HYPO", "Hypo-arousal"

    label = models.CharField(max_length=100, unique=True)
    default_zone = models.CharField(max_length=10, choices=Zone.choices)
    kind = models.CharField(max_length=50, blank=True)

    def __str__(self) -> str:
        return self.label


class DailyCheckIn(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateField()
    keywords = models.ManyToManyField(Keyword, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "date"], name="uniq_checkin_per_user_per_day")
        ]
        ordering = ["-date", "-created_at"]

    def __str__(self) -> str:
        return f"{self.user} - {self.date}"


# ── Weekly Mapping Tool ───────────────────────────────────────────────────────

class WeeklyMap(models.Model):
    pupil_name = models.CharField(max_length=200)
    week_commencing = models.DateField()
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="weekly_maps",
    )
    class_or_year_group = models.CharField(max_length=100, blank=True)
    key_adults = models.TextField(blank=True)
    review_date = models.DateField(null=True, blank=True)
    support_plan = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-week_commencing", "pupil_name"]

    def __str__(self) -> str:
        return f"{self.pupil_name} – w/c {self.week_commencing}"


class Observation(models.Model):
    class State(models.TextChoices):
        GREEN = "GREEN", "Within Window (Green)"
        RED = "RED", "Hyper-arousal (Red)"
        BLUE = "BLUE", "Hypo-arousal (Blue)"
        GREY = "GREY", "Not observed (Grey)"

    class Helpfulness(models.TextChoices):
        YES = "YES", "Yes"
        PARTLY = "PARTLY", "Partly"
        NO = "NO", "No"
        UNKNOWN = "UNKNOWN", "Unknown"

    weekly_map = models.ForeignKey(
        WeeklyMap, on_delete=models.CASCADE, related_name="observations"
    )
    day_name = models.CharField(max_length=20)   # Monday … Friday
    time_slot = models.CharField(max_length=60)  # Arrival, Registration, …
    state = models.CharField(max_length=10, choices=State.choices, default=State.GREY)
    intensity = models.PositiveSmallIntegerField(null=True, blank=True)  # 1–3
    observed_behaviours = models.JSONField(default=list, blank=True)
    possible_triggers = models.JSONField(default=list, blank=True)
    adult_responses = models.JSONField(default=list, blank=True)
    response_helpfulness = models.CharField(
        max_length=10, choices=Helpfulness.choices, blank=True
    )
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="observations",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("weekly_map", "day_name", "time_slot")]
        ordering = ["day_name", "time_slot"]

    def __str__(self) -> str:
        return f"{self.weekly_map} | {self.day_name} {self.time_slot}"
