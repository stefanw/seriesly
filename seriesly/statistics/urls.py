from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin

urlpatterns = patterns('',
    (r'^subscriptions/$', 'statistics.views.subscriptions', {}, "seriesly-statistics-subscriptions"),
    (r'^subscribed_shows/$', 'statistics.views.subscribed_shows', {}, "seriesly-statistics-subscribed_shows"),
)
