class Filter (object):
    def __init__(self, type, enabled):
        self.type = type
        self.enabled = enabled
        self.params = {}

    def load(self, params):
        keys = self.params.keys()
        keys.sort()
        if len(keys) != len(params):
            raise ValueError("Wrong number of parameters for constructor")
        for index, key in enumerate(keys):
            self.params[key] = params[index]

    def testString(self):
        s = ""
        if self.enabled:
            s += "( 1) "
        else:
            s += "(0 ) "
        s += self.type + "\n\t"
        s += "\n\t".join([": ".join([k, v]) for k, v in self.params.iteritems()])
        return s


class SubnetFilter(Filter):
    def __init__(self, enabled):
        Filter.__init__(self, "subnet", enabled)
        self.params['subnet'] = ""


class PortFilter(Filter):
    def __init__(self, enabled):
        Filter.__init__(self, "port", enabled)
        self.params['comparator'] = ""
        self.params['port'] = ""


class ConnectionsFilter(Filter):
    def __init__(self, enabled):
        Filter.__init__(self, "connections", enabled)
        self.params['comparator'] = ""
        self.params['limit'] = ""


class TagsFilter(Filter):
    def __init__(self, enabled):
        Filter.__init__(self, "tags", enabled)
        self.params['has'] = ""
        self.params['tags'] = ""


filterTypes = [SubnetFilter,PortFilter,ConnectionsFilter,TagsFilter]
filterTypes.sort(key=lambda x: str(x)) #sort classes by name

def readEncoded(filterString):
    filters = []
    for encodedFilter in filterString.split("|"):
        params = encodedFilter.split(";")
        typeIndex, enabled, params = params[0], params[1], params[2:]
        enabled = (enabled == "1") #convert to boolean
        filterClass = filterTypes[int(typeIndex)]
        f = filterClass(enabled)
        f.load(params)
        filters.append(f)
    for f in filters:
        print(f.testString())