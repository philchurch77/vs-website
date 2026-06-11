from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class TrainingSummary(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    title = models.CharField(max_length=255)
    school_or_trust = models.CharField(max_length=255)
    summary_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    session_id = models.CharField(max_length=64, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.title:
            current_date = timezone.now().strftime("%Y-%m-%d")
            self.title = f"{current_date - self.school_or_trust}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.created_at.strftime('%Y-%m-%d')})"
