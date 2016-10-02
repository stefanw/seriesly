

class BaseSeriesInfoProvider(object):
    def get_show(self, show_id):
        raise NotImplementedError

    def get_show_by_name(self, show_name):
        raise NotImplementedError
