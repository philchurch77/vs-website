from django import forms
from . import models

class RequestTraining(forms.ModelForm):
    class Meta:
        model = models.TrainingRequest
        fields = ['title', 'body', 'email']