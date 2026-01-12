from django.shortcuts import Http404

def admin_only(view_func):
    """
    Декоратор для проверки на staff-пользователей.
    """
    def wrapper(request, *args, **kwargs):
        user = request.user
        if user and user.is_authenticated and user.is_staff:
            return view_func(request, *args, **kwargs)
        return Http404
    return wrapper