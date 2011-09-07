#-*-coding:utf-8-*-
from xml.dom.minidom import parseString
import logging
import datetime
import urllib

from pytz import utc

from helper.http import get as http_get
from helper.html import unescape
from helper.string_utils import normalize
from helper.dateutils import get_timezone_for_gmt_offset


class TVDataClass(object):
    def __init__(self, **kwargs):
        for k,v in kwargs.items():
            setattr(self, k, v)

class TVShowInfo(TVDataClass):
    pass
        
class TVSeasonInfo(TVDataClass):
    pass
        
class TVEpisodeInfo(TVDataClass):
    pass

class TVRage(object):
    show_info_url = "http://services.tvrage.com/feeds/full_show_info.php?sid=%d"
    search_info_url = "http://services.tvrage.com/feeds/search.php?%s"
    
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
        logging.debug("Start downloading...")
        show_xml = http_get(self.show_info_url % show_id)
        logging.debug("Start parsing...")
        dom = parseString(show_xml)
        logging.debug("Start walking...")
        show_doc = dom.getElementsByTagName("Show")[0]
        seasons = show_doc.getElementsByTagName("Season")
        special = show_doc.getElementsByTagName("Special")
        seasons.extend(special)
        timezone = show_doc.getElementsByTagName("timezone")[0].firstChild.data
        tz = get_timezone_for_gmt_offset(timezone)
        last_show_date = None
        delta_params = show_doc.getElementsByTagName("airtime")[0].firstChild.data.split(":")
        delta = datetime.timedelta(hours=int(delta_params[0]), minutes=int(delta_params[1]))
        season_list = []
        for season in seasons:
            try:
                season_nr = int(season.attributes["no"].value)
            except Exception:
                season_nr = False
            episode_list = []
            for episode in season.getElementsByTagName("episode"):
                if season_nr is False:
                    season_nr = int(episode.getElementsByTagName("season")[0].firstChild.data)
                try:
                    title = unescape(episode.getElementsByTagName("title")[0].firstChild.data)
                except AttributeError:
                    title = ""
                date_str = episode.getElementsByTagName("airdate")[0].firstChild.data
                try:
                    date = datetime.datetime(*map(int, date_str.split("-")))
                    date = date + delta
                    date = tz.localize(date)
                except ValueError, e:
                    date = None
                if date is not None:
                    if last_show_date is None or last_show_date < date:
                        last_show_date = date
                try:
                    epnum = int(episode.getElementsByTagName("seasonnum")[0].firstChild.data)
                except IndexError:
                    epnum = 0
                ep_info = TVEpisodeInfo(date=date, title=title, nr=epnum, season_nr=season_nr)
                episode_list.append(ep_info)
            season = TVSeasonInfo(season_nr=season_nr, episodes=episode_list)
            season_list.append(season)
        try:
            runtime = int(show_doc.getElementsByTagName("runtime")[0].firstChild.data)
        except IndexError:
            runtime = 30
        name = unescape(show_doc.getElementsByTagName("name")[0].firstChild.data)
        country = show_doc.getElementsByTagName("origin_country")[0].firstChild.data
        network = unescape(show_doc.getElementsByTagName("network")[0].firstChild.data)
        
        genres = show_doc.getElementsByTagName("genre")
        genre_list = []
        for genre in genres:
            genre_list.append(genre.firstChild.data)
        genre_str = "|".join(genre_list)
        today = datetime.datetime.now(utc) - datetime.timedelta(hours=24)
        active = show_doc.getElementsByTagName("ended")[0].firstChild
        if active is None or active.data == "0":
            active = True
        else:
            active = False
        logging.debug("Return TVShowInfo...")
        return TVShowInfo(name=name,
                              seasons=season_list, 
                              tvrage_id=show_id,
                              country=country,
                              runtime=runtime,
                              network=network,
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
if __name__ == '__main__':
    main()
