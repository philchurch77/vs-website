from django import forms
from . import models


class RequestTraining(forms.ModelForm):
    # Use an EmailField for better validation and HTML5 email input
    email = forms.EmailField(label="Contact email")

    class Meta:
        model = models.TrainingRequest
        fields = ["title", "body", "email"]
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "placeholder": "Short title for your training request",
                    "autofocus": "autofocus",
                }
            ),
            "body": forms.Textarea(
                attrs={
                    "rows": 6,
                    "placeholder": "Briefly describe the pupil(s), context, and what you would like support with",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "placeholder": "your.name@example.com",
                }
            ),
        }