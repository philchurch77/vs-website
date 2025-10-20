from django.contrib import admin
from .models import TrainingSummary

@admin.register(TrainingSummary)
class TrainingSummaryAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at')
    readonly_fields = ('summary_text',)
