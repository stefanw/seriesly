
import re

def normalize(s):
    return re.sub("[^\w ]", "", s.lower())