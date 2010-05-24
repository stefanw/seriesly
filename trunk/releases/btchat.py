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

class BTChat(object):
    feed_url = "http://rss.bt-chat.com/?cat=9"
    title_regex = re.compile("^(.*?)\.[Ss]?([0-9]+)[EeXx]([0-9]+)\.(.*?)(?:-.*?|\..*?)\.torrent")

    def get_info(self):
        """<item>
               <title>Desperate.Housewives.S06E12.720p.HDTV.x264-IMMERSE.[eztv].torrent</title>
               <category>TV - EZTV</category>
        		<source url="http://www.bt-chat.com/rss.php?group=3">EZTV</source>
        		<description>http://www.bt-chat.com/details.php?id=69386</description>
               <guid isPermaLink="true">http://www.bt-chat.com/details.php?id=69386</guid>
               <link>http://www.bt-chat.com/download1.php?id=69386</link>
        		<pubDate>Mon, 11 Jan 2010 07:26:06 EST</pubDate>
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
                try:
                    date = item.getElementsByTagName("pubDate")[0].firstChild.data
                    date = datetime.datetime.fromtimestamp(mktime_tz(parsedate_tz(date)))
                except:
                    logging.warn(str(e))
                    date = None
                title = unescape(item.getElementsByTagName("title")[0].firstChild.data)
                match = self.title_regex.search(title)
                #(.*?)\.[Ss]([0-9]+)[Ee]([0-9]+)\.(.*?)-.*
                if match is not None:
                    show_name = match.group(1).replace(".", " ")
                    season_nr = int(match.group(2))
                    episode_nr = int(match.group(3))
                    quality = match.group(4).split(".")
                else:
                    logging.warn(u"%s is not well-formed for the regex" % title)
                    quality = []
                    season_nr = None
                    episode_nr = None
                    show_name = None
                torrentlen = None
                if show_name is not None:
                    release_items.append(ReleaseData(which="torrent", 
                                    url=url, 
                                    show_name=show_name,
                                    episode_title="",
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
#<option value="1">BTC</option><option value="13">ConCen</option><option value="220">d734</option><option value="3">EZTV</option><option value="229">FinalGear</option><option value="8">KiND</option><option value="219">MO</option><option value="4">MVG</option><option value="12">Public</option><option value="9">SDH</option><option value="5">SoS</option><option value="227">TC</option><option value="2">VTV</option></select>
class BTChatEZTV(BTChat):
    feed_url = "http://rss.bt-chat.com/?group=3&cat=9"

class BTChatVTV(BTChat):
    feed_url = "http://rss.bt-chat.com/?group=2&cat=9"