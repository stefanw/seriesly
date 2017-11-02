# -*- coding: utf-8 -*-
import os

import dj_database_url
from celery.schedules import crontab


def os_env(name, default=None):
    return os.environ.get(name, default)

BASE_DIR = os.path.dirname(__file__)

# Increase this when you update your media on the production site, so users
# don't have to refresh their cache. By setting this your MEDIA_URL
# automatically becomes /media/MEDIA_VERSION/
DEBUG = False

ADMIN_USERS = ()

ALLOWED_HOSTS = ['*']

DATABASES = {
    'default': dj_database_url.config(env='DATABASE_URL',
            default='sqlite:///' + os.path.join(BASE_DIR, 'db.sqlite3'))
}

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
# 'project' refers to the name of the module created with django-admin.py
ROOT_URLCONF = 'seriesly.urls'

DEFAULT_FROM_EMAIL = 'mail@seriesly.com'
SERVER_EMAIL = DEFAULT_FROM_EMAIL

ADMIN_NAME = "Stefan Wehrmeyer"

SITE_NAME = 'Seriesly'
DOMAIN_URL = os_env('DOMAIN_URL', "http://localhost:8000")

# Make this unique, and don't share it with anybody.
SECRET_KEY = os_env('DJANGO_SECRET_KEY', 'not-so-secret')

SITE_ID = 1

USE_TZ = True

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': (
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.media',
                'django.template.context_processors.request',
                'django.template.context_processors.i18n',
                'django.contrib.messages.context_processors.messages',
                'seriesly.helper.context_processors.site_info',
            )
        },
    },
]

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware'
)

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.contenttypes',
    'django.contrib.admin',
    'django.contrib.flatpages',
    'django.contrib.redirects',
    'django.contrib.sites',
    'django.contrib.staticfiles',
    'django.contrib.messages',

    'seriesly.series',
    'seriesly.subscription',
    'seriesly.helper',
]


STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, "public", "static")

# Additional locations of static files
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, "static"),
)

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': ('%(asctime)s [%(process)d] [%(levelname)s] ' +
                       'pathname=%(pathname)s lineno=%(lineno)s ' +
                       'funcname=%(funcName)s %(message)s'),
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        },
    },
}

BROKER_URL = os.environ.get("CLOUDAMQP_URL", "django://")
BROKER_POOL_LIMIT = 1
BROKER_CONNECTION_MAX_RETRIES = None
if BROKER_URL == "django://":
    INSTALLED_APPS += ["kombu.transport.django"]


CELERY_TASK_SERIALIZER = "json"
CELERY_ALWAYS_EAGER = bool(int(os_env('CELERY_ALWAYS_EAGER', '1')))
CELERY_ACCEPT_CONTENT = ['json']
CELERYD_MAX_TASKS_PER_CHILD = 1
CELERY_TIMEZONE = 'UTC'
CELERY_ROUTES = {
    'seriesly.series.tasks.update_all_shows': {'queue': 'update_show'},
    'seriesly.series.tasks.update_show': {'queue': 'update_show'},
}

CELERYBEAT_SCHEDULE = {
    'update-shows': {
        'task': 'seriesly.series.tasks.update_all_shows',
        'schedule': crontab(minute=0, hour=0),
        'options': {
            'expires': 60 * 60 * 12
        }
    },
}

CELERY_TIMEZONE = 'UTC'

EMAIL_HOST = os_env('POSTMARK_SMTP_SERVER')
EMAIL_PORT = 2525
EMAIL_HOST_USER = os_env('POSTMARK_API_TOKEN')
EMAIL_HOST_PASSWORD = os_env('POSTMARK_API_TOKEN')
EMAIL_USE_TLS = True

SERIESLY_FEATURES = {
    'feed': True,
    'guide': True,
    'email': False,
    'calendar': True,
    'webhook': False,
    'public': True
}


try:
    from .local_settings import *  # noqa
except ImportError:
    pass
