# -*- coding: utf-8 -*-
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Increase this when you update your media on the production site, so users
# don't have to refresh their cache. By setting this your MEDIA_URL
# automatically becomes /media/MEDIA_VERSION/
DEBUG = False

ADMIN_USERS = ()

ALLOWED_HOSTS = ['*']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
# 'project' refers to the name of the module created with django-admin.py
ROOT_URLCONF = 'seriesly.urls'

DEFAULT_FROM_EMAIL = 'mail@seriesly.com'
SERVER_EMAIL = DEFAULT_FROM_EMAIL

ADMIN_NAME = "Stefan Wehrmeyer"

DOMAIN_URL = "https://serieslycom.appspot.com"
SECURE_DOMAIN_URL = "https://serieslycom.appspot.com"

# Make this unique, and don't share it with anybody.
SECRET_KEY = '02ca0jaadlbjk;.93nfnvopm 40mu4w0daadlclm fniemcoia984<mHMImlkFUHA=")JRFP"Om'

TEMPLATE_CONTEXT_PROCESSORS = (
    # 'django.core.context_processors.auth',
    'django.core.context_processors.media',
    'django.core.context_processors.request',
    # 'django.core.context_processors.i18n',
    'seriesly.helper.context_processors.site_info',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    # 'django.contrib.sessions.middleware.SessionMiddleware',
    # 'django.contrib.auth.middleware.AuthenticationMiddleware',
    # 'django.middleware.doc.XViewMiddleware',

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

    'seriesly.series',
    'seriesly.subscription',
    'seriesly.helper',
    'seriesly.statistics',
)

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or
    # "C:/www/django/templates".  Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(BASE_DIR, 'templates'),
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

try:
    from local_settings import *  # noqa
except ImportError:
    pass
