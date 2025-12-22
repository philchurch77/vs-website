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
