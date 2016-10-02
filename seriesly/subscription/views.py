import logging
from datetime import timedelta
import re

from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.utils import timezone

from seriesly.helper import is_post
from seriesly.series.models import Show, Episode

from .forms import (SubscriptionForm, MailSubscriptionForm,
                    WebHookSubscriptionForm,
                    SubscriptionKeyForm)
from .models import Subscription
from .tasks import send_confirmation_mail_task

WORD = re.compile("^\w+$")


def index(request, form=None, extra_context=None):
    if form is None:
        form = SubscriptionForm()
    context = {"form": form}
    if extra_context is not None:
        context.update(extra_context)
    return render(request, "subscription/index.html", context)


@is_post
def subscribe(request):
    form = SubscriptionForm(request.POST)
    if not form.is_valid():
        return index(request, form=form)
    editing = False
    if form.cleaned_data["subkey"] == "":
        subkey = Subscription.generate_subkey()
        subscription = Subscription(last_changed=timezone.now(), subkey=subkey)
    else:
        editing = True
        subkey = form.cleaned_data["subkey"]
        subscription = form._subscription
    sub_settings = {}
    subscription.set_settings(sub_settings)

    try:
        selected_shows = Show.objects.filter(pk__in=map(int, form.cleaned_data["shows"]))
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
        'webhook': WebHookSubscriptionForm,
        'public_id': SubscriptionKeyForm
    }
    for key, form_class in context_forms.items():
        form_key = '{}_form'.format(key)
        if form_key not in extra_context:
            val = getattr(subscription, key)
            extra_context[form_key] = form_class(initial={key: val, "subkey": subkey})

    extra_context.update({
        'sub_settings': subscription.get_settings(),
        'shows': subscription.get_shows(),
        'subscription': subscription
    })

    response = render(request, "subscription/subscription.html", extra_context)
    response.set_cookie("subkey", subkey, max_age=31536000)

    return response


def show_public(request, public_id):
    subscription = get_object_or_404(Subscription, public_id=public_id)
    return render(request, 'subscription/subscription_public.html', {
        "shows": subscription.get_shows(),
        "subscription": subscription
    })


def edit(request, subkey):
    subscription = get_object_or_404(Subscription, subkey=subkey)
    if request.method == "GET":
        subscription.get_settings()
        sub_dict = {
            "email": subscription.email,
            "shows": map(lambda x: x.pk, subscription.get_shows()),
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
    return feed(request, subkey, template="subscription/rss.xml")


def feed_atom(request, subkey, template="subscription/atom.xml"):
    return feed(request, subkey, template=template)


def feed(request, subkey, template):
    subscription = get_object_or_404(Subscription, subkey=subkey)
    mimetype = "application/atom+xml"
    if "rss" in template:
        mimetype = "application/rss+xml"
    return _feed(request, subscription, template, mimetype=mimetype)


def feed_atom_public(request, public_id, template="atom_public.xml"):
    subscription = get_object_or_404(Subscription, public_id=public_id)
    now = timezone.now()
    if subscription.needs_update(subscription.feed_public_stamp, now):
        subscription.check_beacon_status(now)
        # don't specify encoding for unicode strings!
        # subscription.feed_public_cache = db.Text(_feed(request, subscription, template, public=True))
        subscription.feed_public_stamp = now
        try:
            subscription.save()  # this put is not highly relevant
        except Exception as e:
            logging.warning(e)
    return HttpResponse(subscription.feed_public_cache, mimetype="application/atom+xml")


def feed_rss_public(request, public_id, template="subscription/rss_public.xml"):
    subscription = get_object_or_404(Subscription, public_id=public_id)
    return HttpResponse(_feed(request, subscription, template, public=True), mimetype="application/rss+xml")


def _feed(request, subscription, template, public=False, mimetype="application/atom+xml"):
    now = timezone.now()
    subscription.get_settings()

    subscription.updated = now.strftime('%Y-%m-%dT%H:%M:%SZ')
    subscription.expires = (now + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%SZ')

    the_shows = subscription.get_shows()
    wait_time = timedelta(hours=6)
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
    }, content_type=mimetype)


def calendar(request, subkey):
    subscription = get_object_or_404(Subscription, subkey=subkey)
    return _calendar(request, subscription)


def calendar_public(request, public_id):
    subscription = get_object_or_404(Subscription, public_id=public_id)
    return _calendar(request, subscription, public=True)


def _calendar(request, subscription, public=False):
    response = HttpResponse(subscription.get_icalendar(public), content_type='text/calendar')
    response['Filename'] = 'seriesly-calendar.ics'  # IE needs this
    response['Content-Disposition'] = 'attachment; filename=seriesly-calendar.ics'
    return response


def guide(request, subkey):
    subscription = get_object_or_404(Subscription, subkey=subkey)
    return _guide(request, subscription)


def guide_public(request, public_id):
    subscription = get_object_or_404(Subscription, public_id=public_id)
    return _guide(request, subscription, template="subscription/guide_public.html", public=True)


def _guide(request, subscription, template="subscription/guide.html",
           public=False, extra_context=None):
    subscription.is_public = public
    subscription.get_settings()
    now = timezone.now()
    the_shows = subscription.get_shows()
    episodes = Episode.get_for_shows(the_shows, order="date")
    twentyfour_hours_ago = now - timedelta(hours=24)
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
    response = render(request, template, context)
    if not public:
        response.set_cookie("subkey", subscription.subkey)
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
    subscription.last_changed = timezone.now()
    subscription.save()
    if subscription.email != "" and subscription.activated_mail is False:
        send_confirmation_mail_task.delay(subscription.subkey)
    return redirect(subscription.get_absolute_url() + "#email")


def confirm_mail(request, subkey, confirmkey):
    subscription = get_object_or_404(Subscription, subkey=subkey)
    if not subscription.check_signed_email(confirmkey):
        raise Http404

    if subscription.activated_mail is False and subscription.email != "":
        subscription.activated_mail = True
        subscription.save()

    # FIXME: add messages

    return redirect(
        subscription.get_absolute_url() + "#email"
    )


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
    subscription.last_changed = timezone.now()
    subscription.save()
    return HttpResponseRedirect(subscription.get_absolute_url() + "#webhook")


@is_post
def run_webhook_test(request, subkey):
    subscription = get_object_or_404(Subscription, subkey=subkey)
    if subscription.webhook is None:
        raise Http404
    Subscription.add_webhook_task(subscription.key())
    return HttpResponse("Task for posting to %s added. Will run in some seconds. Be reminded of The Rules on http://www.seriesly.com/webhook-xml/#the-rules" % subscription.webhook)


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
