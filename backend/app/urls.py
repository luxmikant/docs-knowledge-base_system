"""
URL routing for app
"""
from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('auth/login', views.login, name='login'),
    path('auth/signup', views.signup, name='signup'),
    path('auth/me', views.get_current_user, name='current_user'),

    # Tasks
    path('tasks', views.tasks_endpoint, name='tasks_endpoint'),
    path('tasks/create', views.create_task, name='create_task'),
    path('tasks/<int:task_id>', views.update_task, name='update_task'),

    # Documents
    path('documents', views.documents_endpoint, name='documents_endpoint'),
    path('documents/<int:document_id>', views.get_document_detail, name='document_detail'),

    # Semantic search
    path('search', views.search_documents, name='search_documents'),

    # Analytics
    path('analytics', views.get_analytics, name='get_analytics'),

    # Users
    path('users', views.list_users, name='list_users'),
]
