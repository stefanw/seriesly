# -*- coding: utf-8 -*-
import os
ROOT_PATH = os.path.dirname(__file__)

from google.appengine.api import apiproxy_stub_map
have_appserver = bool(apiproxy_stub_map.apiproxy.GetStub('datastore_v3'))
on_production_server = have_appserver and \
    not os.environ.get('SERVER_SOFTWARE', '').lower().startswith('devel')


# Increase this when you update your media on the production site, so users
# don't have to refresh their cache. By setting this your MEDIA_URL
# automatically becomes /media/MEDIA_VERSION/
DEBUG = False

ADMIN_USERS = ()

MEDIA_VERSION = 1
if not on_production_server:
    DEBUG = True
# By hosting media on a different domain we can get a speedup (more parallel
# browser connections).
#if on_production_server or not have_appserver:
#    MEDIA_URL = 'http://media.mydomain.com/media/%d/'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(ROOT_PATH, 'media')
# 'project' refers to the name of the module created with django-admin.py
ROOT_URLCONF = 'urls'

DEFAULT_FROM_EMAIL = 'mail@seriesly.com'
SERVER_EMAIL = DEFAULT_FROM_EMAIL

ADMIN_NAME = "Stefan Wehrmeyer"

DOMAIN_URL = "https://serieslycom.appspot.com"
SECURE_DOMAIN_URL = "https://serieslycom.appspot.com"

# Make this unique, and don't share it with anybody.
SECRET_KEY = '02ca0jaadlbjk;.93nfnvopm 40mu4w0daadlclm fniemcoia984<mHMImlkFUHA=")JRFP"Om'

TEMPLATE_CONTEXT_PROCESSORS = (
#    'django.core.context_processors.auth',
    'django.core.context_processors.media',
    'django.core.context_processors.request',
#    'django.core.context_processors.i18n',
    'helper.context_processors.site_info',
)

MIDDLEWARE_CLASSES = (
   # 'google.appengine.ext.appstats.recording.AppStatsDjangoMiddleware',
   'django.middleware.common.CommonMiddleware',
#    'django.contrib.sessions.middleware.SessionMiddleware',
#    'django.contrib.auth.middleware.AuthenticationMiddleware',
#    'django.middleware.doc.XViewMiddleware',
    'google.appengine.ext.appstats.recording.AppStatsDjangoMiddleware',
    'google.appengine.ext.ndb.django_middleware.NdbDjangoMiddleware',
)

INSTALLED_APPS = (

#    'django.contrib.auth',
#    'django.contrib.sessions',
#    'django.contrib.admin',
#    'django.contrib.webdesign',
#    'django.contrib.flatpages',
#    'django.contrib.redirects',
#    'django.contrib.sites',
    'series',
    'subscription',
    'helper',
    'statistics',
#    'mediautils',
)

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or
    # "C:/www/django/templates".  Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    ROOT_PATH + '/templates',
)

try:
    from local_settings import *
except ImportError:
    pass
