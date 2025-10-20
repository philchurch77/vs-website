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
    path('posts/', include('posts.urls')),
    path('users/', include('users.urls')),
    path('evaluation/', include('evaluation.urls')),
    path('flashcards/', include('flashcards.urls')),
    path('training/', include('training.urls')),
    path('sdq/', include(('sdq.urls', 'sdq'), namespace='sdq')),
]

# Serve static and media files in development mode
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
