from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin

urlpatterns = patterns('',
    (r'^product_for_show/$', 'amazon.views.product_for_show', {}, "seriesly-amazon-product_for_show"),
    (r'^update/$', 'amazon.views.update', {}, "seriesly-amazon-update"),
)
