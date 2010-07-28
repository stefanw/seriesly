import random
import hashlib
import hmac
import logging
import datetime

from google.appengine.ext import db
from google.appengine.api import mail
from google.appengine.api import xmpp
from google.appengine.api.labs import taskqueue

from django.core.urlresolvers import reverse
from django.conf import settings

from helper.http import post as http_post

from releases.models import Release
from series.models import Show, Episode

class Subscription(db.Model):
    subkey =        db.StringProperty()
    last_visited =  db.DateTimeProperty()
    last_changed =  db.DateTimeProperty()
    activated_mail = db.BooleanProperty(default=False)
    email =          db.StringProperty()
    activated_xmpp = db.BooleanProperty(default=False)
    xmpp =          db.StringProperty()
    settings =      db.TextProperty()
    webhook =       db.StringProperty()
    
    BEACON_TIME = datetime.timedelta(days=30)
    
    @classmethod
    def kind(cls):
        return "subscription_subscription"
    
    def get_absolute_url(self):
        return reverse("seriesly-subscription-show", args=(self.subkey,))
        
    def get_domain_absolute_url(self):
        return settings.DOMAIN_URL + reverse("seriesly-subscription-show", args=(self.subkey,))

    def check_beacon_status(self, time):
        if self.last_visited is None or time - self.last_visited > self.BEACON_TIME:
            self.last_visited = time
            return True
        return False
    
    def check_confirmation_key(self, confirmkey):
        shouldbe = hmac.new(settings.SECRET_KEY, self.subkey, digestmod=hashlib.sha1).hexdigest()
        logging.debug("shouldbe: "+ shouldbe)
        if confirmkey == shouldbe:
            return True
        return False
        
    def send_confirmation_mail(self):
        confirmation_key = hmac.new(settings.SECRET_KEY, self.subkey, digestmod=hashlib.sha1).hexdigest()
        confirmation_url = settings.DOMAIN_URL + reverse("seriesly-subscription-confirm_mail", args=(self.subkey, confirmation_key))
        sub_url = settings.DOMAIN_URL + reverse("seriesly-subscription-show", args=(self.subkey,))
        subject = "Confirm your seriesly.com email notifications"
        body = """Please confirm your email notifications for your favorite TV-Shows from seriesly.com by clicking the link below:

%s

You will only receive further emails from seriesly.com when you click the link.
If you did not expect this mail, you should ignore it.
By the way: your Seriesly subscription URL is: %s
""" % (confirmation_url, sub_url)
        mail.send_mail(settings.DEFAULT_FROM_EMAIL, self.email, subject, body)
        
    def send_invitation_xmpp(self):
        xmpp.send_invite(self.xmpp)
    
    def set_settings(self, d):
        self._cached_settings = d
        l = []
        for k, v in d.items():
            l.append("%s\t%s" % (k,v))
        self.settings = "\n".join(l)
    
    def get_settings(self):
        if hasattr(self, "_cached_settings"):
            return self._cached_settings
        lines = self.settings.split("\n")
        self._cached_settings = {}
        for l in lines:
            k,v = l.split("\t", 1)
            self._cached_settings[k] = v.strip()
        # This is basically bad:
        for k,v in self._cached_settings.items():
            if v == "False":
                self._cached_settings[k] = False
            elif v == "True":
                self._cached_settings[k] = True
        return self._cached_settings
    
    @property
    def want_releases(self):
        return self.get_settings()["stream"] or self.get_settings()["torrent"]
    
    @classmethod
    def generate_subkey(cls):
        CHARS = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        wtf = False
        while wtf is not None:
            key = ""
            for i in range(32):
                key += random.choice(CHARS)
            wtf = Subscription.all().filter("subkey =", key).get()
        return key
        
    def get_shows(self):
        show_dict = Show.get_all_dict()
        return [show_dict[str(sub_item._show)] for sub_item in self.subscriptionitem_set if str(sub_item._show) in show_dict]
        
    def set_shows(self, shows, old_shows=None):
        if old_shows is None:
            old_shows = []
        old_show_ids = [show.key() for show in old_shows]
        show_ids = [show.key() for show in shows]
        for show in shows:
            if not show.key() in old_show_ids:
                s = SubscriptionItem(subscription=self, show=show)
                s.put()
        for old_show in old_shows:
            if not old_show.key() in show_ids:
                s = SubscriptionItem.all().filter("subscription =",self).filter("show =", old_show).get()
                s.delete()
                
    def add_email_task(self):
        return self.add_task('seriesly-subscription-mail', "mail-queue")

    def add_xmpp_task(self):
        return self.add_task('seriesly-subscription-xmpp', "xmpp-queue")

    def add_webhook_task(self):
        return self.add_task('seriesly-subscription-webhook', "webhook-queue")

    def add_task(self, url_name, queue_name):
        t = taskqueue.Task(url=reverse(url_name), params={"key": str(self.key())})
        t.add(queue_name=queue_name)
        return t
        
    def post_to_callback(self, body):
        response = http_post(self.webhook, body)
        if str(response.status_code)[0] != "2":
            raise IOError, "Return status %s" % response.status_code
        if len(response.content) > 0:
            raise ValueError, "Returned content, is defined illegal"
        
    def get_message_context(self):
        the_shows = self.get_shows()
        now = datetime.datetime.now()
        twentyfour_hours_ago = now - datetime.timedelta(hours=24)
        episodes = Episode.get_for_shows(the_shows, before=now, after=twentyfour_hours_ago, order="date")
        logging.debug(episodes)
        if not len(episodes):
            return None
        context = {"subscription": self, "items": []}
        for episode in episodes:
            episode.releases = []
            if self.want_releases:
                episode.releases = Release.filter(episode.releases, self.get_settings())
            context["items"].append(episode)
        return context
        

class SubscriptionItem(db.Model):
    subscription =  db.ReferenceProperty(Subscription)
    show =  db.ReferenceProperty(Show)

    @classmethod
    def kind(cls):
        return "subscription_subscriptionitem"