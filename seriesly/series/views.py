import logging

from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404

from seriesly.series.models import Show, Episode
from seriesly.helper import is_get, is_post


def update(request):
    shows = Show.get_all_ordered()
    for show in shows:
        show.add_update_task()
    Episode.add_clear_cache_task("series")
    return HttpResponse("Done: %d" % (len(shows)))


@is_post
def update_show(request):
    key = None
    show = None
    try:
        key = request.POST.get("key", None)
        if key is None:
            raise Http404
        show = Show.get_all_dict().get(key, None)
        if show is None:
            raise Http404
        show.update()
    except Http404:
        raise Http404
    except Exception as e:
        logging.error("Error Updating Show (%s)%s: %s" % (show, key, e))
        return HttpResponse("Done (with errors, %s(%s))" % (show, key))
    logging.debug("Done updating show %s(%s)" % (show, key))
    return HttpResponse("Done: %s(%s)" % (show, key))


def redirect_to_front(request, episode_id):
    return HttpResponseRedirect("/")


def clear_cache(request):
    Show.clear_cache()
    Episode.clear_cache()
    return HttpResponse("Done.")


@is_get
def redirect_to_amazon(request, show_id):
    show = get_object_or_404(Show, pk=show_id)
    if not show.amazon_url:
        raise Http404
    return HttpResponseRedirect(show.amazon_url)
