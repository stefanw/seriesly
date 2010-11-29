import urllib
import logging

from google.appengine.ext import db
from google.appengine.api.labs import taskqueue

from django.core.urlresolvers import reverse

from releases.ezrss import EZRSS
from releases.tvshack import TVShack
from releases.eztvpipe import EZTVPipe
from releases.oneddl import OneDDL
# from releases.torrentz import Torrentz, TorrentzDate
#from releases.btchat import BTChatEZTV, BTChatVTV
#from releases.surfthechannel import SurfTheChannel
#from releases.piratebayez import PirateBayEZ
#from releases.piratebaytvteam import PirateBayTVTeam
from series.models import Show, Episode
from helper.string_utils import normalize

class Release(db.Model):
    episode =       db.ReferenceProperty(Episode, collection_name="release_set")
    which    =      db.StringProperty() # torrent, stream, magnet etc.
    pub_date =      db.DateTimeProperty()
    url     =       db.StringProperty()
    meta    =       db.TextProperty()
    quality =       db.StringListProperty()
    md5     =       db.StringProperty()
    torrent =       db.BlobProperty()
    torrentlen =    db.IntegerProperty()
    
    @property
    def idnr(self):
        return self.key().id()
        
    @property
    def url_domain(self):
        return ".".join(self.url.split("//")[1].split("/")[0].split(".")[-2:])
        
    @property
    def which_title(self):
        return self.which.title()
    
    @classmethod
    def kind(cls):
        return "releases_release"
    
    quality_map = {"default": 0, "Stream": 0, "WS": 1, "HDTV": 1, "720p": 2, "DVDRIP": 2,"DVDSCR": 2, "1080p":3, "PDTV": 1}
    providers = {"ezrss": EZRSS, "tvshack": TVShack, "eztvpipe": EZTVPipe, "oneddl": OneDDL}
    # "torrentz": Torrentz, "torrentz-date": TorrentzDate} 
    #, "surfthechannel": SurfTheChannel, 
    #"piratebayez": PirateBayEZ, 
    #"piratebaytvteam": PirateBayTVTeam}
    
    def __unicode__(self):
        return u"%s (%s, %s)" % (self.url, self.which, ", ".join(self.quality))

    def __str__(self):
        return "%s (%s, %s)" % (self.url, self.which, ", ".join(self.quality))
    
    @property
    def title(self):
        return u"%s (%s) from %s" % (self.which_title, self.quality[0], self.url_domain)
    
    @classmethod
    def add_update_task(cls, provider_key):
        t = taskqueue.Task(url=reverse('seriesly-releases-update_provider'), params={"provider": provider_key})
        t.add(queue_name="releases")
        return t
    
    @classmethod
    def update(cls):
        for p in cls.provider:
            cls.update_provider(p)
            
    @classmethod
    def update_provider(cls, kls):
        updater = kls()
        release_list = updater.get_info()
        for release_info in release_list:
            already = Release.all().filter("url =", release_info.url).get()
            if already is not None:
                continue
            show = Show.find(release_info.show_name)
            if show is None:
                logging.debug("There is no show named %s" % release_info.show_name)
                continue
            if release_info.season_number is not None and release_info.episode_number is not None:
                episode = Episode.all().filter("show =", show).filter("season_number =",release_info.season_number)\
                    .filter("number =",release_info.episode_number).get()
            elif release_info.pub_date is not None:
                episode = Episode.all().filter("show =", show).filter("date <",release_info.pub_date).order("-date").get()
            else:
                episode = None
            if episode is None:
                logging.debug("There is no episode in %s" % release_info)
                continue
            urlparts = release_info.url.split("//",1)
            new_url = "%s//%s" % (urlparts[0], urllib.quote(urlparts[1]))
            r = Release(episode=episode, 
                        which=release_info.which,
                        pub_date=release_info.pub_date,
                        url=new_url,
                        quality=cls.filter_quality(release_info.quality),
                        torrentlen=release_info.torrentlen
            )
            r.put()
    
    @classmethod
    def filter_quality(cls, qlist):
        nq = [q for q in qlist if q.lower() in [k.lower() for k in cls.quality_map.keys()]]
        if len(nq):
            return nq
        else:
            return ["HDTV"]
    
    @classmethod
    def filter(cls, releases, sub_settings):
        real_releases = []
        q_need = cls.quality_map[sub_settings["quality"]]
        q_range = 0
        while q_range < 4:# magic?
            for release in releases:
                if not release.which in sub_settings or not bool(sub_settings[release.which]):
                    continue
                rqs = []
                for q in release.quality:
                    if q in cls.quality_map:
                       rqs.append(cls.quality_map[q])
                    else:
                        rqs.append(1)
                if any(map(lambda x: (q_need + q_range == x) or (q_need - q_range == x), rqs)):
                    real_releases.append(release)
            q_range += 1
        return real_releases
        
    @classmethod
    def find_for_episode(cls, episode, sub_settings):
        releases = Release.all().filter("episode =", episode).fetch(50)
        return cls.filter(releases, sub_settings)