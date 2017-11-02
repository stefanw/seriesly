from itertools import chain
import re

from django.utils.html import conditional_escape
from django.utils.encoding import force_text
from django import forms
from django.utils.safestring import mark_safe

from seriesly.series.models import Show
from seriesly.subscription.models import Subscription


def get_choices():
    shows = Show.get_all_ordered()
    return [(show.pk,
            {"name": show.ordered_name, "new": show.is_new,
            "provider_id": show.provider_id}) for show in shows]


class SerieslyCheckboxSelectMultiple(forms.CheckboxSelectMultiple):
    def render(self, name, value, attrs=None, choices=()):
        """From django.forms.widgets adapted to insert class"""
        if value is None:
            value = []
        has_id = attrs and 'id' in attrs
        final_attrs = self.build_attrs(attrs)
        # Normalize to strings
        output = []
        str_values = set([force_text(v) for v in value])
        for i, (option_value, option_dict) in enumerate(chain(self.choices, choices)):
            option_label = option_dict['name']
            option_new = option_dict['new']
            provider_id = option_dict['provider_id']
            # If an ID attribute was given, add a numeric index as a suffix,
            # so that the checkboxes don't all have the same ID attribute.
            if has_id:
                final_attrs = dict(final_attrs, id='%s_%s' % (attrs['id'], i))
                label_for = u' for="%s"' % final_attrs['id']
            else:
                label_for = ''
            if option_new:
                label_new = ' class="is-new"'
            else:
                label_new = ''
            cb = forms.CheckboxInput(final_attrs, check_test=lambda value: value in str_values)
            option_value = force_text(option_value)
            rendered_cb = cb.render(name, option_value, attrs={"data-tvrage": str(provider_id)})
            option_label = conditional_escape(force_text(option_label))
            output.append(u'<li%s><label%s>%s %s</label></li>' % (label_new, label_for,
                rendered_cb, option_label))
        return mark_safe(u'\n'.join(output))


class SubKeyMixIn(object):
    def clean_subkey(self):
        subkey = self.cleaned_data["subkey"]
        if subkey:
            try:
                subscription = Subscription.objects.get(subkey=subkey)
            except Subscription.DoesNotExist:
                raise forms.ValidationError("You don't have a valid Seriesly Subscription")
            else:
                self._subscription = subscription
        return subkey


class SubscriptionKeyForm(SubKeyMixIn, forms.Form):
    subkey = forms.CharField(required=True, widget=forms.HiddenInput)


class SubscriptionForm(SubKeyMixIn, forms.Form):
    subkey = forms.CharField(required=False, widget=forms.HiddenInput)
    shows = forms.MultipleChoiceField(required=True, choices=get_choices, widget=SerieslyCheckboxSelectMultiple,
        error_messages={'required': 'You need to select at least one show!'})

    def clean_shows(self):
        if len(self.cleaned_data["shows"]) > 200:
            raise forms.ValidationError("You can select 200 shows maximum!")
        return self.cleaned_data["shows"]

    def checkboxclean(self, key):
        if key in self.cleaned_data:
            self.cleaned_data[key] = True
        else:
            self.cleaned_data[key] = False
        return self.cleaned_data[key]


class MailSubscriptionForm(SubscriptionKeyForm):
    email = forms.EmailField(required=False, label="Email",
            error_messages={'invalid': "This isn't a valid email address."})

    def clean_email(self):
        email = self.cleaned_data["email"]
        if email == "your.name@example.com":
            email = ""
        return email


class WebHookSubscriptionForm(SubscriptionKeyForm):
    webhook = forms.URLField(required=False, label="Callback URL",
            error_messages={'invalid': "This isn't a valid HTTP URL."}, initial="http://")

    def clean_webhook(self):
        webhook = self.cleaned_data["webhook"]
        if len(webhook):
            if (not webhook.startswith("http://") and
                    not webhook.startswith("https://")):
                webhook = "http://" + webhook
            match = re.match("^https?://.+?$", webhook)
            if match is None:
                raise forms.ValidationError(
                    "Sorry, that doesn't look like a valid XMPP Address."
                )
        else:
            webhook = None
        return webhook
