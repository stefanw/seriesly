from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin

urlpatterns = patterns('',
    (r'^update/$', 'releases.views.update_releases', {}, "seriesly-releases-update"),
    (r'^update/(\w+)/$', 'releases.views.update_one', {}, "seriesly-releases-update_one"),
    (r'^update_provider/$', 'releases.views.update_provider', {}, "seriesly-releases-update_provider"),
    (r'^go/(\d+)/$', 'releases.views.redirect_to_release', {}, "seriesly-releases-redirect"),
)
