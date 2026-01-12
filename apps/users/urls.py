from  django.urls import path, include

urlpatterns=[
    path('api/users/', include('apps.users.api.urls')),
]