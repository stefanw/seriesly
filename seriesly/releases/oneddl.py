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
        

class OneDDL(object):
    feed_url = "http://www.oneddl.com/category/tv-shows/feed/"
#    title_regex = re.compile("(.*?) ([0-9]{1,3})[xX]([0-9]{1,3}) \[([^\]]+)\]")
    title_regex = re.compile("(.*?)\.[sS]([0-9]+)[eE]([0-9]+)\.(.*)$")
    
    def get_info(self):
        """
        <item>
		<title>Lost.Girl.S01E11.HDTV.XviD-2HD</title>

		<link>http://www.oneddl.com/tv-shows/lost-girl-s01e11-hdtv-xvid-2hd/</link>
		<comments>http://www.oneddl.com/tv-shows/lost-girl-s01e11-hdtv-xvid-2hd/#comments</comments>
		<pubDate>Mon, 29 Nov 2010 07:12:48 +0000</pubDate>
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
                title = title.split(" & ")[0]
                match = self.title_regex.search(title)
                if match is None:
                    logging.warn(u"%s is not well-formed for the regex" % title)
                    continue
                else:
                    quality = match.group(4).split(".")
                    season_nr = int(match.group(2))
                    episode_nr = int(match.group(3))
                    title = match.group(1).replace(".", " ")                    
                release_items.append(ReleaseData(which="sharehoster", 
                                url=url,
                                show_name=title,
                                episode_title="",
                                season_number=season_nr,
                                episode_number=episode_nr,
                                pub_date=date,
                                quality=quality,
                                torrentlen=0)
                                )
            except Exception, e:
                logging.warn(str(e))
                continue
        return release_items
        
if __name__ == '__main__':
    http_get = lambda x: """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"
	xmlns:content="http://purl.org/rss/1.0/modules/content/"
	xmlns:wfw="http://wellformedweb.org/CommentAPI/"
	xmlns:dc="http://purl.org/dc/elements/1.1/"
	xmlns:atom="http://www.w3.org/2005/Atom"
	xmlns:sy="http://purl.org/rss/1.0/modules/syndication/"
	xmlns:slash="http://purl.org/rss/1.0/modules/slash/"
	>

