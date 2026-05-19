from django.contrib import admin
from .models import Keyword, DailyCheckIn, WeeklyMap, Observation


@admin.register(Keyword)
class KeywordAdmin(admin.ModelAdmin):
    list_display = ("label", "default_zone", "kind")
    list_filter = ("default_zone", "kind")
    search_fields = ("label",)


@admin.register(DailyCheckIn)
class DailyCheckInAdmin(admin.ModelAdmin):
    list_display = ("user", "date", "created_at")
    list_filter = ("date",)
    search_fields = ("user__username", "user__email", "user__first_name", "user__last_name")
    filter_horizontal = ("keywords",)


@admin.register(WeeklyMap)
class WeeklyMapAdmin(admin.ModelAdmin):
    list_display = ("pupil_name", "week_commencing", "class_or_year_group", "recorded_by", "review_date")
    list_filter = ("week_commencing",)
    search_fields = ("pupil_name", "recorded_by__username")
    date_hierarchy = "week_commencing"


@admin.register(Observation)
class ObservationAdmin(admin.ModelAdmin):
    list_display = ("weekly_map", "day_name", "time_slot", "state", "intensity", "created_by")
    list_filter = ("state", "day_name")
    search_fields = ("weekly_map__pupil_name",)
