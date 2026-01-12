from django.urls import path, include
from  rest_framework import routers
from .views import UserAdminViewSet

routers = routers.DefaultRouter()
routers.register(r'admin/users', UserAdminViewSet, basename='admin-users')

urlpatterns = [
    path('', include(routers.urls)),
]