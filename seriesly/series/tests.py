from datetime import timedelta

from django.utils import timezone

from .models import Show, Season, Episode


def make_shows():
    now = timezone.now()
    show = Show.objects.create(name="Seriesly!", runtime=60, provider_id=0)
    show_2 = Show.objects.create(name="Seriously!", runtime=60, provider_id=1)
    season = Season.objects.create(show=show, number=1)
    Episode.objects.create(
        show=show,
        season=season,
        season_number=season.number,
        number=1,
        title="First Episode",
        date=now - timedelta(days=8),
    )
    Episode.objects.create(
        show=show,
        season=season,
        season_number=season.number,
        number=2,
        title="Second Episode",
        date=now - timedelta(days=3),
    )
    Episode.objects.create(
        show=show,
        season=season,
        season_number=season.number,
        number=3,
        title="Third Episode",
        date=now + timedelta(days=4),
    )
    return [show, show_2]
