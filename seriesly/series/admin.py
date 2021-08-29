from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import PermissionDenied
from django.conf.urls import url
from django.contrib import admin

from .models import Show, Season, Episode
from .tasks import update_show


class ShowAdmin(admin.ModelAdmin):
    list_display = ('name', 'network', 'active')
    list_filter = ('active', 'country')
    search_fields = ('name', 'alt_names')
    actions = ["update"]

    def get_urls(self):
        urls = super(ShowAdmin, self).get_urls()
        my_urls = [
            url(
                r"^import/$",
                self.admin_site.admin_view(self.import_show),
                name="series-import_show",
            ),
        ]
        return my_urls + urls

    def import_show(self, request):
        if not request.method == "POST":
            raise PermissionDenied
        if not self.has_change_permission(request):
            raise PermissionDenied

        show = Show.update_or_create(request.POST.get("name", ""))
        self.message_user(request, _("Import succeeded: %s") % show)

        Show.clear_cache()

        return redirect("admin:series_show_changelist")

    def update(self, request, queryset):
        for show in queryset:
            update_show.delay(show.pk, full=True)


admin.site.register(Show, ShowAdmin)
admin.site.register(Season)
admin.site.register(Episode)
