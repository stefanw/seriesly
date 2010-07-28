from django.template import Library
from django.utils.http import urlquote

register = Library()

@register.filter
def fixurl(value):
    """Escapes a value for use in a URL."""
    if value is None:
        return ""
    value = value.replace("http://", "")
    return "http://" + urlquote(value)
fixurl.is_safe = False

@register.filter
def rfc3339(date): 
    if date is None:
        return ""
    return date.strftime('%Y-%m-%dT%H:%M:%SZ')

