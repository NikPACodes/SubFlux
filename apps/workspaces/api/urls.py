from django.urls import path, include
from  rest_framework import routers
from apps.workspaces.api.views import DefaultWorkspaceViewSet


router = routers.DefaultRouter()
router.register(r'/me', DefaultWorkspaceViewSet, basename='workspace-default')

urlpatterns = [
    path('', include(router.urls)),
]