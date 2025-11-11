from django.urls import path
from . import views

app_name = 'resources'

urlpatterns = [
    path('', views.resource_list, name='resource_list'),
    path('tag/<slug:slug>/', views.resource_list_by_tag, name='resource_list_by_tag'),
    path('<slug:slug>/', views.resource_page, name='page'),
]
