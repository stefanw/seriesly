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
        

class PirateBayEZ(object):
    feed_url = "http://rss.thepiratebay.org/user/d17c6a45441ce0bc0c057f19057f95e1"
#    title_regex = re.compile("(.*?) ([0-9]{1,3})[xX]([0-9]{1,3}) \[([^\]]+)\]")
    title_regex = re.compile("(.+?) [sS]?([0-9]+)[eExX]([0-9]+) (.+?)-[^-]+?$")
    title_regex2 = re.compile("(.+?) (\d{4}) (\d{2}) (\d{2}) (.+?) (.{,2}TV .+?)$") # Craig Ferguson 2010 05 18 Jon Favreau HDTV XviD-2HD [eztv]
    
    def get_info(self):
        """<item>
			<title>Mercy S01E11 Were All Adults PROPER HDTV XviD-FQM [eztv]</title>
			<link>http://torrents.thepiratebay.org/5279904/Mercy_S01E11_Were_All_Adults_PROPER_HDTV_XviD-FQM_[eztv].5279904.TPB.torrent</link>

			<comments>http://thepiratebay.org/torrent/5279904</comments>
			<pubDate>Thu, 14 Jan 2010 21:26:44 +0100</pubDate>
			<category domain="http://thepiratebay.org/browse/205">Video / TV shows</category>
			<dc:creator>eztv</dc:creator>
			<guid>http://thepiratebay.org/torrent/5279904/</guid>
			<enclosure url="http://torrents.thepiratebay.org/5279904/Mercy_S01E11_Were_All_Adults_PROPER_HDTV_XviD-FQM_[eztv].5279904.TPB.torrent" length="" type="application/x-bittorrent" />

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
                #(.+?) [sS]?([0-9]+)[eExX]([0-9]+) (.+?)-[^-]+?$
                if match is not None:
                    show_name = match.group(1)
                    season_nr = int(match.group(2))
                    episode_nr = int(match.group(3))
                    quality = match.group(4).split(" ")
                else:
                    logging.warn(u"%s is not well-formed for the regex" % title)
                    quality = []
                    season_nr = None
                    episode_nr = None
                    show_name = None
                enclosure = item.getElementsByTagName("enclosure")[0]
                try:
                    torrentlen = int(enclosure.attributes["length"].value)
                except ValueError:
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