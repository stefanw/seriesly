import re


def normalize(s):
    s = re.sub(r"\(\d{4}\)$", "", s)
    return re.sub("[^\w ]", "", s.lower())
