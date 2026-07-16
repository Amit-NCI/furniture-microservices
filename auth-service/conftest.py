import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'auth_service'))

from django.conf import settings


def pytest_configure():
    settings.DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }
    settings.DEBUG = True