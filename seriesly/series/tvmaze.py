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
        """<Show>
        <name>Scrubs</name>
        <totalseasons>9</totalseasons>
        <showid>5118</showid>
        <showlink>http://tvrage.com/Scrubs</showlink>
        <started>Oct/02/2001</started>
        <ended></ended>
        <image>http://images.tvrage.com/shows/6/5118.jpg</image>
        <origin_country>US</origin_country>
        <status>Returning Series</status>
        <classification>Scripted</classification>
        <genres><genre>Comedy</genre></genres>
        <runtime>30</runtime>
        <network country="US">ABC</network>
        <airtime>21:00</airtime>
        <airday>Tuesday</airday>
        <timezone>GMT-5 -DST</timezone>
        <akas><aka country="LV">Dakterīši</aka><aka country="HU">Dokik</aka><aka country="SE">Första hjälpen</aka><aka country="NO">Helt sykt</aka><aka country="PL">Hoży doktorzy</aka><aka attr="Second Season" country="RU">Klinika</aka><aka attr="First Season" country="RU">Meditsinskaya akademiya</aka><aka country="DE">Scrubs: Die Anfänger</aka><aka country="RO">Stagiarii</aka><aka attr="French Title" country="BE">Toubib or not toubib</aka><aka country="FI">Tuho Osasto</aka><aka country="IL">סקרבס</aka></akas>
        <Episodelist>

        <Season no="1">
        <episode><epnum>1</epnum><seasonnum>01</seasonnum>
        <prodnum>535G</prodnum>
        <airdate>2001-10-02</airdate>
        <link>http://www.tvrage.com/Scrubs/episodes/149685</link>
        <title>My First Day</title>
        <screencap>http://images.tvrage.com/screencaps/26/5118/149685.jpg</screencap></episode>"""
        
        show = pytvmaze.get_show(maze_id=show_id)
        
        # converts time to GMT?
        # because tz is always time delta to GMT
        # -> calc utc to gmt
        
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
        
        last_show_date = None
        season_list = []
        for season in show.seasons:
            episode_list = []
            for episode in show[season].episodes:
                try:
                    date = dateutil.parser.parse(show[season][episode].airstamp)
                except ValueError:
                    date = None
                if date is not None:
                    if last_show_date is None or last_show_date < date:
                        last_show_date = date
                ep_info = TVEpisodeInfo(date      = date,
                                        title     = show[season][episode].title,
                                        nr        = show[season][episode].episode_number,
                                        season_nr = show[season][episode].season_number)
                episode_list.append(ep_info)
            season = TVSeasonInfo(season_nr= show[season].season_number, episodes=episode_list)
            season_list.append(season)
        
        if show.status == "Ended":
            active = False
        else:
            active = True
        
        timezone = show.network["country"]["timezone"]
        
        genre_str = "|".join(show.genres)
        
        # test return output
        # logging.info(" --- START TEST RETURN OUTPUT")
        # logging.info(show.name)
        # logging.info(season_list)
        # logging.info(show.id)
        # logging.info(show.network["country"]["code"])
        # logging.info(show.runtime)
        # logging.info(show.network["name"])
        # logging.info(timezone)
        # logging.info(active)
        # logging.info(genre_str)
        # logging.info(" --- END TEST RETURN OUTPUT")
        
        logging.debug("Return TVShowInfo...")
        return TVShowInfo(name=show.name,
                              seasons=season_list,
                              tvmaze_id=show.id,
                              country=show.network["country"]["code"],
                              runtime=show.runtime,
                              network=show.network["name"],
                              timezone=timezone,
                              active=active,
                              genres=genre_str)

    def get_info_by_name(self, show_name):
        """<Results>
        <show>
        <showid>2445</showid>
        <name>24</name>
        <link>http://www.tvrage.com/24</link>
        <country>US</country>
        <started>2001</started>
        <ended>0</ended>
        <seasons>8</seasons>
        <status>Returning Series</status>
        <classification>Scripted</classification>
        <genres><genre01>Action</genre01><genre02>Adventure</genre02><genre03>Drama</genre03></genres>
        </show>
        <show>"""
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
