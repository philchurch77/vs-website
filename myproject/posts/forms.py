from django import forms
from . import models
from taggit.forms import TagWidget

class CreatePost(forms.ModelForm):
    class Meta:
        model = models.Post
        fields = ['title', 'body', 'image', 'tags']
        widgets = {
            'tags': TagWidget(attrs={'placeholder': 'Enter comma-separated tags'}),
        }
