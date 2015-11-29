#-*-coding:utf-8-*-
import logging
import datetime
import urllib
import calendar

import pytvmaze

import dateutil.parser
from pytz import utc

from helper.http import get as http_get
from helper.html import unescape
from helper.string_utils import normalize
from helper.dateutils import get_timezone_for_gmt_offset


monthsToNumber = dict((v,k) for k,v in enumerate(calendar.month_abbr))

class TVDataClass(object):
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class TVShowInfo(TVDataClass):
    pass


class TVSeasonInfo(TVDataClass):
    pass


class TVEpisodeInfo(TVDataClass):
    pass


class TVMaze(object):

    def get_info(self, show_id):
        """http://api.tvmaze.com/shows/82:
        
        [{
          "score":1.9266452,
          "show":{
                 "id":82,
                 "url":"http://www.tvmaze.com/shows/82/game-of-thrones",
                 "name":"Game of Thrones",
                 "type":"Scripted",
                 "language":"English",
                 "genres":["Drama","Adventure","Fantasy"],
                 "status":"Running",
                 "runtime":60,
                 "premiered":"2011-04-17",
                 "schedule":{
                             "time":"21:00",
                             "days":["Sunday"]},
                 "rating":{"average":9.4},
                 "weight":27,
                 "network":{"id":8,
                            "name":"HBO",
                            "country":{
                                       "name":"United States",
                                       "code":"US",
                                       "timezone":"America/New_York"}},
                 "webChannel":null,
                 "externals":{"tvrage":24493,"thetvdb":121361},
                 "image":{"medium":"http://tvmazecdn.com/uploads/images/medium_portrait/0/581.jpg",
                          "original":"http://tvmazecdn.com/uploads/images/original_untouched/0/581.jpg"},
                 "summary":"<p>Based on the bestselling book series A Song of Ice and Fire...</p>",
                 "updated":1444833343,
                 "_links":{"self":{"href":"http://api.tvmaze.com/shows/82"},
                           "previousepisode":{"href":"http://api.tvmaze.com/episodes/162186"}}
                 }
        }]"""
        
        show = pytvmaze.get_show(maze_id=show_id)
        
        # airtime in tvmaze is defined by "airstamp" (ISO8601 formated timestamp) using UTC as reference
        # see: https://en.wikipedia.org/wiki/ISO_8601
        # info from blogpost (http://www.tvmaze.com/threads/4/api-changelog):
        #
        #    Timezone information was just added to the API. Each episode now has an "airstamp" property,
        #    which is an ISO 8601 formatted timestamp of when the episode aired. For example,
        #    for a Homeland episode which premieres in the America/New_York timezone the value is
        #    "2014-12-19T21:00:00-05:00", while the UK's Graham Norton Show (Europe/London) has
        #    "2014-12-19T22:35:00+00:00".
        #
        #    Please note the special case of episodes that air after midnight. For the airdate property,
        #    such episodes are considered part of the previous day, but the new airstamp property will
        #    display the technically correct date. For example, tonight's episode of the Late Late Show
        #    has an airdate property of "2014-12-19", an airtime of "00:35", and an airstamp of
        #    "2014-12-20T00:35:00-05:00".
        
        season_list = []
        for season in show.seasons:
            episode_list = []
            for episode in show[season].episodes:
                try:
                    date = dateutil.parser.parse(show[season][episode].airstamp)
                except ValueError:
                    date = None
                ep_info = TVEpisodeInfo(date      = date,
                                        title     = show[season][episode].title,
                                        nr        = show[season][episode].episode_number,
                                        season_nr = show[season][episode].season_number)
                episode_list.append(ep_info)
            season = TVSeasonInfo(season_nr= show[season].season_number, episodes=episode_list)
            season_list.append(season)
        
        # show has eigther network or webChannel data, depending if tv- or web-series
        if show.network == None:
            timezone = show.webChannel["country"]["timezone"]
            country  = show.webChannel["country"]["code"]
            network  = show.webChannel["name"]
        else:
            timezone = show.network["country"]["timezone"]
            country  = show.network["country"]["code"]
            network  = show.network["name"]
        
        if show.status == "Ended":
            active = False
        else:
            active = True
        
        genre_str = "|".join(show.genres)
        
        logging.debug("Return TVShowInfo..." + show.name)
        
        return TVShowInfo(name=show.name,
                          seasons=season_list,
                          tvmaze_id=show.id,
                          country=country,
                          runtime=show.runtime,
                          network=network,
                          timezone=timezone,
                          active=active,
                          genres=genre_str)

    def get_info_by_name(self, show_name):
        """http://api.tvmaze.com/singlesearch/shows?q=game%20of%20thrones:
        
        {
         "id":82,
         "url":"http://www.tvmaze.com/shows/82/game-of-thrones",
         "name":"Game of Thrones",
         "type":"Scripted",
         "language":"English",
         "genres":["Drama","Adventure","Fantasy"],
         "status":"Running",
         "runtime":60,
         "premiered":"2011-04-17",
         "schedule":{
                     "time":"21:00",
                     "days":["Sunday"]},
         "rating":{"average":9.4},
         "weight":27,
         "network":{"id":8,
                    "name":"HBO",
                    "country":{
                               "name":"United States",
                               "code":"US",
                               "timezone":"America/New_York"}},
         "webChannel":null,
         "externals":{"tvrage":24493,"thetvdb":121361},
         "image":{"medium":"http://tvmazecdn.com/uploads/images/medium_portrait/0/581.jpg",
                  "original":"http://tvmazecdn.com/uploads/images/original_untouched/0/581.jpg"},
         "summary":"<p>Based on the bestselling book series A Song of Ice and Fire...</p>",
         "updated":1444833343,
         "_links":{"self":{"href":"http://api.tvmaze.com/shows/82"},
                   "previousepisode":{"href":"http://api.tvmaze.com/episodes/162186"}}
        }"""
        show = pytvmaze.show_single_search(show_name)
        
        if show.id is None:
            logging.warn("Did not really find %s" % show_name)
            return None
        
        return self.get_info(show.id)


def main():
    tz = get_timezone_for_gmt_offset("GMT-5 -DST")
    date_str = "2011-01-31"
    date = datetime.datetime(*map(int, date_str.split("-")))
    delta = datetime.timedelta(hours=21, minutes=0)
    date = date + delta
    date = tz.localize(date)
    today = datetime.datetime.now(utc)
    print date >= today
    tvmaze = TVMaze()
    print tvmaze.get_info(15614).active

if __name__ == '__main__':
    main()
