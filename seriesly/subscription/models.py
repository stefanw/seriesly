import random
import hashlib
import hmac
import datetime

from django.db import models
from django.core import mail
from django.core.urlresolvers import reverse
from django.conf import settings
from django.utils.encoding import python_2_unicode_compatible
from django.core.signing import Signer, BadSignature

import vobject

from seriesly.helper.http import post as http_post
from seriesly.series.models import Show, Episode


@python_2_unicode_compatible
class Subscription(models.Model):
    subkey = models.CharField(max_length=255)
    last_visited = models.DateTimeField(null=True)
    last_changed = models.DateTimeField(null=True)
    activated_mail = models.BooleanField(default=False)
    email = models.CharField(max_length=255, blank=True)
    activated_xmpp = models.BooleanField(default=False)
    xmpp = models.CharField(max_length=255, blank=True)
    settings = models.TextField(blank=True)
    webhook = models.CharField(max_length=255, blank=True)
    public_id = models.CharField(max_length=255, blank=True)

    feed_cache = models.TextField(blank=True)
    feed_stamp = models.DateTimeField(null=True, blank=True)
    calendar_cache = models.TextField(blank=True)
    calendar_stamp = models.DateTimeField(null=True, blank=True)

    feed_public_cache = models.TextField(blank=True)
    feed_public_stamp = models.DateTimeField(null=True, blank=True)

    show_cache = models.TextField(blank=True)

    next_airtime = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.subkey

    def get_absolute_url(self):
        return reverse("seriesly-subscription-show", args=(self.subkey,))

    def get_domain_absolute_url(self):
        return settings.DOMAIN_URL + reverse("seriesly-subscription-show", args=(self.subkey,))

    def get_email_signer(self):
        return Signer(salt='emailconfirmation|%s' % self.subkey)

    def check_signed_email(self, value):
        signer = self.get_email_signer()
        try:
            email = signer.unsign(value)
        except BadSignature:
            return False
        return email == self.email

    def get_signed_email(self):
        signer = self.get_email_signer()
        return signer.sign(self.email)

    def send_confirmation_mail(self):
        confirmation_key = self.get_signed_email()
        confirmation_url = settings.DOMAIN_URL + reverse("seriesly-subscription-confirm_mail", args=(self.subkey, confirmation_key))

        sub_url = settings.DOMAIN_URL + reverse("seriesly-subscription-show", args=(self.subkey,))

        subject = "Confirm your seriesly.com email notifications"
        body = """Please confirm your email notifications for your favorite TV-Shows by clicking the link below:

%s

You will only receive further emails when you click the link.
If you did not expect this mail, you should ignore it.
By the way: your Seriesly subscription URL is: %s
    """ % (confirmation_url, sub_url)
        mail.send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [self.email])

    def set_settings(self, d):
        self._cached_settings = d
        l = []
        for k, v in d.items():
            l.append("%s\t%s" % (k, v))
        self.settings = "\n".join(l)

    def get_settings(self):
        if hasattr(self, "_cached_settings"):
            return self._cached_settings
        lines = self.settings.split("\n")
        self._cached_settings = {}
        for l in lines:
            try:
                k, v = l.split("\t", 1)
                self._cached_settings[k] = v.strip()
            except ValueError:
                pass
        # FIXME: This is basically bad:
        for k, v in self._cached_settings.items():
            if v == "False":
                self._cached_settings[k] = False
            elif v == "True":
                self._cached_settings[k] = True
        return self._cached_settings

    @classmethod
    def generate_subkey(cls):
        return cls.generate_key("subkey")

    @classmethod
    def generate_key(cls, field="subkey"):
        CHARS = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        wtf = False
        while wtf is not None:
            key = ''.join(random.choice(CHARS) for _ in range(32))
            try:
                wtf = Subscription.objects.get(**{field: key})
            except Subscription.DoesNotExist:
                wtf = None
        return key

    def get_shows(self):
        show_dict = Show.get_all_dict()
        return [show_dict[show_key] for show_key in self.get_show_cache() if show_key in show_dict]

    def get_shows_old(self):
        show_dict = Show.get_all_dict()
        return [show_dict[str(sub_item.show_id)] for sub_item in self.subscriptionitem_set if str(sub_item.show_id) in show_dict]

    def get_show_cache(self):
        if self.show_cache is None or not len(self.show_cache):
            self.set_show_cache([str(sub_item.show_id) for sub_item in self.subscriptionitem_set])
            self.save()
        return self.show_cache.split("|")

    def set_show_cache(self, show_keys):
        self.show_cache = '|'.join(show_keys)

    def set_shows(self, shows, old_shows=None):
        changes = False
        if old_shows is None:
            old_shows = []
        old_show_ids = set(show.pk for show in old_shows)
        show_ids = set(show.pk for show in shows)
        for show in shows:
            if show.pk not in old_show_ids:
                s = SubscriptionItem(subscription=self, show=show)
                s.save()
                changes = True
        for old_show in old_shows:
            if old_show.pk not in show_ids:
                num, _ = SubscriptionItem.objects.filter(
                        subscription=self, show=old_show).delete()
                if num:
                    changes = True
        return changes

    def reset_cache(self, show_list):
        self.set_show_cache([str(show.pk) for show in show_list])
        # don't know next airtime
        self.next_airtime = datetime.date(2010, 1, 1)
        self.feed_stamp = None
        self.calendar_stamp = None
        self.feed_public_stamp = None

    @classmethod
    def add_email_task(cls, key):
        return cls.add_task('seriesly-subscription-mail', "mail-queue", key)

    @classmethod
    def add_xmpp_task(cls, key):
        return cls.add_task('seriesly-subscription-xmpp', "xmpp-queue", key)

    @classmethod
    def add_webhook_task(cls, key):
        return cls.add_task('seriesly-subscription-webhook', "webhook-queue", key)

    @classmethod
    def add_task(cls, url_name, queue_name, key):
        t = taskqueue.Task(url=reverse(url_name), params={"key": str(key)})
        t.add(queue_name=queue_name)
        return t

    def post_to_callback(self, body):
        response = http_post(self.webhook, body)
        if str(response.status_code)[0] != "2":
            raise IOError("Return status %s" % response.status_code)
        if len(response.content) > 0:
            raise ValueError("Returned content, is defined illegal")

    def get_message_context(self):
        the_shows = self.get_shows()
        now = datetime.datetime.now()
        twentyfour_hours_ago = now - datetime.timedelta(hours=24)
        episodes = Episode.get_for_shows(the_shows, after=twentyfour_hours_ago, order="date")
        if not len(episodes):
            return None
        context = {"subscription": self, "items": []}
        for episode in episodes:
            if episode.date > now:
                self.next_airtime = episode.date.date()
                break
            context["items"].append(episode)
        if not context["items"]:
            return None
        return context

    def get_icalendar(self, public):
        """Nice hints from here: http://blog.thescoop.org/archives/2007/07/31/django-ical-and-vobject/"""
        the_shows = self.get_shows()
        # two_weeks_ago = now - datetime.timedelta(days=7)
        # five_hours = datetime.timedelta(hours=5)
        # sub_settings = self.get_settings()
        self.get_settings()
        episodes = Episode.get_for_shows(the_shows, order="date")
        cal = vobject.iCalendar()
        cal.add('method').value = 'PUBLISH'  # IE/Outlook needs this
        for episode in episodes:
            episode.create_event_details(cal)
        return cal.serialize()


@python_2_unicode_compatible
class SubscriptionItem(models.Model):
    subscription = models.ForeignKey(Subscription)
    show = models.ForeignKey(Show)

    def __str__(self):
        return '%s -> %s' % (self.subscription, self.show)