<channel>
	<title>OneDDL - One Stop Rapidshare Links &#187; TV Shows</title>
	<atom:link href="http://www.oneddl.com/category/tv-shows/feed/" rel="self" type="application/rss+xml" />
	<link>http://www.oneddl.com</link>
	<description>Direct HTTP Downloads</description>
	<lastBuildDate>Mon, 29 Nov 2010 09:46:14 +0000</lastBuildDate>

	<language>en</language>
	<sy:updatePeriod>hourly</sy:updatePeriod>
	<sy:updateFrequency>1</sy:updateFrequency>
	<generator>http://wordpress.org/?v=3.0.1</generator>
		<item>
		<title>Lost.Girl.S01E11.HDTV.XviD-2HD</title>

		<link>http://www.oneddl.com/tv-shows/lost-girl-s01e11-hdtv-xvid-2hd/</link>
		<comments>http://www.oneddl.com/tv-shows/lost-girl-s01e11-hdtv-xvid-2hd/#comments</comments>
		<pubDate>Mon, 29 Nov 2010 07:12:48 +0000</pubDate>
		<dc:creator>Choppa</dc:creator>
				<category><![CDATA[1-Click]]></category>
		<category><![CDATA[HD 720p]]></category>
		<category><![CDATA[TV Shows]]></category>

		<category><![CDATA[Lost Girl]]></category>
		<category><![CDATA[S01]]></category>

		<guid isPermaLink="false">http://www.oneddl.com/?p=87661</guid>
		<description><![CDATA[Series Link Faetal Justice &#8211; When Dyson wakes up bloody and without the last eight hours of memory, he finds himself accused of murdering Ba&#8217;al, a close associate of The Morrigan&#8217;s pet psychopath, Vex, and takes refuge in Trick&#8217;s bar, invoking sanctuary. Rapidshare http://88288.oneddl.canhaz.it/ Hotfile http://88291.oneddl.canhaz.it/ FileServe http://88290.oneddl.canhaz.it/ Netload http://88289.oneddl.canhaz.it/ HD Release Rapidshare Uploading&#8230; Hotfile [...]]]></description>
			<content:encoded><![CDATA[<p align="center"><img class="alignnone" title="Lost Girl" src="http://images.oneddl.com/images/uhp625ken5burxgqpfh8.png" alt="Lost Girl" /></p>
<p align="center"><a href="http://www.oneddl.com/?tag=Lost-Girl+s01">Series Link</a></p>
<p><infoimg /></p>
<p><strong>Faetal Justice</strong> &#8211; When Dyson wakes up bloody and without the last eight hours of memory, he finds himself accused of murdering Ba&#8217;al, a close associate of The Morrigan&#8217;s pet psychopath, Vex, and takes refuge in Trick&#8217;s bar, invoking sanctuary.</p>
<p align="center"><span id="more-87661"></span></p>
<p><oneclickimg /></p>
<p><strong>Rapidshare</strong><br />
<a href="http://88288.oneddl.canhaz.it/">http://88288.oneddl.canhaz.it/</a></p>
<p><strong>Hotfile</strong><br />
<a href="http://88291.oneddl.canhaz.it/">http://88291.oneddl.canhaz.it/</a></p>
<p><strong>FileServe</strong><br />
<a href="http://88290.oneddl.canhaz.it/">http://88290.oneddl.canhaz.it/</a></p>
<p><strong>Netload</strong><br />
<a href="http://88289.oneddl.canhaz.it/">http://88289.oneddl.canhaz.it/</a></p>
<hr />
<strong>HD Release</strong></p>
<p><oneclickimg /></p>
<p><strong>Rapidshare</strong><br />
Uploading&#8230;</p>
<p><strong>Hotfile</strong><br />
Uploading&#8230;</p>
<p><downloadimg /></p>
<p><strong>Rapidshare (400mb Links)</strong><br />
Uploading&#8230;</p>
<p><strong>FileServe (Interchangeable)</strong><br />
Uploading&#8230;</p>
]]></content:encoded>
			<wfw:commentRss>http://www.oneddl.com/tv-shows/lost-girl-s01e11-hdtv-xvid-2hd/feed/</wfw:commentRss>
		<slash:comments>0</slash:comments>

		</item>
		<item>
		<title>National.Geographic.Inside.Afghan.Marine.Base.HDTV.XviD-ViLD</title>
		<link>http://www.oneddl.com/tv-shows/national-geographic-inside-afghan-marine-base-hdtv-xvid-vild/</link>
		<comments>http://www.oneddl.com/tv-shows/national-geographic-inside-afghan-marine-base-hdtv-xvid-vild/#comments</comments>
		<pubDate>Mon, 29 Nov 2010 06:27:47 +0000</pubDate>
		<dc:creator>.:H@$EEB:.</dc:creator>

				<category><![CDATA[1-Click]]></category>
		<category><![CDATA[TV Shows]]></category>
		<category><![CDATA[Inside Afghan Marine Base]]></category>
		<category><![CDATA[National Geographic]]></category>

		<guid isPermaLink="false">http://www.oneddl.com/?p=87654</guid>
		<description><![CDATA[Series Link National Geographic &#8211; Inside Afghan Marine Base Rapidshare http://rapidshare.com/files/433801920/OneDDL.com-vild-national.geographic.inside.afghan.marine.base.hdtv.xvid.avi Hotfile http://hotfile.com/dl/85687457/3a6b85f/OneDDL.com-vild-national.geographic.inside.afghan.marine.base.hdtv.xvid.avi.html FileServe http://www.fileserve.com/file/BY2qdaV/OneDDL.com-vild-national.geographic.inside.afghan.marine.base.hdtv.xvid.avi]]></description>

			<wfw:commentRss>http://www.oneddl.com/tv-shows/national-geographic-inside-afghan-marine-base-hdtv-xvid-vild/feed/</wfw:commentRss>

		<slash:comments>0</slash:comments>
<enclosure url="http://rapidshare.com/files/433801920/OneDDL.com-vild-national.geographic.inside.afghan.marine.base.hdtv.xvid.avi" length="366581760" type="video/avi" />
<enclosure url="http://www.fileserve.com/file/BY2qdaV/OneDDL.com-vild-national.geographic.inside.afghan.marine.base.hdtv.xvid.avi" length="0" type="video/avi" />
		</item>
		<item>
		<title>Top.Gear.US.S01E02.Blind.Drift.HDTV.XviD-FQM &amp; Top.Gear.US.S01E02.720p.HDTV.x264-ORENJI</title>
		<link>http://www.oneddl.com/tv-shows/top-gear-us-s01e02-blind-drift-hdtv-xvid-fqm/</link>
		<comments>http://www.oneddl.com/tv-shows/top-gear-us-s01e02-blind-drift-hdtv-xvid-fqm/#comments</comments>

		<pubDate>Mon, 29 Nov 2010 04:24:34 +0000</pubDate>
		<dc:creator>Choppa</dc:creator>
				<category><![CDATA[1-Click]]></category>
		<category><![CDATA[HD 720p]]></category>
		<category><![CDATA[TV Shows]]></category>
		<category><![CDATA[S01]]></category>
		<category><![CDATA[Top Gear US]]></category>

		<guid isPermaLink="false">http://www.oneddl.com/?p=87640</guid>
		<description><![CDATA[Series Link Blind Drift &#8211; Tanner races his favorite cut price sports car against two extreme skiers down a mountain. Rutledge finds out if Aston Martin has solved a horsepower problem in the new Vantage model and Adam and Rutledge try to beat professional drift champion Tanner Foust in a drifting competition by cheating. Actor [...]]]></description>
			<wfw:commentRss>http://www.oneddl.com/tv-shows/top-gear-us-s01e02-blind-drift-hdtv-xvid-fqm/feed/</wfw:commentRss>
		<slash:comments>1</slash:comments>
		</item>
	</channel>
</rss>"""
    provider = OneDDL()
    print provider.get_info()