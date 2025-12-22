from django.urls import path
from . import views

app_name = "tolerance"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("api/toggle-keyword/", views.toggle_keyword, name="toggle_keyword"),
    path("api/save-notes/", views.save_notes, name="save_notes"),
]
