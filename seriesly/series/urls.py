from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin

urlpatterns = patterns('',
    (r'^import/$', 'series.views.import_show_task', {}, "seriesly-shows-import"),
    (r'^import_show/$', 'series.views.import_shows', {}, "seriesly-shows-import_show"),
    (r'^update/$', 'series.views.update', {}, "seriesly-shows-update"),
    (r'^update/show/$', 'series.views.update_show', {}, "seriesly-shows-update_show"),
    (r'^clear/cache/$', 'series.views.clear_cache', {}, "seriesly-shows-clear_cache"),
    (r'^episode/([0-9]+)', 'series.views.redirect_to_front', {}, "seriesly-shows-episode"),
#    (r'^update/(?P<seriesid>\d)?/?$', 'series.views.update'),
)
