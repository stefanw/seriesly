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
    
class SurfTheChannel(object):
    feed_url = "http://www.allnewtvshows.com/feed/"

    def get_info(self):
        """<item>
        		<title>Chuck Season 1 Episode 1 – Pilot</title>

        		<link>http://www.allnewtvshows.com/chuck/season-1-chuck/chuck-season-1-episode-1-%e2%80%93-pilot/</link>
        		<comments>http://www.allnewtvshows.com/chuck/season-1-chuck/chuck-season-1-episode-1-%e2%80%93-pilot/#comments</comments>
        		<pubDate>Thu, 14 Jan 2010 00:20:15 +0000</pubDate>
        		<dc:creator>TVGod</dc:creator>
        				<category><![CDATA[Season 1]]></category>

        		<guid isPermaLink="false">http://www.allnewtvshows.com/chuck/season-1-chuck/chuck-season-1-episode-1-%e2%80%93-pilot/</guid>

        		<description><![CDATA[
        Related TV ShowsNo Related Post]]></description>
        		<wfw:commentRss>http://www.allnewtvshows.com/chuck/season-1-chuck/chuck-season-1-episode-1-%e2%80%93-pilot/feed/</wfw:commentRss>
        		<slash:comments>0</slash:comments>
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
        rss_xml = rss_xml.replace("&hellip;","...")
        dom = parseString(rss_xml)
        items = dom.getElementsByTagName("item")
        release_items = []
        for item in items:
            try:
                url = item.getElementsByTagName("link")[0].firstChild.data
                desc = unescape(item.getElementsByTagName("description")[0].firstChild.data)
                desc = desc.replace("<pre>", "").replace("</pre>","")
                desc_dict = dict(map(lambda x: tuple(map(unicode.strip, x.split(":", 1))), [d for d in desc.split("<br />") if ":" in d])) # Don't ask
                date = None
                try:
                    title = desc_dict["Show"]
                except:
                    title = unescape(item.getElementsByTagName("title")[0].firstChild.data).split(" - ")[0]
                try:
                    season_nr = int(desc_dict["Season"])
                except:
                    season_nr = None
                try:
                    episode_nr = int(desc_dict["Episode"])
                except:
                    episode_nr = None
                
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
                logging.warn(desc + " - " + str(e))
                continue
        return release_items