from django.contrib.auth.models import User
from django.db import models


class ChatTurn(models.Model):
    """A single message in an AI chat session.

    ``tool`` keeps each tool's sessions separate even though they share
    users. ``role`` is usually "user" or "assistant"; the flashcards tool
    also stores one "title" row per renamed session. The evaluation app
    was removed, but its choice stays so historic rows remain valid.
    """

    TOOL_FLASHCARDS = "flashcards"
    TOOL_EVALUATION = "evaluation"
    TOOL_CHOICES = [
        (TOOL_FLASHCARDS, "Flashcards"),
        (TOOL_EVALUATION, "Evaluation"),
    ]

    tool = models.CharField(max_length=20, choices=TOOL_CHOICES)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="chat_turns", null=True
    )
    session_id = models.CharField(max_length=100)
    role = models.CharField(
        max_length=10,
        choices=[("user", "User"), ("assistant", "Assistant"), ("title", "Title")],
    )
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["tool", "user", "session_id"])]

    def __str__(self):
        return f"{self.timestamp} | {self.role}: {self.content[:50]}"
