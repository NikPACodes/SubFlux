from django.core.exceptions import ValidationError
from rest_framework import serializers

def as_drf_validation_error(exc: ValidationError) -> serializers.ValidationError:
    """
    Преобразует Django ValidationError в DRF ValidationError
    """
    if hasattr(exc, "message_dict"):
        return serializers.ValidationError(exc.message_dict)
    if hasattr(exc, "messages"):
        return serializers.ValidationError(exc.messages)
    return serializers.ValidationError(str(exc))


def call_service(func, *args, **kwargs):
    """
    Обёртка для вызова service layer с автоматическим преобразованием ошибок
    """
    try:
        return func(*args, **kwargs)
    except ValidationError as exc:
        raise as_drf_validation_error(exc)