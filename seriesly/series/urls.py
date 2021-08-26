from django.conf.urls import url

from .views import update, update_show, clear_cache, redirect_to_front

urlpatterns = [
    url(r"^update/$", update, name="seriesly-shows-update"),
    url(r"^update/show/$", update_show, name="seriesly-shows-update_show"),
    url(r"^clear/cache/$", clear_cache, name="seriesly-shows-clear_cache"),
    url(r"^episode/([0-9]+)", redirect_to_front, name="seriesly-shows-episode"),
]
