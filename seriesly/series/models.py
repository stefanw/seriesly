import logging
import re
import datetime

from pytz import utc

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.core.cache import cache
from django.utils import timezone as tz

from seriesly.helper.string_utils import normalize
from seriesly.helper.dateutils import get_timezone_for_gmt_offset

from .providers import get_provider


def get_show_info(name, show_id=None):
    provider = get_provider()
    if show_id is None:
        show_info = provider.get_show_by_name(name)
    else:
        show_info = provider.get_show(show_id)
    return show_info


@python_2_unicode_compatible
class Show(models.Model):
    name = models.CharField(max_length=255)
    ordered_name = models.CharField(max_length=255)
    normalized_name = models.CharField(max_length=255)
    alt_names = models.TextField()
    slug = models.SlugField()
    description = models.TextField()
    genres = models.CharField(max_length=255)
    network = models.CharField(max_length=255)
    active = models.BooleanField(default=True)
    country = models.CharField(max_length=255)
    runtime = models.IntegerField()
    timezone = models.CharField(max_length=255)
    provider_id = models.IntegerField()
    added = models.DateTimeField(default=tz.now)

    _memkey_all_shows_ordered = "all_shows_ordered"
    _memkey_shows_dict = "all_shows_dict"
    re_find_the = re.compile("^The (.*)$")

    def __str__(self):
        return self.name

    def alternative_names(self):
        if self.alt_names is None:
            return []
        return self.alt_names.split("|")

    @classmethod
    def get_all_ordered(cls):
        shows = cache.get(cls._memkey_all_shows_ordered)
        if shows is not None:
            return shows
        shows = Show.objects.filter(active=True)
        show_list = []
        for show in shows:
            if len(show.name) > 33:
                show.ordered_name = cls.re_find_the.sub(
                    "\\1, The", show.name[:33] + "...")
            else:
                show.ordered_name = cls.re_find_the.sub("\\1, The", show.name)
            show_list.append(show)
        shows = sorted(show_list, key=lambda x: x.ordered_name.lower())
        cache.set(cls._memkey_all_shows_ordered, shows)
        return shows

    @classmethod
    def find(cls, show_name):
        if not len(show_name):
            return None
        norm_name = normalize(show_name)
        shows = Show.objects.get_all_ordered()
        for show in shows:
            if (show_name == show.name or norm_name == show.normalized_name or
                    any(norm_name == alt_name for alt_name in show.alternative_names())):
                return show

    @classmethod
    def get_all_dict(cls):
        show_dict = cache.get(cls._memkey_shows_dict)
        if show_dict is not None:
            return show_dict
        shows = Show.get_all_ordered()
        show_dict = dict([(str(show.pk), show) for show in shows])
        cache.set(cls._memkey_shows_dict, show_dict)
        return show_dict

    @classmethod
    def clear_cache(cls):
        cache.delete(cls._memkey_all_shows_ordered)
        cache.delete(cls._memkey_shows_dict)

    def update(self, show_info=None, everything=False):
        if show_info is None:
            show_info = get_show_info(self.name, show_id=self.provider_id)

            attr_list = ["name", "network", "genres", "active",
                "country", "runtime", "timezone", "provider_id"]
            if self.update_attrs(show_info, attr_list):
                self.save()
        for season_info in show_info['seasons']:
            logging.debug("Update or create Season...")
            Season.update_or_create(self, season_info, everything=everything)

    def update_attrs(self, info_obj, attr_list):
        changed = False
        for attr in attr_list:
            val = info_obj.get(attr)
            if val != getattr(self, attr):
                setattr(self, attr, val)
                changed = True
        return changed

    @classmethod
    def update_or_create(cls, name, show_id=None):
        show_info = get_show_info(name, show_id=None)
        if show_info is None:
            return False
        logging.debug("Show exists..?")
        try:
            show = Show.objects.get(provider_id=show_info['provider_id'])
        except Show.DoesNotExist:
            logging.debug("Creating Show...")
            show = Show(name=show_info['name'],
                        network=show_info['network'],
                        genres=show_info['genres'],
                        active=show_info['active'],
                        country=show_info['country'],
                        runtime=show_info['runtime'],
                        timezone=show_info['timezone'],
                        provider_id=show_info['provider_id'],
                        added=tz.now())
            show.save()
        show.update(show_info, everything=True)
        return show

    @property
    def is_new(self):
        if self.added is None:
            return False
        new_time = datetime.timedelta(days=7)
        if tz.now() - self.added < new_time:
            return True
        return False


@python_2_unicode_compatible
class Season(models.Model):
    show = models.ForeignKey(Show)
    number = models.IntegerField()
    start = models.DateTimeField(null=True)
    end = models.DateTimeField(null=True)

    def __str__(self):
        return u'{} ({})'.format(self.show, self.number)

    @classmethod
    def update_or_create(cls, show, season_info, everything=False):
        try:
            season = Season.objects.get(show=show, number=season_info['season_nr'])
        except Season.DoesNotExist:
            season = Season(show=show, number=season_info['season_nr'])
            season.save()
        season.update(season_info, everything=everything)
        season.save()
        return season

    def update(self, season_info, everything=False):
        first_date = None
        episode_info = None
        now = tz.now()
        fortyeight_hours_ago = now - datetime.timedelta(hours=48)
        for episode_info in season_info['episodes']:
            logging.debug("Update episode... %s" % episode_info)
            if first_date is None:
                first_date = episode_info['date']
            if (everything or episode_info['date'] is None or
                    episode_info['date'] >= fortyeight_hours_ago):
                Episode.update_or_create(self, episode_info)
        logging.debug("All episodes updated...")
        self.start = first_date
        if episode_info is not None:
            self.end = episode_info['date']


