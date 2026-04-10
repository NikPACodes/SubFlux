from rest_framework.permissions import BasePermission

class IsOwner(BasePermission):
    """
    Доступ только владельцу объекта
    """
    message = "У вас нет полномочий к этому объекту."

    def has_object_permission(self, request, view, obj):
        return obj.user_id == request.user.id