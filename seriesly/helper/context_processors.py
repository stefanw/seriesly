from django.conf import settings

def site_info(request):
    return {'DOMAIN_URL': settings.DOMAIN_URL,
            'SECURE_DOMAIN_URL': settings.SECURE_DOMAIN_URL,
            'DEBUG': settings.DEBUG,
            'AMAZON': settings.AMAZON_ENABLED}