@python_2_unicode_compatible
class Episode(models.Model):
    show = models.ForeignKey(Show)
    season = models.ForeignKey(Season, null=True)
    season_number = models.IntegerField(default=0)
    number = models.IntegerField(default=0)
    title = models.CharField(max_length=255)
    text = models.TextField()
    date = models.DateTimeField()

    _memkey_episode_dict = "all_episodes_dict"

    def __str__(self):
        return u'{} S{:02d}E{:02d}'.format(self.show,
                                           self.season_number, self.number)

    @property
    def date_end(self):
        return self.date + datetime.timedelta(minutes=self.show.runtime)

    @property
    def date_local(self):
        if getattr(self, "_date_local", None) is None:
            try:
                tz = get_timezone_for_gmt_offset(self.show.timezone)
            except Exception:
                tz = utc
            self._date_local = self.date.astimezone(tz)
        return self._date_local

    @property
    def has_aired(self):
        return self.date < tz.now()

    def season_episode(self):
        return 'S{:02d}E{:02d}'.format(self.season_number, self.number)

    @property
    def date_local_end(self):
        if getattr(self, "_date_local_end", None) is None:
            try:
                tz = get_timezone_for_gmt_offset(self.show.timezone)
            except Exception:
                tz = utc
            self._date_local_end = utc.localize(self.date_end).astimezone(tz)
        return self._date_local_end

    @classmethod
    def update_or_create(cls, season, episode_info):
        try:
            episode = Episode.objects.get(show=season.show,
                                          season=season,
                                          number=episode_info['nr'])
        except Episode.DoesNotExist:
            episode = Episode.create(season, episode_info)
        else:
            episode.update(episode_info)
        episode.save()
        return episode

    @classmethod
    def create(cls, season, episode_info):
        return Episode(show=season.show, season=season,
                        season_number=season.number,
                        number=episode_info['nr'],
                        title=episode_info['title'],
                        date=episode_info['date'])

    @classmethod
    def get_all_dict(cls):
        episode_dict = cache.get(cls._memkey_episode_dict)
        if episode_dict is not None:
            return episode_dict
        now = datetime.datetime.now()
        one_week_ago = now - datetime.timedelta(days=8)
        # in_one_week = now + datetime.timedelta(days=8)
        episodes = Episode.objects.filter(date__gt=one_week_ago)
        # removed this: .filter("date <",in_one_week).fetch(1000)
        episode_dict = {}
        for ep in episodes:
            if len(episode_dict.get(str(ep.show_id), [])) < 20:
                # store max of 20 episodes per show
                episode_dict.setdefault(str(ep.show_id), []).append(ep)
        cache.set(cls._memkey_episode_dict, episode_dict)
        return episode_dict

    @classmethod
    def clear_cache(cls):
        cache.delete(cls._memkey_episode_dict)

    @classmethod
    def get_for_shows(cls, shows, before=None, after=None, order=None):
        episode_list = []
        episode_dict = Episode.get_all_dict()
        changed = False
        for show in shows:
            k = str(show.pk)
            if k in episode_dict:
                episode_dict[k].sort(key=lambda x: x.date)
                prev = None
                for ep in episode_dict[k]:
                    if prev is not None:
                        prev.next = ep
                    ep.show = show
                    prev = ep
                episode_list.extend(episode_dict[k])
        if changed:
            cache.set(cls._memkey_episode_dict, episode_dict)
        episode_list.sort(key=lambda x: x.date)
        if after is not None or before is not None:
            lower = None
            upper = len(episode_list)
            for ep, i in zip(episode_list, range(len(episode_list))):
                if after is not None and lower is None and ep.date > after:
                    lower = i
                if before is not None and ep.date > before:
                    upper = i
                    break
            if (lower is not None and lower > 0) or upper < len(episode_list):
                episode_list = episode_list[lower:upper]
        if order is not None and order.startswith("-"):
            episode_list.reverse()
        return episode_list

    def update(self, episode_info):
        self.title = episode_info['title']
        self.date = episode_info['date']

    def get_next(self):
        episodes = Episode.objects.filter(date__gt=self.date)
        if episodes:
            return episodes[0]
        return None

    def create_event_details(self, cal):
        vevent = cal.add('vevent')
        vevent.add('uid').value = "seriesly-episode-%s" % self.pk
        try:
            tz = get_timezone_for_gmt_offset(self.show.timezone)
        except Exception:
            tz = utc
        date = utc.localize(self.date).astimezone(tz)
        vevent.add('dtstart').value = date
        vevent.add('dtend').value = date + datetime.timedelta(minutes=self.show.runtime)
        vevent.add('summary').value = "%s - %s (%dx%d)" % (
                self.show.name, self.title,
                self.season_number, self.number)
        vevent.add('location').value = self.show.network
        return vevent
