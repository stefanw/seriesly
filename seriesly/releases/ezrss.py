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
        

class EZRSS(object):
    feed_url = "http://ezrss.it/search/index.php?show_name=%25&date=&quality=&release_group=&mode=rss"
#    title_regex = re.compile("(.*?) ([0-9]{1,3})[xX]([0-9]{1,3}) \[([^\]]+)\]")
    title_regex = re.compile("(.*?) \[([^\]]+)\]")
    
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
        
if __name__ == '__main__':
    http_get = lambda x: """<rss version="2.0">
	<channel>
		<title>ezRSS - Search Results</title>
		<ttl>15</ttl>
		<link>http://ezrss.it/search/index.php</link>
		<image>
			<title>ezRSS - Search Results</title>

			<url>http://ezrss.it/images/ezrssit.png</url>
			<link>http://ezrss.it/search/index.php</link>
		</image>
		<description>Custom RSS feed based off search filters.</description>
		<item>
			<title><![CDATA[Penn & Teller: Bullshit! 8x7 [HDTV - SYS]]]></title>
			<link>http://torrent.zoink.it/Penn.and.Teller.Bullshit.S08E07.HDTV.XviD-SYS.[eztv].torrent</link>

			<category domain="http://eztv.it/shows/211/penn-and-teller-bullshit/"><![CDATA[TV Show / Penn And Teller: Bullshit!]]></category>
			<pubDate>Thu, 22 Jul 2010 22:46:16 -0500</pubDate>
			<description><![CDATA[Show Name: Penn & Teller: Bullshit!; Episode Title: N/A; Season: 8; Episode: 7]]></description>
			<enclosure url="http://torrent.zoink.it/Penn.and.Teller.Bullshit.S08E07.HDTV.XviD-SYS.[eztv].torrent" length="244353024" type="application/x-bittorrent" />
			<comments>http://eztv.it/forum/discuss/21595/</comments>
			<guid>http://eztv.it/ep/21595/penn-and-teller-bullshit-s08e07-hdtv-xvid-sys/</guid>
		</item>

		<item>
			<title><![CDATA[Boston Med 1x5 [HDTV - 2HD]]]></title>
			<link>http://torrent.zoink.it/Boston.Med.S01E05.HDTV.XviD-2HD.[eztv].torrent</link>
			<category><![CDATA[TV Show]]></category>
			<pubDate>Thu, 22 Jul 2010 22:17:15 -0500</pubDate>
			<description><![CDATA[Show Name: Boston Med; Episode Title: N/A; Season: 1; Episode: 5]]></description>
			<enclosure url="http://torrent.zoink.it/Boston.Med.S01E05.HDTV.XviD-2HD.[eztv].torrent" length="366965376" type="application/x-bittorrent" />
			<comments>http://eztv.it/forum/discuss/21594/</comments>

			<guid>http://eztv.it/ep/21594/boston-med-s01e05-hdtv-xvid-2hd/</guid>
		</item>
	</channel>
</rss>"""
    ezrss = EZRSS()
    print ezrss.get_info()
