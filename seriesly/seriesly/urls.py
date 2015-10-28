# -*- coding: utf-8 -*-
from django.conf.urls import url, include
from django.conf import settings
from django.conf.urls.static import static

from django.views.generic import RedirectView, TemplateView


urlpatterns = [
    url(r'^', include('seriesly.subscription.subscription_urls')),
    url(r'^faq/$', TemplateView.as_view(template_name='faq.html'), name="seriesly-faq"),
    url(r'^imprint/$', RedirectView.as_view(url='/about/#impressum')),
    url(r'^terms/$', TemplateView.as_view(template_name='terms.html'), name="seriesly-terms"),
    url(r'^about/$', TemplateView.as_view(template_name='about.html'), name="seriesly-about"),
    url(r'^privacy/$', TemplateView.as_view(template_name='privacy.html'), name="seriesly-privacy"),
    url(r'^missing/$', TemplateView.as_view(template_name='missing.html'), name="seriesly-missing"),
    url(r'^webhook-xml/$', TemplateView.as_view(template_name='webhook_xml.html'), name="seriesly-webhook-xml"),
    url(r'^shows/', include('seriesly.series.urls')),
    url(r'^subscription/', include('seriesly.subscription.urls')),
    # (r'^statistics/', include('statistics.urls')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
