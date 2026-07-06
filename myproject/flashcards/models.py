from django.db import models

from myproject.core.validators import validate_upload_size


class Flashcard(models.Model):
    flashcard_id = models.IntegerField(unique=True)
    title = models.CharField(max_length=255)
    how_to_do_it = models.TextField()
    what_you_need = models.TextField()
    who_where_when_why = models.TextField()
    sort_order = models.IntegerField()
    image = models.ImageField(
        upload_to='flashcard_images/', blank=True, null=True,
        validators=[validate_upload_size],
    )


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
