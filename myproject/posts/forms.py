from django import forms
from . import models
from taggit.forms import TagWidget


class CreatePost(forms.ModelForm):
    class Meta:
        model = models.Post
        fields = ["title", "body", "image", "tags"]
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "placeholder": "Give your post a clear, short title",
                    "autofocus": "autofocus",
                }
            ),
            "body": forms.Textarea(
                attrs={
                    "rows": 8,
                    "placeholder": "Write your update, news, or success story here",
                }
            ),
            "image": forms.ClearableFileInput(
                attrs={
                    "accept": "image/*",
                }
            ),
            "tags": TagWidget(
                attrs={
                    "placeholder": "Enter comma-separated tags, e.g. attendance, SEMH, KS2",
                }
            ),
        }
