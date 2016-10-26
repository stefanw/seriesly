# -*- coding: utf-8 -*-
import os

import dj_database_url


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
DOMAIN_URL = os_env('DOMAIN_URL', "https://serieslynew.herokuapp.com")

# Make this unique, and don't share it with anybody.
SECRET_KEY = os_env('DJANGO_SECRET_KEY', '02ca0jaadlbjk;.93nfnvopm 40mu4w0daadlclm fniemcoia984<mHMImlkFUHA=")JRFP"Om')

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

INSTALLED_APPS = (
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
)


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
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'ERROR'),
        },
    },
}


EMAIL_HOST = os_env('POSTMARK_SMTP_SERVER')
EMAIL_PORT = 2525
EMAIL_HOST_USER = os_env('POSTMARK_API_KEY')
EMAIL_HOST_PASSWORD = os_env('POSTMARK_API_KEY')
EMAIL_USE_TLS = True


try:
    from .local_settings import *  # noqa
except ImportError:
    pass
