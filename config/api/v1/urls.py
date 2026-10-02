from django.urls import include, path


urlpatterns = [
    path('', include('apps.users.api.urls')),
    path('', include('apps.subscriptions.api.urls')),
    path('', include('apps.workspaces.api.urls')),
]