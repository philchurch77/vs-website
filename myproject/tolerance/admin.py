from django.contrib import admin
from .models import Keyword, DailyCheckIn


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
