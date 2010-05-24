import logging

from django.shortcuts import get_object_or_404, render_to_response
from django.http import HttpResponse,HttpResponseRedirect,Http404
from django.template import RequestContext

from helper import is_get, is_post
from releases.models import Release
from series.models import Episode

def update_releases(request):
    for provider in Release.providers.keys():
        Release.add_update_task(provider)
    Episode.add_clear_cache_task("releases")
    return HttpResponse("Done: \n%s" % Release.providers.keys())

@is_post
def update_provider(request):
    provider = None
    try:
        provider = request.POST.get("provider", None)
        if not provider in Release.providers:
            raise Http404
        Release.update_provider(Release.providers[provider])
    except Exception, e:
        logging.error("Error Updating Provider %s: %s" % (provider, e))
        return HttpResponse("Done (with errors): %s" % provider)
    logging.debug("Done updating release provider %s" % provider)
    return HttpResponse("Done: %s" % provider)

@is_get
def redirect_to_release(request, release_id):
    release = Release.get_by_id(int(release_id))
    if release is None:
        raise Http404
    return HttpResponseRedirect(release.url)