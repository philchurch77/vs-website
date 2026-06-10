from django.contrib import admin
from .models import WeeklyMap, Observation


@admin.register(WeeklyMap)
class WeeklyMapAdmin(admin.ModelAdmin):
    list_display = ("pupil_name", "week_commencing", "class_or_year_group", "recorded_by", "review_date")
    list_filter = ("week_commencing",)
    search_fields = ("pupil_name", "recorded_by__username")
    date_hierarchy = "week_commencing"


@admin.register(Observation)
class ObservationAdmin(admin.ModelAdmin):
    list_display = ("weekly_map", "day_name", "time_slot", "state", "created_by")
    list_filter = ("state", "day_name")
    search_fields = ("weekly_map__pupil_name",)
