import datetime
import logging

from google.appengine.api import xmpp
from google.appengine.api import mail
from google.appengine.ext import db

from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import RequestContext
from django.template.loader import render_to_string
from django.conf import settings

from helper import is_post
from series.models import Show, Episode
from subscription.forms import SubscriptionForm, MailSubscriptionForm, \
    XMPPSubscriptionForm, WebHookSubscriptionForm, SubscriptionKeyForm
from subscription.models import Subscription
from releases.models import Release

def index(request, form=None, extra_context=None):
    if form is None:
        form = SubscriptionForm()
    context = {"form" : form}
    if extra_context is not None:
        context.update(extra_context)
    return render_to_response("index.html", RequestContext(request, context))
    
@is_post
def subscribe(request):
    form = SubscriptionForm(request.POST)
    if not form.is_valid():
        return index(request, form=form)
    editing = False
    if form.cleaned_data["subkey"] == "":
        subkey = Subscription.generate_subkey()
        subscription = Subscription(last_changed=datetime.datetime.now(), subkey=subkey)
    else:
        editing = True
        subkey = form.cleaned_data["subkey"]
        subscription = form._subscription
    sub_settings = {"quality": form.cleaned_data["quality"],
                "torrent": str(form.cleaned_data["torrent"]),
                "stream" : str(form.cleaned_data["stream"])
            }
    subscription.set_settings(sub_settings)
    
    try:
        selected_shows = Show.get_by_id(map(int, form.cleaned_data["shows"]))
    except ValueError:
        return index(request, form=form)
    subscription.put()
    
    if editing:
        subscription.set_shows(selected_shows, old_shows=subscription.get_shows())
    else:
        subscription.set_shows(selected_shows)
    response = HttpResponseRedirect(subscription.get_absolute_url())
    response.set_cookie("subkey", subkey, max_age=31536000)
    return response
    
def show(request, subkey, extra_context=None):
    subscription = Subscription.all().filter("subkey =", subkey).get()
    if subscription is None:
        raise Http404
    if extra_context is None:
        extra_context = {}
    if "mail_form" in extra_context:
        subscription.mail_form = extra_context["mail_form"]
    else:
        subscription.mail_form = MailSubscriptionForm({"email": subscription.email, "subkey": subkey})
    if "xmpp_form" in extra_context:
        subscription.xmpp_form = extra_context["xmpp_form"]
    else:
        subscription.xmpp_form = XMPPSubscriptionForm({"xmpp": subscription.xmpp, "subkey": subkey})
    if "webhook_form" in extra_context:
        subscription.webhook_form = extra_context["webhook_form"]
    else:
        subscription.webhook_form = WebHookSubscriptionForm({"webhook": subscription.webhook, "subkey": subkey})
    if "public_id_form" in extra_context:
        subscription.public_id_form = extra_context["public_id_form"]
    else:
        subscription.public_id_form = SubscriptionKeyForm({"subkey": subkey})
    subscription.sub_settings = subscription.get_settings()
    response = render_to_response("subscription.html", RequestContext(request, {"subscription":subscription}))
    response.set_cookie("subkey", subkey, max_age=31536000)
    return response
    
def show_public(request, public_id):
    subscription = Subscription.all().filter("public_id =", public_id).get()
    if subscription is None:
        raise Http404        
    response = render_to_response("subscription_public.html", RequestContext(request, {"shows":subscription.get_shows(), "subscription": subscription}))
    return response

def edit(request, subkey):
    subscription = Subscription.all().filter("subkey =", subkey).get()
    if subscription is None:
        raise Http404
    if request.method == "GET":
        sub_settings = subscription.get_settings()
        sub_dict = {"email": subscription.email, 
                    "quality": sub_settings["quality"],
                    "torrent": sub_settings["torrent"],
                    "stream": sub_settings["stream"],
                    "shows": map(lambda x: x.idnr, subscription.get_shows()),
                    "subkey": subkey}
        form = SubscriptionForm(sub_dict)
        return index(request, form=form, extra_context={"subscription": subscription})
    return HttpResponseRedirect(subscription.get_absolute_url())

@is_post
def edit_public_id(request):
    form = SubscriptionKeyForm(request.POST)
    if not form.is_valid():
        return show(request, request.POST.get("subkey", ""), extra_context={"public_id_form":form})
    subscription = form._subscription
    if subscription.public_id is None:
        subscription.public_id = Subscription.generate_key("public_id")
    else:
        subscription.public_id = None
    subscription.put()
    return HttpResponseRedirect(subscription.get_absolute_url() + "#subscription-public-urls")

