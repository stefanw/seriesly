from django.test import TestCase
from django.core.urlresolvers import reverse


class SubscriptionTest(TestCase):
    def test_index(self):
        response = self.client.get(reverse('seriesly-index'))
        self.assertEqual(response.status_code, 200)
