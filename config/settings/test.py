"""
Test - настройки для тестов
"""
from dotenv import load_dotenv
from pathlib import Path

ENV_TEST_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(ENV_TEST_DIR / '.env.test')

from .base import *

# --------------------------------------------------------------------------
# Core
# --------------------------------------------------------------------------
DEBUG = False
TESTING = True
ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost',
]


# --------------------------------------------------------------------------
# Django REST Framework
# --------------------------------------------------------------------------
REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    'DEFAULT_RENDERER_CLASSES': [
        # Рендер для превращения объектов в JSON
        'rest_framework.renderers.JSONRenderer',
    ]
}
