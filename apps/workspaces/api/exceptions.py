from rest_framework import status
from rest_framework.exceptions import APIException


class WorkspaceDeactivated(APIException):
    """
    Default Workspace пользователя деактивирован.
    """
    status_code = status.HTTP_409_CONFLICT
    default_code = 'workspace_deactivated'

    def __init__(self):
        super().__init__(
            detail={
                'code': self.default_code,
                'detail': 'Default Workspace деактивирован.',
                'action': {
                    'method': 'POST',
                    'url': '/v1/me/status/',
                    'body': {
                        'status': 'active',
                    },
                },
            }
        )