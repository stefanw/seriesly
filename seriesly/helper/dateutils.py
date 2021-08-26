from pytz import timezone


def get_timezone_for_gmt_offset(gmtoffset):
    if "GMT-5" in gmtoffset:
        return timezone("US/Eastern")
    elif "GMT-8" in gmtoffset:
        return timezone("US/Pacific")
    elif "GMT+0" in gmtoffset:
        return timezone("Europe/London")
    else:
        return timezone("US/Eastern")
