from django.urls import path, include
from  rest_framework import routers
from .views import UserAdminViewSet

router = routers.DefaultRouter()
router.register(r'admin/users', UserAdminViewSet, basename='admin-users')

urlpatterns = [
    path('', include(router.urls)),
]