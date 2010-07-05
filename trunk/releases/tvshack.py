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
    
class TVShack(object):
    feed_url = "http://tvshack.cc/rss/television.xml"
    title_regex = re.compile("(.*?) - [Ss]([0-9]{1,3})[Ee]([0-9]{1,3})")
    def get_info(self):
        """<item>
            <title>King of the Hill - S7E13</title>
            <link>http://tvshack.cc/tv/King_of_the_Hill/season_7/episode_13/</link>
            <description>After going to couples&#x2019; therapy, Hank and Peggy realize that they need some excitement in their life -- a motorcycle. Hank enjoys driving the bike, but when Peggy wants to drive it, he is hesitant to give her the front seat for the sake of manliness.</description>
            <pubDate>Fri, 01 Jan 2010 18:17:12 +0000</pubDate>
            <guid isPermaLink="true">http://tvshack.cc/tv/King_of_the_Hill/season_7/episode_13/</guid>
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
                    continue
                title = match.group(1)
                season_nr = int(match.group(2))
                episode_nr = int(match.group(3))
                
                release_items.append(ReleaseData(which="stream", 
                                url=url, 
                                show_name=title,
                                episode_title="",
                                season_number=season_nr,
                                episode_number=episode_nr,
                                pub_date=date,
                                quality=["Stream"],
                                torrentlen=0)
                                )
            except Exception, e:
                logging.warn(str(e))
                continue
        return release_items