from django.template import Library
from django.utils.http import urlquote

register = Library()

@register.filter
def fixurl(value):
    """Escapes a value for use in a URL."""
    value = value.replace("http://", "")
    return "http://" + urlquote(value)
fixurl.is_safe = False

@register.filter
def rfc3339(date): 
    return date.strftime('%Y-%m-%dT%H:%M:%SZ')
    
