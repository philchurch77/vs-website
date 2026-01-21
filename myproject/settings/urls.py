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
    path('posts/',      include('myproject.posts.urls', namespace='posts')),
    path('users/',      include('myproject.users.urls', namespace='users')),
    path('evaluation/', include('myproject.evaluation.urls', namespace='evaluation')),
    path('flashcards/', include('myproject.flashcards.urls', namespace='flashcards')),
    path('training/',   include('myproject.training.urls', namespace='training')),
    path('sdq/',        include('myproject.sdq.urls', namespace='sdq')),
    path('resources/',  include('myproject.resources.urls', namespace='resources')),
    path('tolerance/',  include('myproject.tolerance.urls', namespace='tolerance')),
    path('animation/',  include('myproject.animation.urls', namespace='animation')),
]

# Serve static and media files in development mode
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)