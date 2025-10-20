from django.db import models
from django.utils.text import slugify
from django.utils.crypto import get_random_string

class TrainingRequest(models.Model):
    title = models.CharField(max_length=50)
    body = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    email = models.CharField()
    slug = models.SlugField(unique=True, blank=False, null=False)

    def __str__ (self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while TrainingRequest.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)
