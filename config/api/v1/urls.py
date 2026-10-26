from django.urls import include, path

urlpatterns = [
    path('', include('apps.users.api.urls')),

    # Справочники
    path('', include('apps.subscriptions.api.catalog_urls')),

    # Default Workspace
    path('me/', include('config.api.v1.me_urls')),
]