def feed_rss(request, subkey):
    return feed(request, subkey, template="rss.xml")
    
def feed_atom(request, subkey, template="atom.xml"):
    subscription = Subscription.all().filter("subkey =", subkey).get()
    if subscription is None:
        raise Http404
    now = datetime.datetime.now()
    cache_time = datetime.timedelta(hours=1)
    if subscription.feed_stamp is None or (now - subscription.feed_stamp) > cache_time:
        subscription.check_beacon_status(now)
        # don't specify encoding for unicode strings!
        subscription.feed_cache = db.Text(_feed(request, subscription, template)) 
        subscription.feed_stamp = now
        subscription.put()
    return HttpResponse(subscription.feed_cache, mimetype="application/atom+xml")
    
def feed(request, subkey, template):
    subscription = Subscription.all().filter("subkey =", subkey).get()
    if subscription is None:
        raise Http404
    body = _feed(request, subscription, template)
    mimetype = "application/atom+xml"
    if "rss" in template:
        mimetype = "application/rss+xml"
    return HttpResponse(body, mimetype=mimetype)

    
def feed_atom_public(request, public_id, template="atom_public.xml"):
    subscription = Subscription.all().filter("public_id =", public_id).get()
    if subscription is None:
        raise Http404
    now = datetime.datetime.now()
    cache_time = datetime.timedelta(hours=3)
    if subscription.feed_public_stamp is None or (now - subscription.feed_public_stamp) > cache_time:
        subscription.check_beacon_status(now)
        # don't specify encoding for unicode strings!
        subscription.feed_public_cache = db.Text(_feed(request, subscription, template, public=True)) 
        subscription.feed_public_stamp = now
        subscription.put()
    return HttpResponse(subscription.feed_public_cache, mimetype="application/atom+xml")

def feed_rss_public(request, public_id, template="rss_public.xml"):
    subscription = Subscription.all().filter("public_id =", public_id).get()
    if subscription is None:
        raise Http404
    return HttpResponse(_feed(request, subscription, template, public=True), mimetype="application/rss+xml")

