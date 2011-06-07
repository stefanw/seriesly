# -*- coding: utf-8 -*-
from ragendja.settings_pre import *
import os.path
from appenginepatcher import on_production_server, have_appserver

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))


# Increase this when you update your media on the production site, so users
# don't have to refresh their cache. By setting this your MEDIA_URL
# automatically becomes /media/MEDIA_VERSION/
MEDIA_VERSION = 1

# By hosting media on a different domain we can get a speedup (more parallel
# browser connections).
#if on_production_server or not have_appserver:
#    MEDIA_URL = 'http://media.mydomain.com/media/%d/'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(PROJECT_ROOT, 'media')

# Add base media (jquery can be easily added via INSTALLED_APPS)

# Change your email settings
if on_production_server:
    DEFAULT_FROM_EMAIL = 'mail@stefanwehrmeyer.com'
    SERVER_EMAIL = DEFAULT_FROM_EMAIL
    
DOMAIN_URL = "http://www.seriesly.com"

# Make this unique, and don't share it with anybody.
SECRET_KEY = '02ca0jaadlbjk;.93nfnvopm 40mu4w0daadlclm fniemcoia984<mHMImlkFUHA=")JRFP"Om'

#ENABLE_PROFILER = True
#ONLY_FORCED_PROFILE = True
#PROFILE_PERCENTAGE = 25
#SORT_PROFILE_RESULTS_BY = 'cumulative' # default is 'time'
# Profile only datastore calls
#PROFILE_PATTERN = 'ext.db..+\((?:get|get_by_key_name|fetch|count|put)\)'

# Enable I18N and set default language to 'en'
USE_I18N = False
LANGUAGE_CODE = 'en'

# Restrict supported languages (and JS media generation)
LANGUAGES = (
    ('en', 'English'),
)

TEMPLATE_CONTEXT_PROCESSORS = (
#    'django.core.context_processors.auth',
    'django.core.context_processors.media',
    'django.core.context_processors.request',
#    'django.core.context_processors.i18n',
    'helper.context_processors.site_info',
)

MIDDLEWARE_CLASSES = (
#    'ragendja.middleware.ErrorMiddleware',
#    'django.contrib.sessions.middleware.SessionMiddleware',
    # Django authentication
#    'django.contrib.auth.middleware.AuthenticationMiddleware',
    # Google authentication
    #'ragendja.auth.middleware.GoogleAuthenticationMiddleware',
    # Hybrid Django/Google authentication
    #'ragendja.auth.middleware.HybridAuthenticationMiddleware',
    'django.middleware.common.CommonMiddleware',
#    'django.middleware.locale.LocaleMiddleware',
#    'ragendja.sites.dynamicsite.DynamicSiteIDMiddleware',
#    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
#    'django.contrib.redirects.middleware.RedirectFallbackMiddleware',
)

# Google authentication
#AUTH_USER_MODULE = 'ragendja.auth.google_models'
#AUTH_ADMIN_MODULE = 'ragendja.auth.google_admin'
# Hybrid Django/Google authentication
#AUTH_USER_MODULE = 'ragendja.auth.hybrid_models'

LOGIN_REDIRECT_URL = '/'

INSTALLED_APPS = (

#    'django.contrib.auth',
#    'django.contrib.sessions',
#    'django.contrib.admin',
#    'django.contrib.webdesign',
#    'django.contrib.flatpages',
#    'django.contrib.redirects',
#    'django.contrib.sites',
    'appenginepatcher',
    'series',
    'subscription',
    'helper',
#    'mediautils',
)

# List apps which should be left out from app settings and urlsauto loading
IGNORE_APP_SETTINGS = IGNORE_APP_URLSAUTO = (
    # Example:
    # 'django.contrib.admin',
    # 'django.contrib.auth',
    # 'yetanotherapp',
)

# Remote access to production server (e.g., via manage.py shell --remote)
DATABASE_OPTIONS = {
    # Override remoteapi handler's path (default: '/remote_api').
    # This is a good idea, so you make it not too easy for hackers. ;)
    # Don't forget to also update your app.yaml!
    #'remote_url': '/remote-secret-url',

    # !!!Normally, the following settings should not be used!!!

    # Always use remoteapi (no need to add manage.py --remote option)
    #'use_remote': True,

    # Change appid for remote connection (by default it's the same as in
    # your app.yaml)
    #'remote_id': 'otherappid',

    # Change domain (default: <remoteid>.appspot.com)
    #'remote_host': 'bla.com',
}


DEBUG = not on_production_server
#DEBUG = False

SERVE_MEDIA = DEBUG

ADMINS = ()

DATABASE_ENGINE = 'appengine'
DATABASE_SUPPORTS_TRANSACTIONS = False


EMAIL_HOST = 'localhost'
EMAIL_PORT = 25
EMAIL_HOST_USER = 'user'
EMAIL_HOST_PASSWORD = 'password'
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = 'mail@seriesly.com'
SERVER_EMAIL = 'user@localhost'

ROOT_URLCONF = 'urls'

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
#    'ragendja.template.app_prefixed_loader',
    'django.template.loaders.app_directories.load_template_source',
)

TEMPLATE_DIRS = (
    os.path.join(PROJECT_ROOT, "templates"),
)


CACHE_BACKEND = 'memcached://?timeout=0'

from ragendja.settings_post import *
