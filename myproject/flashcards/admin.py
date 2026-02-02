from django.contrib import admin
from .models import Flashcard, Scenario

@admin.register(Flashcard)
class FlashcardAdmin(admin.ModelAdmin):
    list_display = ('flashcard_id', 'title', 'who_where_when_why', 'how_to_do_it', 'what_you_need', 'sort_order', 'image')


@admin.register(Scenario)
class ScenarioAdmin(admin.ModelAdmin):
    list_display = ('scenario_id', 'title', 'sort_order')
    ordering = ('sort_order',)

