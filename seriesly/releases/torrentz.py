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
        

class Torrentz(object):
    feed_url = "http://www.torrentz.com/feedA?q=TV"
#    title_regex = re.compile("(.*?) ([0-9]{1,3})[xX]([0-9]{1,3}) \[([^\]]+)\]")
    title_regex = re.compile(r"^(.*?) ([Ss]\d+[Ee]\d+|[\d ]+)(.*?)HDTV(.*?)$")
# The League S02E03 The White Knuckler HDTV XviD FQM eztv    
    
    def get_info(self):
        """<item>
         <title>The Big Bang Theory S04E02 The Cruciferous Vegetable Amplification HDTV XviD FQM eztv</title> 
         <guid>http://www.torrentz.com/648fc0722a3822034c6e04b1d9fbb30c17d93e08</guid> 
         <pubDate>Fri, 01 Oct 2010 01:15:18 +0000</pubDate> 
         <category>tv divx xvid</category> 
         <description>Size: 175 Mb Seeds: 9,538 Peers: 9,745 Hash: 648fc0722a3822034c6e04b1d9fbb30c17d93e08</description> 
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
                url = item.getElementsByTagName("guid")[0].firstChild.data
                desc = unescape(item.getElementsByTagName("description")[0].firstChild.data)
                try:
                    date = item.getElementsByTagName("pubDate")[0].firstChild.data
                    date = datetime.datetime.fromtimestamp(mktime_tz(parsedate_tz(date)))
                except:
                    logging.warn(str(e))
                    date = None
                title = unescape(item.getElementsByTagName("title")[0].firstChild.data)
                match = self.title_regex.match(title)
                show_name = None
                episode_title = None
                if match is None:
                    logging.warn(u"%s is not well-formed for the regex" % title)
                    quality = []
                else:
                    show_name = match.group(1)
                    episode_title = match.group(3)
                    dateNumber = match.group(2).lower()
                    if dateNumber.startswith("s"):
                        try:
                            dateNumber = dateNumber[1:]
                            season_nr, episode_nr = map(int, dateNumber.split("e"))
                        except ValueError:
                            season_nr, episode_nr = None, None
                    else:
                        pass
                    quality = "HDTV "+match.group(4).strip()
                    quality.split(" ")[:-1]
                torrentlen = 0
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
    http_get = lambda x: """<?xml version="1.0"?> 
<rss version="2.0"> 
   <channel> 
      <title>Torrentz</title> 
      <link>http://www.torrentz.com/</link> 
      <description>TV search</description> 
      <language>en-us</language> 
      <item> 
         <title>CSI S11E02 720p HDTV X264 DIMENSION eztv</title> 
         <guid>http://www.torrentz.com/0a41b29d7d024769ebec16d957202aaed2948965</guid> 
         <pubDate>Fri, 01 Oct 2010 07:45:06 +0000</pubDate> 
         <category>tv</category> 
         <description>Size: 1119 Mb Seeds: 0 Peers: 0 Hash: 0a41b29d7d024769ebec16d957202aaed2948965</description> 
      </item> 
      <item> 
         <title>The League S02E03 The White Knuckler HDTV XviD FQM eztv</title> 
         <guid>http://www.torrentz.com/70e9c8dc2cd39da2deb399d6fd647a9de10bb778</guid> 
         <pubDate>Fri, 01 Oct 2010 07:45:05 +0000</pubDate> 
         <category>tv</category> 
         <description>Size: 174 Mb Seeds: 0 Peers: 0 Hash: 70e9c8dc2cd39da2deb399d6fd647a9de10bb778</description> 
      </item> 
      <item> 
         <title>Jay Leno 2010 09 29 Diane Lane HDTV XviD 2HD eztv</title> 
         <guid>http://www.torrentz.com/fe2c716154d437bfeedea78eb5cc648cc7635f3b</guid> 
         <pubDate>Fri, 01 Oct 2010 07:30:10 +0000</pubDate> 
         <category>tv</category> 
         <description>Size: 349 Mb Seeds: 0 Peers: 0 Hash: fe2c716154d437bfeedea78eb5cc648cc7635f3b</description> 
      </item> 
	</channel>
</rss>"""
    ezrss = Torrentz()
    print ezrss.get_info()
