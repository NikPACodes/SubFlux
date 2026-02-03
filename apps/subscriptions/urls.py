from  django.urls import path, include

urlpatterns=[
    path('api/', include('apps.subscriptions.api.urls')),
]