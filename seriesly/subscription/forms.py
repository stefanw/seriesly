import re

from django import forms
from django.utils.safestring import mark_safe

from series.models import Show
from subscription.models import Subscription

def get_choices():
    shows = Show.get_all_ordered()
    return [(str(show.idnr), show.ordered_name) for show in shows]
    
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
        return {"placeholder": "your.name@example.com", "class": "default-value email-sub"}
        
class HTML5XMPPField(forms.CharField):
    def widget_attrs(self, widget):
        """
        Given a Widget instance (*not* a Widget class), returns a dictionary of
        any HTML attributes that should be added to the Widget, based on this
        Field.
        """
        return {"placeholder": "account@example.com", "class": "default-value email-sub"}
        
class HTML5URLField(forms.CharField):
    widget = HTML5URLInput
    
class SerieslyCheckboxSelectMultiple(forms.CheckboxSelectMultiple):
    def render(self, *args, **kwargs):
        output = super(SerieslyCheckboxSelectMultiple, self).render(*args, **kwargs)
        return mark_safe(u"\n".join(output.split("\n")[1:-1]))


class SubscriptionForm(forms.Form):
    subkey = forms.CharField(required=False, widget=forms.HiddenInput)
    shows = forms.MultipleChoiceField(required=True, choices=get_choices(), widget=SerieslyCheckboxSelectMultiple, 
        error_messages={'required': 'You need to select at least one show!'})
    torrent = forms.BooleanField(initial=True, label="Torrent Files", required=False)
    stream = forms.BooleanField(initial=True, label="Streaming Links", required=False)
    quality = forms.ChoiceField(choices=[("default", "Standard"), ("720p", "720p"), ("1080p", "1080p")], label="Quality")

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
        if len(self.cleaned_data["shows"]) > 90:
            raise forms.ValidationError("You can select 90 shows maximum!")
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
#        if cleaned_data["email"] != "":
#                self._errors["email"] = forms.util.ErrorList(["This email address already has a subscription."])
#                del cleaned_data["email"]
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
            if not webhook.startswith("http://") and not webhook.startswith("https://") :
                webhook = "http://" + webhook
            match = re.match("^https?://.+?$", webhook)
            if match is None:
                raise forms.ValidationError("Sorry, that doesn't look like a valid XMPP Address.")
        else:
            webhook = None
        return webhook