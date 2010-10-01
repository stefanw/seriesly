#-*-coding:utf-8-*-
import logging
from xml.dom.minidom import parseString
import datetime
from email.utils import parsedate_tz, mktime_tz
import urllib
import re

if __name__ == '__main__':
    import sys
    sys.path.insert(0,"/Users/sw/Sites/seriesly/seriesly")

from pytz import timezone

from helper.http import get as http_get
from helper.html import unescape

from releases import ReleaseData
        

class EZTVPipe(object):
    feed_url = "pipes.yahoo.com/pipes/pipe.run?_id=3dc789adfc63c9360eb76c0edfec2184&_render=rss"
#    title_regex = re.compile("(.*?) ([0-9]{1,3})[xX]([0-9]{1,3}) \[([^\]]+)\]")
    # title_regex = re.compile("(.*?) \[([^\]]+)\]")
    title_regex = re.compile(r"^(.*?) ([Ss]\d+[Ee]\d+|[\d ]+|\d+[xX]\d+)(.*?)$")
    
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
                desc = item.getElementsByTagName("description")[0].firstChild.data.strip()
                days, hours, minutes, seconds = 0, 0, 0, 0
                for d in desc.split(" "):
                    if d[0] == "d":
                        days = int(d[1])
                    if d[0] == "h":
                        hours = int(d[1])
                    if d[0] == "m":
                        minutes = int(d[1])
                    if d[0] == "s":
                        seconds = int(d[1])
                ago = datetime.timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
                date = datetime.datetime.now() - ago
                title = unescape(item.getElementsByTagName("title")[0].firstChild.data)
                match = self.title_regex.search(title)
                show_name = None
                episode_title = None
                season_nr, episode_nr = None, None

                if match is None:
                    logging.warn(u"%s is not well-formed for the regex" % title)
                    quality = []
                else:
                    show_name = match.group(1)
                    show_name = show_name.replace("HDTV", "").strip()
                    dateNumber = match.group(2).lower()
                    if dateNumber.startswith("s"):
                        try:
                            dateNumber = dateNumber[1:]
                            season_nr, episode_nr = map(int, dateNumber.split("e"))
                        except ValueError:
                            season_nr, episode_nr = None, None
                    elif "x" in dateNumber:
                        try:
                            season_nr, episode_nr = map(int, dateNumber.split("x"))
                        except ValueError:
                            season_nr, episode_nr = None, None
                    else:
                        pass
                    quality = match.group(3).strip()
                    quality.split(" ")[:-1]
                    
                torrentlen = 0
                if season_nr is None:
                    continue
                release_items.append(ReleaseData(which="torrent", 
                                url=url, 
                                show_name=show_name,
                                episode_title=episode_title,
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
        
if __name__ == '__main__':
    http_get = lambda x: """
<?xml version="1.0"?> 
<rss version="2.0" xmlns:geo="http://www.w3.org/2003/01/geo/wgs84_pos#" xmlns:content="http://purl.org/rss/1.0/modules/content/" xmlns:media="http://search.yahoo.com/mrss/" xmlns:yt="http://gdata.youtube.com/schemas/2007"> 
   <channel> 
      <title>EZTV Pipe</title> 
      <description>Pipes Output</description> 
      <link>http://pipes.yahoo.com/pipes/pipe.info?_id=3dc789adfc63c9360eb76c0edfec2184</link> 
      <pubDate>Fri, 01 Oct 2010 19:09:22 +0000</pubDate> 
      <generator>http://pipes.yahoo.com/pipes/</generator> 
      <item> 
         <title>BBC Climbing Great Buildings 09of15 Clifton Suspension Bridge x264 AC3 HDTV-MVGroup</title> 
         <link>http://forums.mvgroup.org/torrents/BBC.Climbing.Great.Buildings.09of15.Clifton.Suspension.Bridge.HDTV.x264.AC3.MVGroup.org.mkv.torrent</link> 
         <guid isPermaLink="false">3dc789adfc63c9360eb76c0edfec2184_988faec20d0239289d590f6f3ed2843b</guid> 
      </item> 
		</item>
	</channel>
</rss>"""
    ezrss = EZRSS()
    print ezrss.get_info()
