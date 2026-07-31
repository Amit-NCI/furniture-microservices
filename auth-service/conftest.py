import os
import sys
from unittest.mock import MagicMock

os.environ.pop('DJANGO_SETTINGS_MODULE', None)
sys.modules['pika'] = MagicMock()

# The Django app itself lives one level deeper, in auth_service/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'auth_service'))


def pytest_configure(config):
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DATABASES={
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': ':memory:',
                }
            },
            INSTALLED_APPS=[
                'django.contrib.contenttypes',
                'django.contrib.auth',
                'django.contrib.admin',
                'django.contrib.sessions',
                'rest_framework',
                'rest_framework_simplejwt',
                'corsheaders',
                'users',
            ],
            AUTH_USER_MODEL='users.User',
            DEFAULT_AUTO_FIELD='django.db.models.BigAutoField',
            REST_FRAMEWORK={
                'DEFAULT_AUTHENTICATION_CLASSES': [],
                'DEFAULT_PERMISSION_CLASSES': [],
            },
            SECRET_KEY='test-secret-key-not-used-in-production',
            DEBUG=True,
            ROOT_URLCONF='tests.test_auth',
            USE_TZ=True,
            SIMPLE_JWT={
                'SIGNING_KEY': 'test-jwt-signing-key',
                'ALGORITHM': 'HS256',
            },
        )