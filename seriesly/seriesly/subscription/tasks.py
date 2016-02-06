import datetime
import logging

from django.conf import settings
from django.core import mail
from django.template.loader import render_to_string

from .models import Subscription


def email_task(request):
    filter_date = datetime.datetime.now().date() + datetime.timedelta(days=1)
    subscriptions = Subscription.objects.filter(activated_mail=True, next_airtime__lte=filter_date)
    counter = 0
    for sub in subscriptions:
        Subscription.add_email_task(sub.pk)
        counter += 1
    return counter


def send_mail(key):
    key = None
    try:
        if key is None:
            return None
        subscription = Subscription.objects.get(subkey=key)
        if subscription is None:
            return None

        # quick fix for running tasks
        if subscription.email == "":
            subscription.activated_mail = False
            subscription.save()
            return None
        context = subscription.get_message_context()
        if context is None:
            return None
        subscription.check_beacon_status(datetime.datetime.now())
        subject = "Seriesly.com - %d new episodes" % len(context["items"])
        body = render_to_string("subscription_mail.txt", context)
    except Exception as e:
        logging.error(e)
        return None
    # let mail sending trigger an error to allow retries
    mail.send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [subscription.email])
    try:
        subscription.save()
    except Exception as e:
        logging.warning(e)
    return key


def webhook_task():
    """BadFilterError: invalid filter: Only one property per query may have inequality filters (<=, >=, <, >).."""
    subscriptions = Subscription.object.filter(webhook__isnull=False)
    counter = 0
    for obj in subscriptions:
        Subscription.add_webhook_task(obj.key())
        counter += 1
    return counter


def post_to_callback(key):
    key = None
    webhook = None
    try:
        if key is None:
            return None
        subscription = Subscription.objects.get(subkey=key)
        if subscription is None:
            return None
        subscription.check_beacon_status(datetime.datetime.now())

        context = subscription.get_message_context()
        if context is None:
            return None
        body = render_to_string("subscription_webhook.xml", context)
        webhook = subscription.webhook
        try:
            subscription.post_to_callback(body)
        except Exception as e:
            subscription.webhook = None
            logging.warn("Webhook failed (%s): %s" % (key, e))

        subscription.save()
    except Exception as e:
        logging.error(e)
        return None
    logging.debug("Done sending Webhook Callback to %s" % webhook)
    return key
