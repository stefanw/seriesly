import logging

from django.conf import settings
from django.http import HttpResponse,HttpResponseRedirect,Http404
from django.template import RequestContext

from helper import is_get, is_post
from series.models import Show, Episode

from productapi import API

def update(request):
    shows = Show.get_all_ordered()
    for show in shows:
        show.add_amazon_update_task()
    Episode.add_clear_cache_task("series")
    return HttpResponse("Done: %d" % (len(shows)))


@is_post
def product_for_show(request):
    key = None
    show = None
    url, title = "None", "None"
    try:
        key = request.POST.get("key", None)
        if key is None:
            raise Http404
        show = Show.get_all_dict().get(key, None)
        if show is None:
            raise Http404
        aps = API(settings.AMAZON_ACCESS_KEY, settings.AMAZON_SECRET_ACCESS_KEY, "us")
        url, title = aps.item_search("DVD", Keywords=show.name, AssociateTag=settings.AMAZON_ASSOCIATE_TAG)
        show.update_amazon(url, title)
    except Exception, e:
        logging.error("Error Amazoning Show (%s)%s: %s" % (show, key, e))
        return HttpResponse("Done (with errors, %s(%s))" % (show,key))
    logging.debug("Done amazoning show %s(%s)" % (show,key))
    return HttpResponse("Done: %s: %s, %s" % (show.name, url, title))
    
@is_get
def redirect(request, tld, slug):
    nname = slug.replace("-", " ")
    show = Show.all().filter("normalized_name =", nname).fetch(1)
    if show is None or not len(show):
        raise Http404
    return HttpResponseRedirect(show[0].amazon_link(tld=tld))