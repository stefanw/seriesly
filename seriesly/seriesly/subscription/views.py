import datetime
import logging
import re

from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import RequestContext
from django.template.loader import render_to_string
from django.conf import settings

from seriesly.helper import is_post
from seriesly.series.models import Show, Episode

from .forms import (SubscriptionForm, MailSubscriptionForm,
                    XMPPSubscriptionForm, WebHookSubscriptionForm,
                    SubscriptionKeyForm)
from .models import Subscription

WORD = re.compile("^\w+$")


def index(request, form=None, extra_context=None):
    if form is None:
        form = SubscriptionForm()
    context = {"form": form}
    if extra_context is not None:
        context.update(extra_context)
    return render(request, "index.html", context)


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
    sub_settings = {}
    subscription.set_settings(sub_settings)

    try:
        selected_shows = Show.get_by_id(map(int, form.cleaned_data["shows"]))
    except ValueError:
        return index(request, form=form)

    old_shows = []
    if editing:
        old_shows = subscription.get_shows()

    subscription.reset_cache(selected_shows)
    subscription.save()  # stay here, need key for setting shows!

    if editing:
        subscription.set_shows(selected_shows, old_shows=old_shows)
    else:
        subscription.set_shows(selected_shows)

    response = redirect(subscription)
    response.set_cookie("subkey", subkey, max_age=31536000)
    return response


def show(request, subkey, extra_context=None):
    subscription = get_object_or_404(Subscription, subkey=subkey)
    if extra_context is None:
        extra_context = {}

    context_forms = {
        'email': MailSubscriptionForm,
        'xmpp': XMPPSubscriptionForm,
        'webhook': WebHookSubscriptionForm,
        'public_id': SubscriptionKeyForm
    }
    for key, form in context_forms.items():
        form_key = '{}_form'.format(key)
        if form_key not in extra_context:
            val = getattr(subscription, key)
            extra_context[form_key] = MailSubscriptionForm({key: val, "subkey": subkey})

    extra_context.update({
        'sub_settings': subscription.get_settings(),
        'shows': subscription.get_shows(),
        'subscription': subscription
    })

    response = render(request, "subscription.html", extra_context)
    response.set_cookie("subkey", subkey, max_age=31536000)
    return response


def show_public(request, public_id):
    subscription = get_object_or_404(Subscription, public_id=public_id)
    return render_to_response(request, 'subscription_public.html', {
        "shows": subscription.get_shows(),
        "subscription": subscription
    })


def edit(request, subkey):
    subscription = get_object_or_404(Subscription, subkey=subkey)
    if request.method == "GET":
        subscription.get_settings()
        sub_dict = {
            "email": subscription.email,
            "shows": map(lambda x: x.idnr, subscription.get_shows()),
            "subkey": subkey
        }
        form = SubscriptionForm(sub_dict)
        return index(request, form=form, extra_context={"subscription": subscription})
    return redirect(subscription)


@is_post
def edit_public_id(request):
    form = SubscriptionKeyForm(request.POST)
    if not form.is_valid():
        return show(
            request,
            request.POST.get("subkey", ""),
            extra_context={"public_id_form": form}
        )
    subscription = form._subscription
    if subscription.public_id is None:
        subscription.public_id = Subscription.generate_key("public_id")
    else:
        subscription.public_id = None
    subscription.save()
    return HttpResponseRedirect(subscription.get_absolute_url() + "#public-urls")


def feed_rss(request, subkey):
    return feed(request, subkey, template="rss.xml")


def feed_atom(request, subkey, template="atom.xml"):
    subscription = get_object_or_404(Subscription, subkey=subkey)
    now = datetime.datetime.now()
    if subscription.needs_update(subscription.feed_stamp, now):
        subscription.check_beacon_status(now)
        # don't specify encoding for unicode strings!
        subscription.feed_cache = db.Text(_feed(request, subscription, template))
        subscription.feed_stamp = now
        try:
            subscription.save()  # this put is not highly relevant
        except Exception as e:
            logging.warning(e)
    return HttpResponse(subscription.feed_cache, mimetype="application/atom+xml")


