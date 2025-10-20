from django.urls import path
from . import views

app_name = "evaluation"

urlpatterns = [
    path("", views.chat_page, name="chat_page"),
    path("new/", views.new_chat_session, name="new_chat_session"),
    path("session/<str:session_id>/", views.chat_session, name="chat_session"),
    path("stream/", views.stream_chatgpt_api, name="stream_chat"),
    path("chat_history_partial/", views.chat_history_partial, name="chat_history_partial"),
    path("reset-chat-session/", views.reset_chat_session, name="reset_chat_session"),
]
