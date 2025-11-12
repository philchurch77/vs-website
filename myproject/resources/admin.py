from django.contrib import admin
from .models import Topic

@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "author", "date")
    list_filter = ("author",)            # 'date' is fine in date_hierarchy below
    search_fields = ("title", "slug")    # add "body" here if you add that field
    prepopulated_fields = {"slug": ("title",)}
    date_hierarchy = "date"

    # Do NOT put 'date' in fields; it's non-editable
    fields = ("title", "slug", "author", "tags", "file", "link", "body")  # add "body" if you have it
    readonly_fields = ("date",)

    autocomplete_fields = ("author",)

    def save_model(self, request, obj, form, change):
        # If you want to default the author to the current user on create:
        if not obj.author_id:
            obj.author = request.user
        super().save_model(request, obj, form, change)
