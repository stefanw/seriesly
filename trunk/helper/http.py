from google.appengine.api import urlfetch

def get(url):
    response = urlfetch.fetch(url, deadline=10)
    if response.status_code != 200:
        raise IOError
    return response.content
    
def post(url, content):
    return urlfetch.fetch(url, payload=content, method=urlfetch.POST, follow_redirects=True)
    