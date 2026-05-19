from django.urls import path
from . import views

app_name = "tolerance"

urlpatterns = [
    # Main weekly mapping tool
    path("", views.dashboard, name="dashboard"),
    path("weekly/<int:pk>/", views.weekly_map_detail, name="weekly_map_detail"),
    path("weekly/<int:pk>/api/observation/", views.api_save_observation, name="api_save_observation"),
    path("weekly/<int:pk>/api/support-plan/", views.api_save_support_plan, name="api_save_support_plan"),

    # Legacy staff self check-in
    path("checkin/", views.checkin_dashboard, name="checkin_dashboard"),
    path("api/toggle-keyword/", views.toggle_keyword, name="toggle_keyword"),
    path("api/save-notes/", views.save_notes, name="save_notes"),
]
