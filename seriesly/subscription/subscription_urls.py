from django.conf.urls import url

from .views import (
    index,
    subscribe,
    show_public,
    guide_public,
    feed_rss_public,
    feed_atom_public,
    calendar_public,
    get_json_public,
    show,
    confirm_mail,
    edit,
    guide,
    feed_rss,
    feed_atom,
    calendar,
    get_json,
    run_webhook_test,
)

urlpatterns = [
    url(r"^$", index, name="seriesly-index"),
    url(r"^subscribe/$", subscribe, name="seriesly-subscribe"),
    url(
        r"^public/([A-Za-z0-9]{32})/$",
        show_public,
        name="seriesly-subscription-show_public",
    ),
    url(
        r"^public/([A-Za-z0-9]{32})/guide/$",
        guide_public,
        name="seriesly-subscription-guide_public",
    ),
    url(
        r"^public/([A-Za-z0-9]{32})/rss/$",
        feed_rss_public,
        name="seriesly-subscription-rss_public",
    ),
    url(
        r"^public/([A-Za-z0-9]{32})/feed/$",
        feed_atom_public,
        name="seriesly-subscription-atom_public",
    ),
    url(
        r"^public/([A-Za-z0-9]{32})/calendar/$",
        calendar_public,
        name="seriesly-subscription-calendar_public",
    ),
    url(
        r"^public/([A-Za-z0-9]{32})/json/$",
        get_json_public,
        name="seriesly-subscription-json_public",
    ),
    url(r"^([A-Za-z0-9]{32})/$", show, name="seriesly-subscription-show"),
    url(
        r"^([A-Za-z0-9]{32})/confirm/([^/]+)/$",
        confirm_mail,
        name="seriesly-subscription-confirm_mail",
    ),
    url(r"^([A-Za-z0-9]{32})/edit/$", edit, name="seriesly-subscription-edit"),
    url(r"^([A-Za-z0-9]{32})/guide/$", guide, name="seriesly-subscription-guide"),
    url(r"^([A-Za-z0-9]{32})/rss/$", feed_rss, name="seriesly-subscription-rss"),
    url(r"^([A-Za-z0-9]{32})/feed/$", feed_atom, name="seriesly-subscription-atom"),
    url(
        r"^([A-Za-z0-9]{32})/calendar/$",
        calendar,
        name="seriesly-subscription-calendar",
    ),
    url(r"^([A-Za-z0-9]{32})/json/$", get_json, name="seriesly-subscription-json"),
    url(
        r"^([A-Za-z0-9]{32})/webhook-test/$",
        run_webhook_test,
        name="seriesly-subscription-test_webhook",
    ),
]
