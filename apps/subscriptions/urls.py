from  django.urls import path, include

urlpatterns=[
    path('api/subscriptions/', include('apps.subscriptions.api.urls')),
]