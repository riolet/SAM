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

    def where(self):
        raise NotImplemented("This method must be overridden in the ({0}) class.".format(self.type))


class SubnetFilter(Filter):
    def __init__(self, enabled):
        Filter.__init__(self, "subnet", enabled)
        self.params['subnet'] = ""

    def where(self):
        subnet = int(self.params['subnet'])
        valid_subnets = [8, 16, 24, 32]
        if subnet not in valid_subnets:
            raise ValueError("Subnet is not valid. ({net} not in {valid})".format(net=subnet, valid=valid_subnets))

        return "nodes.subnet = {0}".format(subnet)


class PortFilter(Filter):
    def __init__(self, enabled):
        Filter.__init__(self, "port", enabled)
        self.params['connection'] = ""
        self.params['port'] = ""
        # connections: 0, 1, 2, 3
        # 0: connects to port n
        # 1: doesn't connect to port n
        # 2: receives connection from port n
        # 3: doesn't receive connection from port n

    def where(self):
        if self.params['connection'] == 0:
            return "EXISTS (SELECT * FROM LinksA WHERE LinksA.port = '{0}' && LinksA.dst BETWEEN nodes.ipstart AND nodes.ipend)".format(int(self.params['port']))
        elif self.params['connection'] == 1:
            return "NOT EXISTS (SELECT * FROM LinksA WHERE LinksA.port = '{0}' && LinksA.dst BETWEEN nodes.ipstart AND nodes.ipend)".format(int(self.params['port']))
        elif self.params['connection'] == 2:
            return "EXISTS (SELECT * FROM LinksA WHERE LinksA.port = '{0}' && LinksA.src BETWEEN nodes.ipstart AND nodes.ipend)".format(int(self.params['port']))
        elif self.params['connection'] == 3:
            return "NOT EXISTS (SELECT * FROM LinksA WHERE LinksA.port = '{0}' && LinksA.src BETWEEN nodes.ipstart AND nodes.ipend)".format(int(self.params['port']))
        return ""


class ConnectionsFilter(Filter):
    def __init__(self, enabled):
        Filter.__init__(self, "connections", enabled)
        self.params['comparator'] = ""
        self.params['limit'] = ""

    def where(self):
        return ""


class TagsFilter(Filter):
    def __init__(self, enabled):
        Filter.__init__(self, "tags", enabled)
        self.params['has'] = ""
        self.params['tags'] = ""

    def where(self):
        return ""

class QueryBuilder (object):
    def __init__(self, filterArray):
        self.filters = filterArray


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
    return filters