def feed(request, subkey, template):
    subscription = get_object_or_404(Subscription, subkey=subkey)
    body = _feed(request, subscription, template)
    mimetype = "application/atom+xml"
    if "rss" in template:
        mimetype = "application/rss+xml"
    return HttpResponse(body, mimetype=mimetype)


def feed_atom_public(request, public_id, template="atom_public.xml"):
    subscription = get_object_or_404(Subscription, public_id=public_id)
    now = datetime.datetime.now()
    if subscription.needs_update(subscription.feed_public_stamp, now):
        subscription.check_beacon_status(now)
        # don't specify encoding for unicode strings!
        subscription.feed_public_cache = db.Text(_feed(request, subscription, template, public=True))
        subscription.feed_public_stamp = now
        try:
            subscription.save()  # this put is not highly relevant
        except Exception as e:
            logging.warning(e)
    return HttpResponse(subscription.feed_public_cache, mimetype="application/atom+xml")


def feed_rss_public(request, public_id, template="rss_public.xml"):
    subscription = get_object_or_404(Subscription, public_id=public_id)
    return HttpResponse(_feed(request, subscription, template, public=True), mimetype="application/rss+xml")


def _feed(request, subscription, template, public=False):
    now = datetime.datetime.now()
    subscription.get_settings()
    subscription.updated = now.strftime('%Y-%m-%dT%H:%M:%SZ')
    subscription.expires = (now + datetime.timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%SZ')
    the_shows = subscription.get_shows()
    wait_time = datetime.timedelta(hours=6)
    episodes = Episode.get_for_shows(the_shows, before=now, order="-date")
    items = []
    for episode in episodes:
        if now > episode.date + wait_time:
            pub_date = episode.date_local
            episode.pub_date = pub_date
            items.append(episode)
    return render(request, template, {
        "subscription": subscription,
        "items": items
    })


def calendar(request, subkey):
    subscription = get_object_or_404(Subscription, subkey=subkey)
    return _calendar(request, subscription)


def calendar_public(request, public_id):
    subscription = get_object_or_404(Subscription, public_id=public_id)
    return _calendar(request, subscription, public=True)


def _calendar(request, subscription, public=False):
    now = datetime.datetime.now()
    if subscription.needs_update(subscription.calendar_stamp, now):
        subscription.check_beacon_status(now)
        subscription.calendar_stamp = now
        # specify encoding for byte strings!
        subscription.calendar_cache = db.Text(subscription.get_icalendar(public), encoding="utf8")
        try:
            subscription.save()  # this put is not highly relevant
        except Exception as e:
            logging.warning(e)
    response = HttpResponse(subscription.calendar_cache, mimetype='text/calendar')
    response['Filename'] = 'seriesly-calendar.ics'  # IE needs this
    response['Content-Disposition'] = 'attachment; filename=seriesly-calendar.ics'
    return response


def guide(request, subkey):
    subscription = get_object_or_404(Subscription, subkey=subkey)
    return _guide(request, subscription)


def guide_public(request, public_id):
    subscription = get_object_or_404(Subscription, public_id=public_id)
    return _guide(request, subscription, template="guide_public.html", public=True)


def _guide(request, subscription, template="guide.html",
           public=False, extra_context=None):
    subscription.is_public = public
    subscription.get_settings()
    now = datetime.datetime.now()
    the_shows = subscription.get_shows()
    episodes = Episode.get_for_shows(the_shows, order="date")
    twentyfour_hours_ago = now - datetime.timedelta(hours=24)
    recently = []
    last_week = []
    upcoming = []
    for episode in episodes:
        if episode.date < twentyfour_hours_ago:
            last_week.append(episode)
        elif episode.date <= now:
            recently.append(episode)
        else:
            upcoming.append(episode)
    context = {
        "subscription": subscription,
        "recently": recently,
        "upcoming": upcoming,
        "last_week": last_week
    }
    if extra_context is not None:
        context.update(extra_context)
    response = render_to_response(template, RequestContext(request, context))
    if not public:
        response.set_cookie("subkey", subscription.subkey)
    try:
        if subscription.check_beacon_status(now):
            subscription.save()  # this put is not highly relevant
    except Exception as e:
        logging.warning(e)
    return response


@is_post
def edit_mail(request):
    form = MailSubscriptionForm(request.POST)
    if not form.is_valid():
        return show(
            request,
            request.POST.get("subkey", ""),
            extra_context={"mail_form": form}
        )
    subscription = form._subscription
    if subscription.email != form.cleaned_data["email"]:
        subscription.activated_mail = False
    subscription.email = form.cleaned_data["email"]
    subscription.last_changed = datetime.datetime.now()
    subscription.save()
    if subscription.email != "" and subscription.activated_mail is False:
        subscription.send_confirmation_mail()
    return redirect(subscription.get_absolute_url() + "#email")


def confirm_mail(request, subkey, confirmkey):
    subscription = get_object_or_404(Subscription, subkey=subkey)
    if subscription.check_confirmation_key(confirmkey):
        if (subscription.activated_mail is False and
                subscription.email != ""):
            subscription.activated_mail = True
            subscription.save()
        return redirect(
            subscription.get_absolute_url() + "#email"
        )
    else:
        raise Http404


def send_confirm_mail(request):
    key = None
    try:
        key = request.POST.get("key", None)
        if key is None:
            raise Http404
        subscription = Subscription.get(key)
        if subscription is None:
            raise Http404
    except Exception as e:
        logging.error(e)
        return HttpResponse("Done (with errors): %s" % key)
    subscription.do_send_confirmation_mail()
    logging.debug("Done sending Confirmation Mail to %s" % subscription.email)
    return HttpResponse("Done: %s" % key)


def email_task(request):
    filter_date = datetime.datetime.now().date() + datetime.timedelta(days=1)
    subscriptions = Subscription.objects.filter(activated_mail=True, next_airtime__lte=filter_date)
    counter = 0
    for sub in subscriptions:
        Subscription.add_email_task(sub.pk)
        counter += 1
    return HttpResponse("Done: added %d" % counter)


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
            subscription.save()
            return HttpResponse("Skipping early.")
        context = subscription.get_message_context()
        if context is None:
            return HttpResponse("Nothing to do.")
        subscription.check_beacon_status(datetime.datetime.now())
        subject = "Seriesly.com - %d new episodes" % len(context["items"])
        body = render_to_string("subscription_mail.txt", RequestContext(request, context))
    except Exception as e:
        logging.error(e)
        return HttpResponse("Done (with errors): %s" % key)
    # let mail sending trigger an error to allow retries
    mail.send_mail(settings.DEFAULT_FROM_EMAIL, subscription.email, subject, body)
    try:
        subscription.save()  # this put is not highly relevant
    except Exception as e:
        logging.warning(e)
    return HttpResponse("Done: %s" % key)


def xmpp_task(request):
    subscriptions = Subscription.objects.filter(activated_xmpp=True)
    counter = 0
    for sub in subscriptions:
        Subscription.add_xmpp_task(sub.pk)
        counter += 1
    return HttpResponse("Done: added %d" % counter)


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
        subscription.check_beacon_status(datetime.datetime.now())
        context = subscription.get_message_context()
        if context is None:
            return HttpResponse("Nothing to do.")
        body = render_to_string("subscription_xmpp.txt", RequestContext(request, context))
    except Exception as e:
        logging.error(e)
        return HttpResponse("Done (with errors): %s" % key)
    status_code = xmpp.send_message(subscription.xmpp, body)
    jid_broken = (status_code == xmpp.INVALID_JID)
    if jid_broken:
        subscription.xmpp = None
        subscription.xmpp_activated = False
    try:
        subscription.save()
    except Exception as e:
        logging.warn(e)
    return HttpResponse("Done: %s" % key)


@is_post
def edit_xmpp(request):
    form = XMPPSubscriptionForm(request.POST)
    if not form.is_valid():
        return show(
            request,
            request.POST.get("subkey", ""),
            extra_context={"xmpp_form": form}
        )
    subscription = form._subscription
    if subscription.xmpp != form.cleaned_data["xmpp"]:
        subscription.activated_xmpp = False
    subscription.xmpp = form.cleaned_data["xmpp"]
    subscription.last_changed = datetime.datetime.now()
    if subscription.xmpp != "" and subscription.activated_xmpp is False:
        try:
            subscription.send_invitation_xmpp()
        except Exception:
            form.errors["xmpp"] = ["Could not send invitation to this XMPP address"]
            return show(
                request,
                request.POST.get("subkey", ""),
                extra_context={"xmpp_form": form}
            )
    subscription.save()
    return HttpResponseRedirect(subscription.get_absolute_url() + "#xmpp")


def incoming_xmpp(request):
    try:
        message = xmpp.Message(request.POST)
    except Exception as e:
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
        subscription.save()
        message.reply("Your Seriesly XMPP Subscription is now activated.")
    elif not subscription.activated_xmpp:
        message.reply("Someone requested this Seriesly Subscription to your XMPP address: %s . Please type 'OK' to confirm." % subscription.get_domain_absolute_url())
    else:
        message.reply("Your Seriesly XMPP Subscription is active. Go to %s to change settings." % subscription.get_domain_absolute_url())
    return HttpResponse()


@is_post
def edit_webhook(request):
    form = WebHookSubscriptionForm(request.POST)
    if not form.is_valid():
        return show(
            request,
            request.POST.get("subkey", ""),
            extra_context={"webhook_form": form}
        )
    subscription = form._subscription
    subscription.webhook = form.cleaned_data["webhook"]
    subscription.last_changed = datetime.datetime.now()
    subscription.save()
    return HttpResponseRedirect(subscription.get_absolute_url() + "#webhook")


def webhook_task(request):
    """BadFilterError: invalid filter: Only one property per query may have inequality filters (<=, >=, <, >).."""
    subscriptions = Subscription.object.filter(webhook__isnull=False)
    counter = 0
    for obj in subscriptions:
        Subscription.add_webhook_task(obj.key())
        counter += 1
    return HttpResponse("Done: added %d" % counter)


@is_post
def run_webhook_test(request, subkey):
    subscription = get_object_or_404(Subscription, subkey=subkey)
    if subscription.webhook is None:
        raise Http404
    Subscription.add_webhook_task(subscription.key())
    return HttpResponse("Task for posting to %s added. Will run in some seconds. Be reminded of The Rules on http://www.seriesly.com/webhook-xml/#the-rules" % subscription.webhook)


@is_post
def post_to_callback(request):
    key = None
    webhook = None
    try:
        key = request.POST.get("key", None)
        if key is None:
            raise Http404
        subscription = Subscription.get(key)
        if subscription is None:
            raise Http404
        subscription.check_beacon_status(datetime.datetime.now())

        context = subscription.get_message_context()
        if context is None:
            return HttpResponse("Nothing to do.")
        body = render_to_string("subscription_webhook.xml", RequestContext(request, context))
        webhook = subscription.webhook
        try:
            subscription.post_to_callback(body)
        except Exception as e:
            subscription.webhook = None
            logging.warn("Webhook failed (%s): %s" % (key, e))

        subscription.save()
    except Exception as e:
        logging.error(e)
        return HttpResponse("Done (with errors): %s" % key)
    logging.debug("Done sending Webhook Callback to %s" % webhook)
    return HttpResponse("Done: %s" % key)


def get_extra_json_context(request):
    callback = request.GET.get("callback", None)
    extra_context = {"callback": None}
    if callback is not None and WORD.match(callback) is not None:
        extra_context = {"callback": callback}
    return extra_context


def get_json(request, subkey):
    subscription = get_object_or_404(Subscription, subkey=subkey)
    response = _guide(request, subscription, template="widget.json",
        extra_context=get_extra_json_context(request))
    response["Content-Type"] = 'application/json'
    return response


def get_json_public(request, public_id):
    subscription = get_object_or_404(Subscription, public_id=public_id)
    response = _guide(request, subscription, template="widget.json",
        public=True, extra_context=get_extra_json_context(request))
    response["Content-Type"] = 'application/json'
    return response


def add_next_airtime_task(request):
    for key in Subscription.all(keys_only=True).filter("activated_mail =", True):
        t = taskqueue.Task(url="/subscription/next-airtime/", params={"key": str(key)})
        t.add(queue_name="webhook-queue")
    return HttpResponse("Done: ")


def set_next_airtime(request):
    key = None
    key = request.POST.get("key", None)
    if key is None:
        raise Http404
    subscription = Subscription.get(key)
    subscription.next_airtime = datetime.date(2010, 1, 1)
    subscription.save()
    return HttpResponse("Done: %s" % key)
