from django.urls import path
from . import views

app_name = "animation"

urlpatterns = [
    path("", views.chat_page, name="chat_page"),
    path("new/", views.new_chat_session, name="new_chat_session"),
    path("stream/", views.stream_animation_api, name="stream_animation_api"),
    path("reset-chat-session/", views.reset_chat_session, name="reset_chat_session"),
    path("chat_history_partial/", views.chat_history_partial, name="chat_history_partial"),
    path("session/<str:session_id>/", views.chat_session, name="chat_session"),
    path("session/<str:session_id>/delete/", views.delete_chat_session, name="delete_chat_session"),
    path("session/<str:session_id>/rename/", views.rename_chat_session, name="rename_chat_session"),
    path("session/<str:session_id>/export/", views.export_chat_session, name="export_chat_session"),
]
