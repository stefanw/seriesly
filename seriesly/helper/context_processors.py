from django.conf import settings


def site_info(request):
    return {'APP_NAME': settings.APP_NAME,
            'DOMAIN_URL': settings.DOMAIN_URL,
            'SECURE_DOMAIN_URL': settings.SECURE_DOMAIN_URL,
            'DEFAULT_FROM_EMAIL': settings.DEFAULT_FROM_EMAIL,
            'ADMIN_NAME': settings.ADMIN_NAME,
            'DEBUG': settings.DEBUG}
