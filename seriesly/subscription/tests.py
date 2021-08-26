from django.test import TestCase
from django.core.urlresolvers import reverse

from .models import Subscription
from ..series.tests import make_shows


def make_world():
    return {"shows": make_shows()}


class SubscriptionTest(TestCase):
    def setUp(self):
        self.data = make_world()

    def test_index(self):
        response = self.client.get(reverse("seriesly-index"))
        self.assertEqual(response.status_code, 200)

    def test_empty_subscribe(self):
        response = self.client.post(reverse("seriesly-subscribe"), {"shows": []})
        self.assertEqual(response.status_code, 400)

    def test_subscribe(self):
        response = self.client.post(
            reverse("seriesly-subscribe"), {"shows": [x.pk for x in self.data["shows"]]}
        )
        subs = Subscription.objects.all()
        sub = subs[0]
        self.assertRedirects(
            response, reverse("seriesly-subscription-show", args=[sub.subkey])
        )
