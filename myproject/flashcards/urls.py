# flashcards/urls.py
from django.urls import path
from . import views

app_name = 'flashcards' 

urlpatterns = [
    path('', views.flashcards_page, name='flashcards_page'),
    path('stream/', views.stream_flashcards, name='stream_flashcards'),
    path('filtered/', views.filtered_flashcards, name="filtered_flashcards"),
    path('save_ids/', views.save_flashcard_ids, name='save_flashcard_ids'),
    path('session/<str:session_id>/', views.chat_session, name='chat_session'),
    path("delete/<str:session_id>/", views.delete_chat_session, name="delete_chat_session"),
    path("rename/<str:session_id>/", views.rename_chat_session, name="rename_chat_session"),
    path("export/<str:session_id>/", views.export_chat_session, name="export_chat_session"),
    path('chat_history_partial/', views.chat_history_partial, name='chat_history_partial'),
]