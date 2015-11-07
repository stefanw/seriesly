from google.appengine.api.urlfetch import fetch
import datetime


class TVRageFetcher(object):
    url = "http://www.tvrage.com/quickinfo.php?show=%(name)s&ep=%(season)dx%(episode)d"

    def __init__(self, show):
        self.show = show
        # TODO Add: filter("date >", today)
        self.last_episode = Episode.all().filter("show =", self.show.key()).order('-date').get()
        if last_episode is None:
            self.season_nr = 1
            self.episode_nr = 1
        else:
            self.season_nr = last_episode.season.number
            self.episode_nr = last_episode.number + 1

    def __iter__(self):
        return self

    def next(self):
        season_nr = self.season_nr
        episode_nr = self.episode_nr
        jumped_season = False
        while True:
            response = fetch(self.url % {"name": self.show.name, "season": season_nr, "episode": episode_nr})
            if response.status_code != 200:
                return
            info_dict = self.get_dict(response.content.split("\n"))
            if "Episode Info" not in info_dict and not jumped_season:
                jumped_season = True
                season_nr += 1
                episode_nr = 1
                continue
            elif "Episode Info" not in info_dict and jumped_season:
                return
            else:
                jumped_season = False
            season_nr = self.convert_seapisode(info_dict["Episode Info"][0])[0]
            episode_nr = self.convert_seapisode(info_dict["Episode Info"][0])[1]

            yield {
                "network": info_dict["Network"],
                "active": self.get_status(info_dict["Status"]),
                "country": info_dict["Country"],
                "runtime": int(info_dict["Runtime"])
            }, {
                "show": self.show,
                "number": season_nr,
                "start": self.get_start_date(info_dict),
                "end": self.get_start_date(info_dict)
            }, {
                "show": self.show,
                "number": episode_nr,
                "title": info_dict["Episode Info"][1],
                "date": self.get_start_date(info_dict)
            }

            if self.seapisode(info_dict["Latest Episode"][0]) == (season_nr, episode_nr):
                return
            episode_nr += 1
    __next__ = next

    def get_start_date(self, info):
        d = self.convert_datestring(info["Episode Info"][2])
        if "Airtime" in info:
            splits = info["Airtime"].split(" at ")  # Tuesday at 09:00 pm
            if len(splits) == 1:
                airtime = splits[0]
            else:
                airtime = splits[1]
            timeampm = airtime[1].split(" ")
            times = timeampm[0].split(":")
            if timeampm[1] == "pm":
                times[0] = int(times[0]) + 12
            td = datetime.timedelta(hours=int(times[0]), minutes=int(times[1]))
            d = d + td
        return d

    def get_status(self, status):
        status = status.lower()
        if "ended" in status or "canceled" in status:
            return False
        return True

    def convert_datestring(self, date_str):
        return datetime.datetime.strptime(date_str, "%b/%d/%Y")

    def convert_seapisode(self, seapisode_str):
        seapisode = seapisode_str.split("x")
        return (int(seapisode[0]), int(seapisode[1]))

    def get_dict(self, content):
        """Show Name@Alias
        Show URL@http://www.tvrage.com/Alias
        Premiered@2001
        Episode Info@02x04^Dead Drop^20/Oct/2002
        Episode URL@http://www.tvrage.com/Alias/episodes/4902
        Latest Episode@05x17^All the Time in the World^May/22/2006
        Country@USA
        Status@Canceled/Ended
        Classification@Scripted
        Genres@Action | Adventure | Drama
        Network@ABC
        Runtime@60


        Show Name@Lost
        Show URL@http://www.tvrage.com/Lost
        Premiered@2004
        Latest Episode@05x17^The Incident (2)^May/13/2009
        Next Episode@06x01^LA X (1)^Feb/02/2010
        RFC3339@2010-02-02T21:00:00-5:00
        Country@USA
        Status@Final Season
        Classification@Scripted
        Genres@Action | Adventure | Drama | Mystery
        Network@ABC
        Airtime@Tuesday at 09:00 pm
        Runtime@60"""
        info_dict = {}
        for line in content:
            line = line.strip()
            key, value = line.split("@", 1)
            if "^" in value:
                value = tuple(value.split("^"))
            info_dict[key] = value
        return info_dict
