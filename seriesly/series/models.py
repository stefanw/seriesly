import logging
import re
import datetime

from pytz import utc

from google.appengine.api import taskqueue
from google.appengine.api import memcache
from google.appengine.ext import db

from django.core.urlresolvers import reverse

from helper.string_utils import normalize
from helper.dateutils import get_timezone_for_gmt_offset

from series.tvmaze import TVMaze


class Show(db.Model):
    name = db.StringProperty()
    normalized_name = db.StringProperty()
    alt_names = db.StringProperty()
    slug = db.StringProperty()
    description = db.StringProperty(indexed=False)
    genres = db.StringProperty(indexed=False)
    network = db.StringProperty(indexed=False)
    active = db.BooleanProperty()
    country = db.StringProperty(indexed=False)
    runtime = db.IntegerProperty()
    timezone = db.StringProperty(indexed=False)
    tvmaze_id = db.IntegerProperty()
    added = db.DateTimeProperty()

    _memkey_all_shows_ordered = "all_shows_ordered"
    _memkey_shows_dict = "all_shows_dict"
    re_find_the = re.compile("^The (.*)$")

    @classmethod
    def kind(cls):
        return "series_show"

    def __unicode__(self):
        return self.name

    @property
    def idnr(self):
        return self.key().id()

    @property
    def slug(self):
        return self.normalized_name.replace(" ", "-")

    def alternative_names(self):
        if self.alt_names is None:
            return []
        return self.alt_names.split("|")

    @classmethod
    def get_all_ordered(cls):
        shows = memcache.get(cls._memkey_all_shows_ordered)
        if shows is not None:
            return shows
        shows = Show.all().filter("active =", True)
        show_list = []
        for show in shows:
            if len(show.name) > 33:
                show.ordered_name = cls.re_find_the.sub(
                    "\\1, The", show.name[:33] + "...")
            else:
                show.ordered_name = cls.re_find_the.sub("\\1, The", show.name)
            show_list.append(show)
        shows = sorted(show_list, key=lambda x: x.ordered_name.lower())
        memcache.set(key=cls._memkey_all_shows_ordered, value=shows)
        return shows

    @classmethod
    def find(cls, show_name):
        if not len(show_name):
            return None
        norm_name = normalize(show_name)
        shows = Show.get_all_ordered()
        for show in shows:
            if show_name == show.name or norm_name == show.normalized_name or \
                    any([norm_name == alt_name for alt_name in show.alternative_names()]):
                return show

    @classmethod
    def get_all_dict(cls):
        show_dict = memcache.get(cls._memkey_shows_dict)
        if show_dict is not None:
            return show_dict
        shows = Show.get_all_ordered()
        show_dict = dict([(str(show.key()), show) for show in shows])
        memcache.set(key=cls._memkey_shows_dict, value=show_dict)
        return show_dict

    @classmethod
    def clear_cache(cls):
        memcache.delete(cls._memkey_all_shows_ordered)
        memcache.delete(cls._memkey_shows_dict)

    def add_update_task(self):
        t = taskqueue.Task(url=reverse('seriesly-shows-update_show'), params={"key": str(self.key())})
        t.add(queue_name="series")
        return t

    def update(self, show_info=None, get_everything=False):
        if show_info is None:
            tvmaze = TVMaze()
            show_info = tvmaze.get_info(self.tvmaze_id)
            # Kill Tabatha\u2019s ... here
            show_info.name = show_info.name.replace(u"\u2019", "'")
            # Kill >>'Til Death<< here
            if show_info.name.startswith("'"):
                show_info.name = show_info.name.replace("'", "", 1)
            attr_list = ["name", "network", "genres", "active",
                "country", "runtime", "timezone", "tvmaze_id"]
            if self.update_attrs(show_info, attr_list):
                self.put()
        for season_info in show_info.seasons:
            logging.debug("Update or create Season...")
            Season.update_or_create(self, season_info, get_everything=get_everything)

    def update_attrs(self, info_obj, attr_list):
        changed = False
        for attr in attr_list:
            val = getattr(info_obj, attr)
            if val != getattr(self, attr):
                setattr(self, attr, val)
                changed = True
        return changed

    def put(self):
        self.normalized_name = normalize(self.name)
        return super(Show, self).put()

    @classmethod
    def update_or_create(cls, name, show_id=None):
        tvmaze = TVMaze()
        if name is not None:
            show_info = tvmaze.get_info_by_name(name)
        else:
            show_info = tvmaze.get_info(show_id)
        if show_info is None:
            return False
        logging.debug("Does Show %s exist ...?" % show_info.tvmaze_id)
        show = Show.all().filter("tvmaze_id =", show_info.tvmaze_id).get()
        if show is None:
            logging.debug("Creating new Show... %s" % show_info.name)
            show = Show(name=show_info.name,
                        network=show_info.network,
                        genres=show_info.genres,
                        active=show_info.active,
                        country=show_info.country,
                        runtime=show_info.runtime,
                        timezone=show_info.timezone,
                        tvmaze_id=show_info.tvmaze_id,
                        added=datetime.datetime.now())
            show.put()
        show.update(show_info)

    @property
    def is_new(self):
        if self.added is None:
            return False
        new_time = datetime.timedelta(days=7)
        if datetime.datetime.now() - self.added < new_time:
            return True
        return False


