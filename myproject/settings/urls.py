from django.contrib import admin
from django.urls import path, include, re_path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve

urlpatterns = [
    # Static and media routes (for dev; not recommended in production)
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),

    # Admin and core pages
    path('admin/', admin.site.urls),
    path('', views.homepage),
    path('about/', views.about),

    # App routes
    path('posts/', include('myproject.posts.urls')),
    path('users/', include('myproject.users.urls')),
    path('evaluation/', include('myproject.evaluation.urls')),
    path('flashcards/', include('myproject.flashcards.urls')),
    path('training/', include('myproject.training.urls')),
    path('sdq/', include('myproject.sdq.urls')),
    path('resources/', include('myproject.resources.urls')),
]

# Serve static and media files in development mode
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
