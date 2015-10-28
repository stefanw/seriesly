import logging

from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.core.urlresolvers import reverse

from seriesly.series.models import Show, Episode
from seriesly.helper import is_get, is_post


def import_shows(request):
    this_url = reverse("seriesly-shows-import_show")
    user = request.user
    status = request.GET.get("status", None)
    if status is not None:
        status = "Shows are now being imported."
    nick = False
    if user:
        nick = user.username
    if user.is_authenticated() and user.is_staff:
        if request.method == "GET":
            return render_to_response("import_show.html", RequestContext(request,
                {"logged_in": True,
                    "nick": nick,
                    "status": status,
                    "logout_url": users.create_logout_url(this_url)}))
        else:
            shows = request.POST["show"]
            try:
                shows = [int(s.strip()) for s in shows.split(",")]
            except ValueError:
                return HttpResponse("Error: there was an invalid ID", status=400)
            for show in shows:
                t = taskqueue.Task(url=reverse('seriesly-shows-import'),
                        params={"show": str(show)})
                t.add(queue_name='series')
            return HttpResponseRedirect(this_url + "?status=Done")
    else:
        return render_to_response("import_show.html", RequestContext(request,
            {"logged_in": False, "nick": nick, "login_url": users.create_login_url(this_url),
            "logout_url": users.create_logout_url(this_url)}))


@is_post
def import_show_task(request):
    show_id = None
    try:
        show_id = request.POST.get("show", None)
        if show_id is None:
            raise Http404
        Show.update_or_create(None, int(show_id))
    except Http404:
        raise Http404
    except Exception as e:
        logging.error("Error Importing Show %s: %s" % (show_id, e))
        return HttpResponse("Done (with errors, %s))" % (show_id))
    logging.debug("Done importing show %s" % (show_id))
    return HttpResponse("Done: %s" % (show_id))


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
