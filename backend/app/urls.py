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
    path('search/hybrid', views.hybrid_search_documents, name='hybrid_search_documents'),

    # Task-aware search and documents
    path('tasks/<int:task_id>/documents', views.get_task_documents, name='get_task_documents'),
    path('tasks/documents/add', views.add_documents_to_task, name='add_documents_to_task'),

    # Analytics
    path('analytics', views.get_analytics, name='get_analytics'),

    # Users
    path('users', views.list_users, name='list_users'),

    # Index Optimization (Admin Only)
    path('admin/index/batch', views.batch_index_documents, name='batch_index_documents'),
    path('admin/index/stats', views.get_index_stats, name='get_index_stats'),
    path('admin/index/optimize', views.optimize_index, name='optimize_index'),
    path('admin/index/rebuild', views.rebuild_search_index, name='rebuild_search_index'),
]
