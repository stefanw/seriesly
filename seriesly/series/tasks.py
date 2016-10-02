from celery import shared_task

from .models import Show


@shared_task
def update_all_shows():
    shows = Show.objects.filter(active=True)
    for show in shows:
        show.update()
