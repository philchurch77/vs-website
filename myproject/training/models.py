from django.db import models

from myproject.core.slugs import generate_unique_slug


class TrainingRequest(models.Model):
    title = models.CharField(max_length=50)
    body = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    email = models.CharField()
    slug = models.SlugField(unique=True, blank=False, null=False)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(self, self.title)
        super().save(*args, **kwargs)