def _feed(request, subscription, template, public=False):
    now = datetime.datetime.now()
    sub_settings = subscription.get_settings()
    subscription.updated = now.strftime('%Y-%m-%dT%H:%M:%SZ')
    subscription.expires = (now + datetime.timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%SZ')
    the_shows = subscription.get_shows()
    wait_time = datetime.timedelta(hours=6)
    episodes = Episode.get_for_shows(the_shows, before=now, order="-date")
    items = []
    for episode in episodes:
        releases = []
        if subscription.want_releases:
            releases = Release.filter(episode.releases, sub_settings)
        if not subscription.want_releases or releases or now > episode.date + wait_time:
            torrenturl = False
            torrentlen = 0
            pub_date = episode.date
            if len(releases) > 0:
                # Some smart ranking needed here
                torrenturl = releases[0].url
                torrentlen = releases[0].torrentlen
                pub_date = releases[0].pub_date
            episode.torrenturl = torrenturl
            episode.torrentlen = torrentlen
            episode.pub_date = pub_date
            episode.releases = releases
            items.append(episode)
    return render_to_string(template, RequestContext(request, {"subscription":subscription, "items": items}))
    
def calendar(request, subkey):
    subscription = Subscription.all().filter("subkey =", subkey).get()
    if subscription is None:
        raise Http404
    return _calendar(request, subscription)

def calendar_public(request, public_id):
    subscription = Subscription.all().filter("public_id =", public_id).get()
    if subscription is None:
        raise Http404
    return _calendar(request, subscription, public=True)
    
def _calendar(request, subscription, public=False):
    now = datetime.datetime.now()
    cache_time = datetime.timedelta(hours=1)
    if subscription.calendar_stamp is None or (now - subscription.calendar_stamp) > cache_time:
        try:
            subscription.check_beacon_status(now)
            subscription.calendar_stamp = now
            # specify encoding for byte strings!
            subscription.calendar_cache = db.Text(subscription.get_icalendar(public), encoding="utf8")
            subscription.put()
        except Exception, e:
            logging.error(e)
            subscription.calendar_cache = ""
    response = HttpResponse(subscription.calendar_cache, mimetype='text/calendar')
    response['Filename'] = 'seriesly-calendar.ics'  # IE needs this
    response['Content-Disposition'] = 'attachment; filename=seriesly-calendar.ics'
    return response


def guide(request, subkey):
    subscription = Subscription.all().filter("subkey =", subkey).get()
    if subscription is None:
        raise Http404
    return _guide(request, subscription)
    
def guide_public(request, public_id):
    subscription = Subscription.all().filter("public_id =", public_id).get()
    if subscription is None:
        raise Http404
    return _guide(request, subscription, template="guide_public.html", public=True)
        
def _guide(request, subscription, template="guide.html", public=False):
    subscription.is_public = public
    sub_settings = subscription.get_settings()
    now = datetime.datetime.now()
    if subscription.check_beacon_status(now):
        subscription.put()
    the_shows = subscription.get_shows()
    episodes = Episode.get_for_shows(the_shows, order="date")
    twentyfour_hours_ago = now - datetime.timedelta(hours=24)
    recently = []
    last_week = []
    upcoming = []
    for episode in episodes:
        if subscription.want_releases:
            if episode.date < now:
                releases = Release.filter(episode.releases, sub_settings)
            else:
                releases = []
            episode.releases = releases
        if episode.date < twentyfour_hours_ago:
            last_week.append(episode)
        elif episode.date <= now:
            recently.append(episode)
        else:
            upcoming.append(episode)
    response = render_to_response(template, RequestContext(request, {"subscription":subscription, 
                                "recently": recently, 
                                "upcoming": upcoming, 
                                "last_week": last_week
                            }))
    if not public:
        response.set_cookie("subkey", subscription.subkey)
    return response

@is_post
def edit_mail(request):
    form = MailSubscriptionForm(request.POST)
    if not form.is_valid():
        return show(request, request.POST.get("subkey", ""), extra_context={"mail_form":form})
    subscription = form._subscription
    if subscription.email != form.cleaned_data["email"]:
        subscription.activated_mail = False
    subscription.email = form.cleaned_data["email"]
    subscription.last_changed = datetime.datetime.now()
    subscription.put()
    if subscription.email != "" and subscription.activated_mail == False:
        subscription.send_confirmation_mail()
    return HttpResponseRedirect(subscription.get_absolute_url() + "#email-subscription")
    
def confirm_mail(request, subkey, confirmkey):
    subscription = Subscription.all().filter("subkey =", subkey).get()
    if subscription is None:
        raise Http404
    if subscription.check_confirmation_key(confirmkey):
        if subscription.activated_mail == False and subscription.email != "":
            subscription.activated_mail = True
            subscription.put()
        return HttpResponseRedirect(subscription.get_absolute_url() + "#email-subscription")
    else:
        raise Http404

def email_task(request):
    subscriptions = Subscription.all().filter("activated_mail =", True)
    counter = 0
    for s in subscriptions:
        s.add_email_task()
        counter += 1
    return HttpResponse("Done: \n%s, %d" % (subscriptions, counter))

@is_post
def send_mail(request):
    key = None
    try:
        key = request.POST.get("key", None)
        if key is None:
            raise Http404
        subscription = Subscription.get(key)
        if subscription is None:
            raise Http404
        
        # quick fix for running tasks
        if subscription.email == "":
            subscription.activated_mail = False
            subscription.put()
            return HttpResponse("Skipping early.")
        if subscription.check_beacon_status(datetime.datetime.now()):
            subscription.put()
        
        context = subscription.get_message_context()
        if context is None:
            return HttpResponse("Nothing to do.")
        subject = "Seriesly.com - %d new episodes" % len(context["items"])
        body = render_to_string("subscription_mail.txt", RequestContext(request, context))
    except Exception, e:
        logging.error(e)
        return HttpResponse("Done (with errors): %s" % key)
    # let mail sending trigger an error to allow retries
    mail.send_mail(settings.DEFAULT_FROM_EMAIL, subscription.email, subject, body)
    logging.debug("Done sending Mail to %s" % subscription.email)
    return HttpResponse("Done: %s" % key)

def xmpp_task(request):
    subscriptions = Subscription.all().filter("activated_xmpp =", True)
    counter = 0
    for s in subscriptions:
        s.add_xmpp_task()
        counter += 1
    return HttpResponse("Done: \n%s, %d" % (subscriptions, counter))

@is_post
def send_xmpp(request):
    key = None
    try:
        key = request.POST.get("key", None)
        if key is None:
            raise Http404
        subscription = Subscription.get(key)
        if subscription is None:
            raise Http404
        needs_put = False
        if subscription.check_beacon_status(datetime.datetime.now()):
            needs_put = True
        context = subscription.get_message_context()
        if context is None:
            return HttpResponse("Nothing to do.")
        body = render_to_string("subscription_xmpp.txt", RequestContext(request, context))
        status_code = xmpp.send_message(subscription.xmpp, body)
        jid_broken = (status_code == xmpp.INVALID_JID)
        if jid_broken:
            subscription.xmpp = None
            subscription.xmpp_activated = False
            needs_put = True
        if needs_put:
            subscription.put()
    except Exception, e:
        logging.error(e)
        return HttpResponse("Done (with errors): %s" % key)
    logging.debug("Done sending XMPP to %s" % subscription.xmpp)
    return HttpResponse("Done: %s" % key)
    
@is_post
def edit_xmpp(request):
    form = XMPPSubscriptionForm(request.POST)
    if not form.is_valid():
        return show(request, request.POST.get("subkey", ""), extra_context={"xmpp_form":form})
    subscription = form._subscription
    if subscription.xmpp != form.cleaned_data["xmpp"]:
        subscription.activated_xmpp = False
    subscription.xmpp = form.cleaned_data["xmpp"]
    subscription.last_changed = datetime.datetime.now()
    subscription.put()
    if subscription.xmpp != "" and subscription.activated_xmpp == False:
        subscription.send_invitation_xmpp()
    return HttpResponseRedirect(subscription.get_absolute_url() + "#xmpp-subscription")
    
def incoming_xmpp(request):
    try:
        message = xmpp.Message(request.POST)
    except Exception, e:
        logging.warn("Failed to parse XMPP Message: %s" % e)
        return HttpResponse()
    sender = message.sender.split("/")[0]
    subscription = Subscription.all().filter("xmpp =", sender).get()
    if subscription is None:
        message.reply("I don't know you. Please create a Seriesly subscription at http://www.seriesly.com")
        logging.warn("Sender not found: %s" % sender)
        return HttpResponse()
    if not subscription.activated_xmpp and message.body == "OK":
        subscription.activated_xmpp = True
        subscription.put()
        message.reply("Your Seriesly XMPP Subscription is now activated.")
    elif not subscription.activated_xmpp:
        message.reply("Someone requested this Seriesly Subscription to your XMPP address: %s . Please type 'OK' to confirm." % subscription.get_domain_absolute_url())
    else:
        message.reply("Your Seriesly XMPP Subscription is active. Go to %s to change settings."  % subscription.get_domain_absolute_url())
    return HttpResponse()

@is_post
def edit_webhook(request):
    form = WebHookSubscriptionForm(request.POST)
    if not form.is_valid():
        return show(request, request.POST.get("subkey", ""), extra_context={"webhook_form":form})
    subscription = form._subscription
    subscription.webhook = form.cleaned_data["webhook"]
    subscription.last_changed = datetime.datetime.now()
    subscription.put()
    return HttpResponseRedirect(subscription.get_absolute_url() + "#webhook-subscription")

def webhook_task(request):
    subscriptions = Subscription.all().filter("webhook !=", None)
    counter = 0
    for s in subscriptions:
        s.add_webhook_task()
        counter += 1
    return HttpResponse("Done: \n%d" % counter)

@is_post
def post_to_callback(request):
    key = None
    try:
        key = request.POST.get("key", None)
        if key is None:
            raise Http404
        subscription = Subscription.get(key)
        if subscription is None:
            raise Http404
        needs_put = False

        if subscription.check_beacon_status(datetime.datetime.now()):
            needs_put = True
            
        context = subscription.get_message_context()
        if context is None:
            return HttpResponse("Nothing to do.")
        body = render_to_string("subscription_webhook.xml", RequestContext(request, context))
        try:
            subscription.post_to_callback(body)
        except Exception, e:
            subscription.webhook = None
            needs_put = True
            logging.warn("Webhook failed (%s): %s" % (key, e))
            
        if needs_put:
            subscription.put()
    except Exception, e:
        logging.error(e)
        return HttpResponse("Done (with errors): %s" % key)
    logging.debug("Done sending Webhook Callback to %s" % subscription.xmpp)
    return HttpResponse("Done: %s" % key)