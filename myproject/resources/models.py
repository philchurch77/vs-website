from django.core.validators import FileExtensionValidator
from django.db import models
from django.contrib.auth.models import User
from taggit.managers import TaggableManager

from myproject.core.slugs import generate_unique_slug
from myproject.core.validators import validate_upload_size


class Topic(models.Model):
    title = models.CharField(max_length=200)
    body = models.TextField(blank=True, null=True)
    slug = models.SlugField(max_length=200, unique=True, blank=False, null=False)
    date = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, default=None)
    link = models.URLField(max_length=200, blank=True, null=True)
    file = models.FileField(
        upload_to='documents/', blank=True, null=True,
        validators=[
            FileExtensionValidator(["pdf", "doc", "docx", "ppt", "pptx", "xls", "xlsx", "png", "jpg", "jpeg"]),
            validate_upload_size,
        ],
    )
    tags = TaggableManager()

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(self, self.title)
        super().save(*args, **kwargs)
