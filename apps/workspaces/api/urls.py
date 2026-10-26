"""
URL-маршруты Workspace.

В OSS-версии SubFlux поддерживается работа только с
Default Workspace текущего пользователя.
"""
from rest_framework import routers
from apps.workspaces.api.views import DefaultWorkspaceViewSet


router = routers.SimpleRouter()
router.register(r'', DefaultWorkspaceViewSet, basename='workspace-default')

urlpatterns = router.urls