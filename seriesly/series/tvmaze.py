#-*-coding:utf-8-*-
from xml.dom.minidom import parseString
import logging
import datetime
import urllib
import calendar
import pytvmaze

from pytz import utc

from helper.http import get as http_get
from helper.html import unescape
from helper.string_utils import normalize
from helper.dateutils import get_timezone_for_gmt_offset

import pytvmaze


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
        show_json = pytvmaze.show_main_info(show_id)
        if show_json:
            return show = pytvmaze.Show(show_json)
        
        seasons = show_doc.getElementsByTagName("Season")
        special = show_doc.getElementsByTagName("Special")
        seasons.extend(special)
        timezone = show_doc.getElementsByTagName("timezone")[0].firstChild.data
            episode_list = []
                ep_info = TVEpisodeInfo(date=date, title=title, nr=epnum, season_nr=season_nr)
                episode_list.append(ep_info)
            season = TVSeasonInfo(season_nr=season_nr, episodes=episode_list)
            season_list.append(season)

        country = show_doc.getElementsByTagName("origin_country")[0].firstChild.data
        
        if show.status == "Ended":
            active = False
        elif:
            active = True
        
        logging.debug("Return TVShowInfo...")
        return TVShowInfo(name=show.name,
                              seasons=season_list,
                              tvmaze_id=show_id,
                              country=country,
                              runtime=show.runtime,
                              network=show.network,
                              timezone=timezone,
                              active=active,
                              genres=show.genres)

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
        if show_name.endswith(", The"):
            show_name = show_name.replace(", The", "")
            show_name = "The " + show_name
        show_xml = http_get(self.search_info_url % urllib.urlencode({"show": show_name}))
        dom = parseString(show_xml)
        shows = dom.getElementsByTagName("show")
        show_id = None
        for show in shows:
            if normalize(unescape(show.getElementsByTagName("name")[0].firstChild.data)) == normalize(show_name):
                show_id = int(show.getElementsByTagName("showid")[0].firstChild.data)
                break
        if show_id is None:
            logging.warn("Did not really find %s" % show_name)
            if len(shows):
                logging.warn("Taking first")
                return self.get_info(int(shows[0].getElementsByTagName("showid")[0].firstChild.data))
            return None
        return self.get_info(show_id)


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
