from itertools import chain
import re

from django.utils.html import conditional_escape
from django.utils.encoding import force_unicode
from django import forms
from django.utils.safestring import mark_safe

from seriesly.series.models import Show
from seriesly.subscription.models import Subscription


def get_choices():
    shows = Show.get_all_ordered()
    return [(str(show.idnr),
            {"name": show.ordered_name, "new": show.is_new,
            "tvrage_id": show.tvrage_id}) for show in shows]


class HTML5EmailInput(forms.TextInput):
    input_type = 'email'


class HTML5URLInput(forms.TextInput):
    input_type = 'url'


class HTML5EmailField(forms.EmailField):
    widget = HTML5EmailInput

    def widget_attrs(self, widget):
        """
        Given a Widget instance (*not* a Widget class), returns a dictionary of
        any HTML attributes that should be added to the Widget, based on this
        Field.
        """
        return {
            "placeholder": "your.name@example.com",
            "class": "default-value email-sub"
        }


class HTML5XMPPField(forms.CharField):
    def widget_attrs(self, widget):
        """
        Given a Widget instance (*not* a Widget class), returns a dictionary of
        any HTML attributes that should be added to the Widget, based on this
        Field.
        """
        return {
            "placeholder": "account@example.com",
            "class": "default-value email-sub"
        }


class HTML5URLField(forms.CharField):
    widget = HTML5URLInput


class SerieslyCheckboxSelectMultiple(forms.CheckboxSelectMultiple):
    def render(self, name, value, attrs=None, choices=()):
        """From django.forms.widgets adapted to insert class"""
        if value is None:
            value = []
        has_id = attrs and 'id' in attrs
        final_attrs = self.build_attrs(attrs, name=name)
        # Normalize to strings
        output = []
        str_values = set([force_unicode(v) for v in value])
        for i, (option_value, option_dict) in enumerate(chain(self.choices, choices)):
            option_label = option_dict['name']
            option_new = option_dict['new']
            tvrage_id = option_dict['tvrage_id']
            # If an ID attribute was given, add a numeric index as a suffix,
            # so that the checkboxes don't all have the same ID attribute.
            if has_id:
                final_attrs = dict(final_attrs, id='%s_%s' % (attrs['id'], i))
                label_for = u' for="%s"' % final_attrs['id']
            else:
                label_for = ''
            if option_new:
                label_new = ' class="new-show"'
            else:
                label_new = ''
            cb = forms.CheckboxInput(final_attrs, check_test=lambda value: value in str_values)
            option_value = force_unicode(option_value)
            rendered_cb = cb.render(name, option_value, attrs={"data-tvrage": str(tvrage_id)})
            option_label = conditional_escape(force_unicode(option_label))
            output.append(u'<li%s><label%s>%s %s</label></li>' % (label_new, label_for,
                rendered_cb, option_label))
        return mark_safe(u'\n'.join(output))


class SubscriptionForm(forms.Form):
    subkey = forms.CharField(required=False, widget=forms.HiddenInput)
    shows = forms.MultipleChoiceField(required=True, choices=get_choices(), widget=SerieslyCheckboxSelectMultiple,
        error_messages={'required': 'You need to select at least one show!'})

    def clean_subkey(self):
        subkey = self.cleaned_data["subkey"]
        if subkey != "":
            subscription = Subscription.all().filter("subkey =", subkey).get()
            if subscription is None:
                raise forms.ValidationError("You don't have a valid Seriesly Subscription Key")
            else:
                self._subscription = subscription
        return subkey

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


class MailSubscriptionForm(forms.Form):
    email = HTML5EmailField(required=False, label="Email",
            error_messages={'invalid': "This isn't a valid email address."})
    subkey = forms.CharField(required=True, widget=forms.HiddenInput)

    def clean_subkey(self):
        subkey = self.cleaned_data["subkey"]
        sub = Subscription.all().filter("subkey =", subkey).get()
        if sub is None:
            raise forms.ValidationError("You don't have a valid Seriesly Subscription Key")
        self._subscription = sub
        return subkey

    def clean_email(self):
        email = self.cleaned_data["email"]
        if email == "your.name@example.com":
            email = ""
        return email

    def clean(self):
        cleaned_data = self.cleaned_data
        return cleaned_data


class XMPPSubscriptionForm(forms.Form):
    xmpp = HTML5XMPPField(required=False, label="XMPP-Address",
            error_messages={'invalid': "This isn't a valid xmpp address."})
    subkey = forms.CharField(required=True, widget=forms.HiddenInput)

    def clean_subkey(self):
        subkey = self.cleaned_data["subkey"]
        sub = Subscription.all().filter("subkey =", subkey).get()
        if sub is None:
            raise forms.ValidationError("You don't have a valid Seriesly Subscription Key")
        self._subscription = sub
        return subkey

    def clean_xmpp(self):
        xmpp = self.cleaned_data["xmpp"]
        if len(xmpp):
            match = re.match("^(?:([^@/<>'\"]+)@)?([^@/<>'\"]+)(?:/([^<>'\"]*))?$", xmpp)
            if match is None:
                raise forms.ValidationError("Sorry, that doesn't look like a valid XMPP Address.")
        return xmpp

    def clean(self):
        cleaned_data = self.cleaned_data
        if cleaned_data["xmpp"] != "":
            sub = Subscription.all().filter("xmpp =", cleaned_data["xmpp"]).filter("subkey !=", self._subscription.subkey).get()
            if sub is not None:
                self._errors["xmpp"] = forms.util.ErrorList(["This XMPP address already belongs to a subscription."])
                del cleaned_data["xmpp"]
        return cleaned_data


class WebHookSubscriptionForm(forms.Form):
    webhook = HTML5URLField(required=False, label="Callback URL",
            error_messages={'invalid': "This isn't a valid HTTP URL."}, initial="http://")
    subkey = forms.CharField(required=True, widget=forms.HiddenInput)

    def clean_subkey(self):
        subkey = self.cleaned_data["subkey"]
        sub = Subscription.all().filter("subkey =", subkey).get()
        if sub is None:
            raise forms.ValidationError("You don't have a valid Seriesly Subscription Key")
        self._subscription = sub
        return subkey

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


class SubscriptionKeyForm(forms.Form):
    subkey = forms.CharField(required=True, widget=forms.HiddenInput)

    def clean_subkey(self):
        subkey = self.cleaned_data["subkey"]
        sub = Subscription.all().filter("subkey =", subkey).get()
        if sub is None:
            raise forms.ValidationError("You don't have a valid Seriesly Subscription Key")
        self._subscription = sub
        return subkey
