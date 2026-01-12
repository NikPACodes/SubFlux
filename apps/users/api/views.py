from  django.contrib.auth import get_user_model
from rest_framework.permissions import IsAdminUser
from rest_framework.viewsets import ModelViewSet

from .serializers import UserCreateSerializer, UserDetailSerializer, UserPublicSerializer

User = get_user_model()

# TODO реализован для тестирования в дальнейшем ужесточить и переделать в APIView
class UserAdminViewSet(ModelViewSet):
    """
    API ViewSet создания пользователя

    ВАЖНО
    - Создаёт пользователя. Точка регистрации без авторизации.
    - Доступна только администраторам
    - Реализован для тестирования
    """
    permission_classes = [IsAdminUser]
    queryset = User.objects.all().order_by('-id')

    def get_serializer_class(self):
        # Для создания сериализатор с password (write_only)
        if self.action == 'create':
            return UserCreateSerializer
        return UserDetailSerializer