from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import PermissionDenied
from django.conf.urls import url
from django.contrib import admin

from .models import Subscription, SubscriptionItem


class SubscriptionItemInlineAdmin(admin.StackedInline):
    model = SubscriptionItem
    raw_id_fields = ("show",)


class SubscriptionAdmin(admin.ModelAdmin):
    inlines = [SubscriptionItemInlineAdmin]


admin.site.register(Subscription, SubscriptionAdmin)
