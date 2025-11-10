# sdq/urls.py
from django.urls import path
from . import views

app_name = 'sdq' 

urlpatterns = [
    path("", views.sdq_view, name="sdq_form_view"),
]
