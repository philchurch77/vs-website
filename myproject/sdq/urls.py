# sdq/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("", views.sdq_view, name="sdq_form_view"),
]
