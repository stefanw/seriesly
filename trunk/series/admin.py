from django.contrib import admin
from seriesly.series.models import Serie, Season, Episode

admin.site.register(Serie)
admin.site.register(Season)
admin.site.register(Episode)