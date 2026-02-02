from django.db import models
from django.contrib.auth.models import User

class ChatTurn(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="chat_turns", null=True)
    session_id = models.CharField(max_length=100)
    role = models.CharField(max_length=10, choices=[("user", "User"), ("assistant", "Assistant")])
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.timestamp} | {self.role}: {self.content[:50]}"

class Flashcard(models.Model):
    flashcard_id = models.IntegerField(unique=True)
    title = models.CharField(max_length=255)
    how_to_do_it = models.TextField()
    what_you_need = models.TextField()
    who_where_when_why = models.TextField()
    sort_order = models.IntegerField()
    image = models.ImageField(upload_to='flashcard_images/', blank=True, null=True)


    class Meta:
        ordering = ["sort_order"]


    def __str__(self):
        return f"{self.sort_order}. {self.title}"
    
class Scenario(models.Model):
    scenario_id = models.IntegerField(unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    sort_order = models.IntegerField()

    class Meta:
        ordering = ["sort_order"]
        verbose_name = "Scenario"
        verbose_name_plural = "Scenarios"

    def __str__(self):
        return f"{self.sort_order}. {self.title}"
