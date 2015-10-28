import requests


def get(url):
    response = requests.get(url)
    if response.status_code != 200:
        raise IOError
    return response.content


def post(url, content):
    return requests.post(
        url,
        data=content,
    )
