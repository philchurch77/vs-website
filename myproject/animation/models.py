from django.db import models
from django.contrib.auth.models import User


class ChatTurn(models.Model):
    session_id = models.CharField(max_length=100)
    role = models.CharField(max_length=10, choices=[("user", "User"), ("assistant", "Assistant")])
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name="animation_chatturns")

    def __str__(self):
        return f"{self.timestamp} | {self.role}: {self.content[:50]}"