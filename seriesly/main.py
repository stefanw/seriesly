import logging
import os
import sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

# Force sys.path to have our own directory first, in case we want to import
# from it.
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/pytvmaze"))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Must set this env var *before* importing any part of Django

# import django.db
import django.core.signals
import django.dispatch
import django.core.handlers.wsgi


def log_exception(sender, **kwargs):
    if 'request' in kwargs:
        try:
            repr_request = repr(kwargs['request'])
        except:
            repr_request = 'Request repr() not available.'
    else:
        repr_request = 'Request not available.'
    if logging is not None:
        logging.exception("Request: %s" % repr_request)


django.dispatch.Signal.connect(
    django.core.signals.got_request_exception, log_exception)

# django.dispatch.Signal.disconnect(
#     django.core.signals.got_request_exception,
#     django.db._rollback_on_exception)


app = django.core.handlers.wsgi.WSGIHandler()
