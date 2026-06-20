"""
Dev - настройки для локальной разработки
"""
from dotenv import load_dotenv
from pathlib import Path

ENV_DEV_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(ENV_DEV_DIR / '.env.dev')

from .base import *

# --------------------------------------------------------------------------
# Core
# --------------------------------------------------------------------------
DEBUG = True
ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost',
]

INTERNAL_IPS = [
    '127.0.0.1',
    'localhost',
]


# --------------------------------------------------------------------------
# Application
# --------------------------------------------------------------------------
INSTALLED_APPS += [
    'debug_toolbar',
]

MIDDLEWARE = [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    *MIDDLEWARE,
]


# --------------------------------------------------------------------------
# Django REST Framework
# --------------------------------------------------------------------------
REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    'DEFAULT_RENDERER_CLASSES': [
        # Рендер для превращения объектов в JSON
        'rest_framework.renderers.JSONRenderer',
        # Интерактивный интерфейс для endpoints
        'rest_framework.renderers.BrowsableAPIRenderer',
    ]
}


# --------------------------------------------------------------------------
# Spectacular
# --------------------------------------------------------------------------
SPECTACULAR_SETTINGS = {
    **SPECTACULAR_SETTINGS,

    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': True,
    },

    # 'SECURITY': [
    #     {
    #         'Bearer': [],
    #     }
    # ],
    # 'SECURITY_SCHEMES': {
    #     'Bearer': {
    #         'type': 'http',
    #         'scheme': 'bearer',
    #         'bearerFormat': 'JWT',
    #     }
    # }
}


# --------------------------------------------------------------------------
# Logging
# --------------------------------------------------------------------------
LOGGING = {

}