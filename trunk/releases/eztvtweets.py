#-*-coding:utf-8-*-
import logging
from xml.dom.minidom import parseString
import datetime
from email.utils import parsedate_tz, mktime_tz
import urllib
import re

from pytz import timezone

from helper.http import get as http_get
from helper.html import unescape

from releases import ReleaseData

class EZRSS(object):
    feed_url = "http://twitter.com/statuses/user_timeline/37039456.rss"
#    title_regex = re.compile("(.*?) ([0-9]{1,3})[xX]([0-9]{1,3}) \[([^\]]+)\]")
    title_regex = re.compile("eztv_it: (.*?) [sS]?([0-9]+)[eExX]([0-9]+) .*? - (http://.*?)$")
    title_regex2 = re.compile("eztv_it: (.*?) [0-9]{4} [0-9]{2} [0-9]{2} .*? - (http://.*?)$")
    
    def get_info(self):
        """<item>
            <title>Royal Institution Christmas Lectures - Part2 20x9 [WS - PDTV - WATERS]</title>
            <link>http://torrent.zoink.it/Royal.Institution.Christmas.Lectures.2009.Part2.WS.PDTV.XviD-WATERS.[eztv].torrent</link>
            <category>TV Show</category>
            <pubDate>Thu, 24 Dec 2009 18:26:04 -0500</pubDate>
            <description>Show Name: Royal Institution Christmas Lectures; Episode Title: Part2; Season: 20; Episode: 9</description>
            <enclosure url="http://torrent.zoink.it/Royal.Institution.Christmas.Lectures.2009.Part2.WS.PDTV.XviD-WATERS.[eztv].torrent" length="364605440" type="application/x-bittorrent" />
            <comments>http://eztv.it/forum/discuss/18088/</comments>
            <guid>http://eztv.it/ep/18088/royal-institution-christmas-lectures-2009-part2-ws-pdtv-xvid-waters/</guid>
        </item>
        episode =       db.ReferenceProperty(Episode)
        which    =       db.StringProperty() # torrent, stream, magnet etc.
        url     =       db.StringProperty()
        meta    =       db.TextProperty()
        md5     =       db.StringProperty()
        torrent =       db.BlobProperty()
        torrentlen =    db.IntegerProperty()
        """
        rss_xml = http_get(self.feed_url)
        dom = parseString(rss_xml)
        items = dom.getElementsByTagName("item")
        release_items = []
        for item in items:
            try:
                url = item.getElementsByTagName("link")[0].firstChild.data
                desc = unescape(item.getElementsByTagName("description")[0].firstChild.data)
                desc_dict = dict(map(lambda x: tuple(x.split(": ")), desc.split("; ")))
                try:
                    date = item.getElementsByTagName("pubDate")[0].firstChild.data
                    date = datetime.datetime.fromtimestamp(mktime_tz(parsedate_tz(date)))
                except:
                    logging.warn(str(e))
                    date = None
                title = unescape(item.getElementsByTagName("title")[0].firstChild.data)
                match = self.title_regex.search(title)
                if match is None:
                    logging.warn(u"%s is not well-formed for the regex" % title)
                    quality = []
                else:
                    quality = match.group(2).split(" - ")[:-1] # split and ignore the release group
                    
                enclosure = item.getElementsByTagName("enclosure")[0]
                torrentlen = int(enclosure.attributes["length"].value)
                season_nr = None
                try:
                    if "Season" in desc_dict:
                        season_nr = int(desc_dict["Season"])
                except ValueError:
                    pass
                episode_nr = None
                try:
                    if "Episode" in desc_dict:
                        episode_nr = int(desc_dict["Episode"])
                except ValueError:
                    pass
                release_items.append(ReleaseData(which="torrent", 
                                url=url, 
                                show_name=desc_dict["Show Name"],
                                episode_title=desc_dict["Episode Title"],
                                season_number=season_nr,
                                episode_number=episode_nr,
                                pub_date=date,
                                quality=quality,
                                torrentlen=torrentlen)
                                )
            except Exception, e:
                logging.warn(str(e))
                continue
        return release_items