import logging
try:
    from google.appengine.api.urlfetch import fetch as urlfetch_fetch
except ImportError:
    logging.warn("There's no Appengine UrlFetch")
    urlfetch_fetch = lambda x: x

def get(url):
    response = urlfetch_fetch(url, deadline=10)
    if response.status_code != 200:
        raise IOError
    return response.content
    
def post(url, content):
    return urlfetch_fetch(url, payload=content, method="POST", follow_redirects=True)
    