from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^edit/mail/$', 'subscription.views.edit_mail', {}, 'seriesly-subscription-edit_mail'),
    (r'^mail-task/$', 'subscription.views.email_task', {}, "seriesly-subscription-email_task"),
    (r'^confirmmail/$', 'subscription.views.send_confirm_mail', {}, "seriesly-subscription-send_confirm_mail"),
    (r'^mail/$', 'subscription.views.send_mail', {}, "seriesly-subscription-mail"),
    
    (r'^edit/xmpp/$', 'subscription.views.edit_xmpp', {}, 'seriesly-subscription-edit_xmpp'),
    (r'^xmpp-task/$', 'subscription.views.xmpp_task', {}, "seriesly-subscription-xmpp_task"),
    (r'^xmpp/$', 'subscription.views.send_xmpp', {}, "seriesly-subscription-xmpp"),

    (r'^edit/webhook/$', 'subscription.views.edit_webhook', {}, 'seriesly-subscription-edit_webhook'),
    (r'^webhook-task/$', 'subscription.views.webhook_task', {}, "seriesly-subscription-webhook_task"),
    (r'^webhook/$', 'subscription.views.post_to_callback', {}, "seriesly-subscription-webhook"),
    
    (r'^toggle/public-urls$', 'subscription.views.edit_public_id', {}, "seriesly-subscription-edit_public_id"),
)
