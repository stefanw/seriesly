from django.conf.urls.defaults import patterns

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin

urlpatterns = patterns('',
    (r'^subscriptions/$', 'statistics.views.subscriptions', {}, "seriesly-statistics-subscriptions"),
    (r'^subscribed_shows/$', 'statistics.views.subscribed_shows', {}, "seriesly-statistics-subscribed_shows"),
    (r'^dump_subscriptions/$', 'statistics.views.dump_subscriptions', {}, "seriesly-statistics-dump_subscriptions"),
    (r'^memcache/$', 'statistics.views.memcache', {}, "seriesly-statistics-memcache"),
)
