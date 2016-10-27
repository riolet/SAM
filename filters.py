
class Filter (object):
    def __init__(self, type, enabled):
        self.type = type
        self.enabled = enabled
        self.params = {}


def readEncoded(self, filterString):
    filters = []
    for encodedFilter in filterString.split("|"):
        params = encodedFilter.split(";")
        typeIndex, enabled, params = params[0], params[1], params[2:]
        typeNames = self.filterFormat.keys().sort()
        type = typeNames[typeIndex]