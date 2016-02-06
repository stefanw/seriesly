from django.conf.urls import url

from .views import (edit_mail, send_confirm_mail
    # edit_xmpp, xmpp_task, send_xmpp,
    edit_webhook, post_to_callback,
    edit_public_id,
)

urlpatterns = [
    url(r'^edit/mail/$', edit_mail, name='seriesly-subscription-edit_mail'),
    # url(r'^mail-task/$', email_task, name='seriesly-subscription-email_task'),
    url(r'^confirmmail/$', send_confirm_mail, name='seriesly-subscription-send_confirm_mail'),
    # url(r'^mail/$', send_mail, name='seriesly-subscription-mail'),

    # url(r'^edit/xmpp/$', edit_xmpp, name='seriesly-subscription-edit_xmpp'),
    # url(r'^xmpp-task/$', xmpp_task, name='seriesly-subscription-xmpp_task'),
    # url(r'^xmpp/$', send_xmpp, name='seriesly-subscription-xmpp'),

    url(r'^edit/webhook/$', edit_webhook, name='seriesly-subscription-edit_webhook'),
    # url(r'^webhook-task/$', webhook_task, name='seriesly-subscription-webhook_task'),
    url(r'^webhook/$', post_to_callback, name='seriesly-subscription-webhook'),

    url(r'^toggle/public-urls$', edit_public_id,
                name='seriesly-subscription-edit_public_id'),

]
