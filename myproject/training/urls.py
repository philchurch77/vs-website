from django.urls import path
from . import views

app_name = 'training'

urlpatterns = [
    path('trainingrequest/', views.Training_Request_New, name="training_request"),
]
