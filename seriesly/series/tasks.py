from .models import Show

from ..celery import app


@app.task
def update_all_shows():
    shows = Show.objects.filter(active=True)
    for show in shows:
        show.update()


@app.task
def update_show(show_id, full=False):
    try:
        show = Show.objects.get(pk=show_id)
    except Show.DoesNotExist:
        pass
    show.update(full=full)
