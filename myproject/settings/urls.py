from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.urls import path, include, re_path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve

urlpatterns = [
    # Admin and core pages
    path('admin/', admin.site.urls),
    path('', views.homepage),

    # App routes. allauth's urls are deliberately NOT mounted: they include an
    # open /accounts/signup/ view, and self-registration must stay closed.
    path('users/',      include('myproject.users.urls', namespace='users')),
    path('flashcards/', include('myproject.flashcards.urls', namespace='flashcards')),
    path('sdq/',        include('myproject.sdq.urls', namespace='sdq')),
    path('resources/',  include('myproject.resources.urls', namespace='resources')),
    path('tolerance/',  include('myproject.tolerance.urls', namespace='tolerance')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # WhiteNoise serves static in production. Media (admin-uploaded documents
    # and flashcard images) is served to logged-in staff only.
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', login_required(serve), {'document_root': settings.MEDIA_ROOT}),
    ]
