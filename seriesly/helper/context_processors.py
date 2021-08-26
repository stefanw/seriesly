from django.conf import settings


def site_info(request):
    return {
        "SITE_NAME": settings.SITE_NAME,
        "DOMAIN_URL": settings.DOMAIN_URL,
        "DEFAULT_FROM_EMAIL": settings.DEFAULT_FROM_EMAIL,
        "ADMIN_NAME": settings.ADMIN_NAME,
        "DEBUG": settings.DEBUG,
        "seriesly_features": settings.SERIESLY_FEATURES,
    }
