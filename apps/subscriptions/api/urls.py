from django.urls import path, include
from  rest_framework import routers
from .views import CategoryViewSet, CategoryReadViewSet

router = routers.DefaultRouter()
router.register(r'admin/categories', CategoryViewSet, basename='admin-categories')
router.register(r'categories', CategoryReadViewSet, basename='categories')

urlpatterns = [
    path('', include(router.urls)),
]