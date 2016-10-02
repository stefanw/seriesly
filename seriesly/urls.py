# -*- coding: utf-8 -*-
from django.conf.urls import url, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin

urlpatterns = [
    url(r'^', include('seriesly.subscription.subscription_urls')),
    url(r'^shows/', include('seriesly.series.urls')),
    url(r'^subscription/', include('seriesly.subscription.urls')),
    url(r'^admin/', include(admin.site.urls)),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
