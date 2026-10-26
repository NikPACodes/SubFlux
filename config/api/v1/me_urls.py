"""
URL-маршруты Default Workspace.
"""
from django.urls import include, path

urlpatterns = [
    path('', include('apps.workspaces.api.urls')),
    path('', include('apps.subscriptions.api.urls')),
]
