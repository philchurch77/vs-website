from django.urls import path
from . import views

app_name = "animation"

urlpatterns = [
    path("", views.chat_page, name="chat_page"),
    path("new/", views.new_chat_session, name="new_chat_session"),
]
