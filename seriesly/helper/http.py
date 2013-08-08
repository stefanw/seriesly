import logging

try:
    from google.appengine.api.urlfetch import fetch as urlfetch_fetch
except ImportError:
    logging.warn("There's no Appengine UrlFetch")

    def urlfetch_fetch(url, deadline=10):  # noqa
        import httplib
        url = url[len("http://"):]
        conn = httplib.HTTPConnection(url[:url.find("/")])
        conn.request("GET", url[url.find("/"):])
        response = conn.getresponse()
        print response.status, response.reason
        data = response.read()
        return data


def get(url):
    response = urlfetch_fetch(url, deadline=10)
    if hasattr(response, 'status_code'):
        if response.status_code != 200:
            raise IOError
        return response.content
    else:
        return response


def post(url, content):
    return urlfetch_fetch(
        url,
        payload=content,
        method="POST",
        follow_redirects=True
    )
