"""
WSGI config for correctiv_community project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/dev/howto/deployment/wsgi/
"""

import sys
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "seriesly.settings")

project = os.path.dirname(__file__)
sys.path.append(project)

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

try:
    from whitenoise.django import DjangoWhiteNoise
    application = DjangoWhiteNoise(application)
except ImportError:
    pass
