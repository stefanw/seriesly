import logging

from django.shortcuts import get_object_or_404, render_to_response
from django.http import HttpResponse,HttpResponseRedirect,Http404
from django.template import RequestContext

from helper import is_get, is_post
from series.models import Show, Episode
from subscription.forms import SubscriptionForm

def import_shows(request):
    from series_list import series_list
    show_names = series_list.split("\n")
    Show.clear_cache()
    for show_name in show_names:
        Show.update_or_create(show_name)
    Show.clear_cache()
    return HttpResponse("Done")
    
def import_show(request):
    if request.method == "GET":
        return HttpResponse("""<form action="." method="post">
            <input type="text" name="show"/><input type="submit"/></form>""")
    else:
        name = request.POST["show"]
        if name.startswith("!"):
            show_id = int(name[1:])
            Show.update_or_create(None, show_id)
        else:
            Show.update_or_create(name)
        Show.clear_cache()
        Episode.clear_cache()
        return HttpResponse("Done")
    
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
    except Exception, e:
        logging.error("Error Updating Show (%s)%s: %s" % (show, key, e))
        return HttpResponse("Done (with errors, %s(%s))" % (show,key))
    logging.debug("Done updating show %s(%s)" % (show,key))
    return HttpResponse("Done: %s(%s)" % (show,key))
    
def redirect_to_front(request, episode_id):
    return HttpResponseRedirect("/")
    
def clear_cache(request):
    Show.clear_cache()
    Episode.clear_cache()
    return HttpResponse("Done.")