from  django.urls import path, include

urlpatterns=[
    path('api/', include('apps.users.api.urls')),
]