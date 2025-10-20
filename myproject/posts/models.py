from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import User
from taggit.managers import TaggableManager

# Create your models here.

class Post(models.Model):
    title = models.CharField(max_length=75)
    body = models.TextField()
    slug = models.SlugField(unique=True, blank=False, null=False)
    date = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to='posts/', blank=True, null=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, default=None)
    tags = TaggableManager()

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    