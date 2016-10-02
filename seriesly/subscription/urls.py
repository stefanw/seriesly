from django.conf.urls import url

from .views import edit_mail, edit_webhook, edit_public_id


urlpatterns = [
    url(r'^edit/mail/$', edit_mail, name='seriesly-subscription-edit_mail'),

    url(r'^edit/webhook/$', edit_webhook, name='seriesly-subscription-edit_webhook'),

    url(r'^toggle/public-urls/$', edit_public_id,
                name='seriesly-subscription-edit_public_id'),

]
