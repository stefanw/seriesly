from django import template

register = template.Library()


@register.filter
def rfc3339(date):
    if date is None:
        return ""
    return date.strftime("%Y-%m-%dT%H:%M:%SZ")
