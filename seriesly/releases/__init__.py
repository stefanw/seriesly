class ReleaseDataClass(object):
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        for k,v in kwargs.items():
            setattr(self, k, v)
            
    def __unicode__(self):
        return u"ReleaseData(**%s)" % unicode(self.kwargs)
    def __str__(self):
        return "ReleaseData(**%s)" % str(self.kwargs)

class ReleaseData(ReleaseDataClass):
    def __unicode__(self):
        return u"ReleaseData(**%s)" % unicode(self.kwargs)
    def __str__(self):
        return "ReleaseData(**%s)" % str(self.kwargs)
    __repr__ = __str__
