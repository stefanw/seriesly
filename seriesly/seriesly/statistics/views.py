import datetime

from django.http import HttpResponse
from django.utils import simplejson as json

from seriesly.subscription.models import Subscription, SubscriptionItem
from seriesly.series.models import Show


def subscriptions(request):
    now = datetime.datetime.now()
    threshold = now - datetime.timedelta(days=30 * 3)
    subcount = 0
    for subscription in Subscription.all():
        if subscription.last_visited is not None and subscription.last_visited > threshold:
            subcount += 1
    return HttpResponse("Done: \n%d" % subcount)


def subscribed_shows(request):
    subcount = 0
    show_ranking = {}
    user_ranking = {}
    for subitem in SubscriptionItem.all():
        # if subscription.last_visited is not None and subscription.last_visited > threshold:
        subcount += 1
        show_ranking.setdefault(subitem._show, 0)
        show_ranking[subitem._show] += 1
        user_ranking.setdefault(subitem._subscription, 0)
        user_ranking[subitem._subscription] += 1
    tops = []
    top_users = user_ranking.items()
    for show in Show.all():
        if show.active:
            tops.append((show.name, show_ranking.get(show.key(), 0)))
    tops.sort(key=lambda x: x[1], reverse=True)
    top_users.sort(key=lambda x: x[1], reverse=True)
    return HttpResponse("Done: <br/>%s" % "<br/>".join(map(lambda x: "%s: %d" % (x[0], x[1]), tops)) + "<hr/>" + "<br/>".join(map(lambda x: "%s: %d" % (x[0], x[1]), top_users)))


def dump_subscriptions(request):
    users = {}
    for subitem in SubscriptionItem.all():
        # if subscription.last_visited is not None and subscription.last_visited > threshold:
        users.setdefault(str(subitem._subscription), [])
        users[str(subitem._subscription)].append(str(subitem._show))
    return HttpResponse(json.dumps(users))
