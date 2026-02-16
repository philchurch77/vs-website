from django.contrib import admin
from .models import Post
from taggit.models import TaggedItem
from taggit.managers import TaggableManager as TaggableManagerField

class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'author']
    list_filter = ['date', 'author']
    search_fields = ['title']
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'date'
    fields = ['title', 'slug', 'author', 'body', 'image', 'tags']

admin.site.register(Post, PostAdmin)
