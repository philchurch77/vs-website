from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import User
from taggit.managers import TaggableManager

class Topic(models.Model):
    title = models.CharField(max_length=200)
    text = models.TextField(blank=True, null=True)
    slug = models.SlugField(max_length=200, unique=True, blank=False, null=False)
    date = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, default=None)
    link = models.URLField(max_length=200, blank=True, null=True)
    file = models.FileField(upload_to='documents/', blank=True, null=True)
    tags = TaggableManager()

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)