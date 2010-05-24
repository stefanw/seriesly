import logging, os, sys
import traceback
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from google.appengine.dist import use_library

use_library('django', '1.1')
# Google App Engine imports.
from google.appengine.ext.webapp.util import run_wsgi_app

# Force sys.path to have our own directory first, in case we want to import
# from it.
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Must set this env var *before* importing any part of Django

from django import db
from django.core import signals
import django.core.handlers.wsgi
 
 
def log_exception(sender, **kwargs):
    logging.exception('Exception in request:\n' + ''.join(traceback.format_exception(*sys.exc_info())))
    if 'request' in kwargs:
        try:
            repr_request = repr(kwargs['request'])
        except:
            repr_request = 'Request repr() not available.'
    else:
        repr_request = 'Request not available.'
    logging.exception("Request: %s" % repr_request)
 
signals.got_request_exception.connect(log_exception)
signals.got_request_exception.disconnect(db._rollback_on_exception)


def main():
    # Create a Django application for WSGI.
    application = django.core.handlers.wsgi.WSGIHandler()
    # Run the WSGI CGI handler with that application.
    run_wsgi_app(application)

if __name__ == '__main__':
    main()