class Season(db.Model):
    show = db.ReferenceProperty(Show)
    number = db.IntegerProperty()
    start = db.DateTimeProperty()
    end = db.DateTimeProperty()

    @classmethod
    def kind(cls):
        return "series_season"

    @classmethod
    def update_or_create(cls, show, season_info, get_everything=False):
        season = Season.all().filter("show =", show).filter(
                "number =", season_info.season_nr).get()
        logging.debug("Found season: S%s" % season.number)
        if season is None:
            season = Season(show=show, number=season_info.season_nr)
            season.put()
        season.update(season_info, get_everything=get_everything)
        season.put()

    def update(self, season_info, get_everything=False):
        first_date = None
        episode_info = None
        now = utc.localize(datetime.datetime.now())
        fortyeight_hours_ago = now - datetime.timedelta(hours=48)
        for episode_info in season_info.episodes:
            logging.debug("Update episode... S%sE%s %s" % (episode_info.season_nr, episode_info.nr, episode_info.title))
            if first_date is None:
                first_date = episode_info.date
            if get_everything or episode_info.date is None or episode_info.date >= fortyeight_hours_ago:
                Episode.update_or_create(self, episode_info)
        logging.debug("All episodes updated...")
        self.start = first_date
        if episode_info is not None:
            self.end = episode_info.date


class Episode(db.Model):
    show = db.ReferenceProperty(Show)
    season = db.ReferenceProperty(Season)
    season_number = db.IntegerProperty()
    number = db.IntegerProperty()
    title = db.StringProperty()
    text = db.TextProperty(default="")
    date = db.DateTimeProperty()

    _memkey_episode_dict = "all_episodes_dict"

    @classmethod
    def kind(cls):
        return "series_episode"

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
            self._date_local = utc.localize(self.date).astimezone(tz)
        return self._date_local

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
        episode = Episode.all().filter("show =", season.show).filter(
            "season =", season).filter("number =", episode_info.nr).get()
        logging.debug("Found episode... %s" % episode.number)
        if episode is None:
            episode = Episode.create(season, episode_info)
        else:
            episode.update(episode_info)
        episode.put()
        return episode

    @classmethod
    def create(cls, season, episode_info):
        return Episode(show=season.show, season=season,
                        season_number=season.number,
                        number=episode_info.nr,
                        title=episode_info.title,
                        date=episode_info.date)

    @classmethod
    def get_all_dict(cls):
        episode_dict = memcache.get(cls._memkey_episode_dict)
        if episode_dict is not None:
            return episode_dict
        now = datetime.datetime.now()
        one_week_ago = now - datetime.timedelta(days=8)
        # in_one_week = now + datetime.timedelta(days=8)
        episodes = Episode.all().filter("date >", one_week_ago)
        # removed this: .filter("date <",in_one_week).fetch(1000)
        episode_dict = {}
        for ep in episodes:
            if len(episode_dict.get(str(ep._show), [])) < 20:
                # store max of 20 episodes per show
                episode_dict.setdefault(str(ep._show), []).append(ep)
        memcache.set(key=cls._memkey_episode_dict, value=episode_dict)
        return episode_dict

    @classmethod
    def clear_cache(cls):
        memcache.delete(cls._memkey_episode_dict)

    @classmethod
    def add_clear_cache_task(cls, queue_name):
        t = taskqueue.Task(url=reverse('seriesly-shows-clear_cache'), params={})
        t.add(queue_name=queue_name)
        return t

    @classmethod
    def get_for_shows(cls, shows, before=None, after=None, order=None):
        episode_list = []
        episode_dict = Episode.get_all_dict()
        changed = False
        for show in shows:
            k = str(show.key())
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
            memcache.set(key=cls._memkey_episode_dict, value=episode_dict)
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
            if lower > 0 or upper < len(episode_list):
                episode_list = episode_list[lower:upper]
        if order is not None and order.startswith("-"):
            episode_list.reverse()
        return episode_list

    @classmethod
    def get_for_shows_old(cls, shows, before=None, after=None, order=None):
        def extra(q):
            if before is not None:
                q = q.filter("date <", before)
            if after is not None:
                q = q.filter("date >", after)
            if order is not None:
                q = q.order(order)
            return q

        if not len(shows):
            return []

        if len(shows) <= 28:
            logging.debug("starting query")
            query = Episode.all().filter("show IN", shows)
            return extra(query).fetch(1000)

        episodes = []
        for i in range(len(shows) / 28 + 1):
            q_shows = shows[i * 28:(i + 1) * 28]
            if not len(q_shows):
                continue
            episodes.extend(extra(Episode.all().filter("show IN", q_shows)).fetch(1000))
        if order is not None and order.startswith("-"):
            return sorted(episodes, lambda x: x.date).reverse()
        else:
            return sorted(episodes, lambda x: x.date)

    def update(self, episode_info):
        self.title = episode_info.title
        self.date = episode_info.date

    def get_next(self):
        return Episode.all().filter("date >", self.date).get()

    def create_event_details(self, cal):
        vevent = cal.add('vevent')
        vevent.add('uid').value = "seriesly-episode-%s" % self.key()
        try:
            tz = get_timezone_for_gmt_offset(self.show.timezone)
        except Exception:
            tz = utc
        date = utc.localize(self.date).astimezone(tz)
        vevent.add('dtstart').value = date
        vevent.add('dtend').value = date + datetime.timedelta(minutes=self.show.runtime)
        vevent.add('summary').value = "%s - %s (%dx%d)" % (self.show.name, self.title,
                                                                self.season_number, self.number)
        vevent.add('location').value = self.show.network
        return vevent
