from django.contrib import admin
from . models import TrainingRequest

@admin.register(TrainingRequest)
class TrainingAdmin(admin.ModelAdmin):
    list_display = ['title', 'body', 'email', 'date', 'slug']
