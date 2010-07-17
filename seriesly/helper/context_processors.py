from django.conf import settings

def site_info(request):
    return {'DOMAIN_URL': settings.DOMAIN_URL}