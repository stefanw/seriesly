import importlib
from django.conf import settings


def get_provider(name=None, **kwargs):
    if name is None:
        name = getattr(settings, 'SERIES_INFO_PROVIDER', 'tvmaze')
    mod = importlib.import_module('.' + name, 'seriesly.series.providers')
    return mod.get_provider(**kwargs)
