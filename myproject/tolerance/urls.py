from django.urls import path
from . import views

app_name = "tolerance"

urlpatterns = [
    # Main weekly mapping tool
    path("", views.dashboard, name="dashboard"),
    path("weekly/<int:pk>/", views.weekly_map_detail, name="weekly_map_detail"),
    path("weekly/<int:pk>/delete/", views.delete_weekly_map, name="delete_weekly_map"),
    path("weekly/<int:pk>/api/observation/", views.api_save_observation, name="api_save_observation"),
    path("weekly/<int:pk>/api/support-plan/", views.api_save_support_plan, name="api_save_support_plan"),
    path("weekly/<int:pk>/api/visible-slots/", views.api_save_visible_slots, name="api_save_visible_slots"),
]
