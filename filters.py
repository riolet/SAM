import common


class Filter (object):
    def __init__(self, f_type, enabled):
        self.type = f_type
        self.enabled = enabled
        self.params = {}

    def load(self, params):
        keys = self.params.keys()
        keys.sort()
        if len(keys) != len(params):
            print("Wrong number of parameters for constructor")
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

    def having(self):
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

    def having(self):
        return ""


class MaskFilter(Filter):
    def __init__(self, enabled):
        Filter.__init__(self, "mask", enabled)
        self.params['mask'] = ""

    def where(self):
        r = common.determine_range_string(self.params['mask'])
        return "nodes.ipstart BETWEEN {0} AND {1}".format(r[0], r[1])

    def having(self):
        return ""


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
        if self.params['connection'] == '0':
            return "EXISTS (SELECT port FROM LinksOut WHERE LinksOut.port = '{0}' && LinksOut.src_start = nodes.ipstart && LinksOut.src_end = nodes.ipend)".format(int(self.params['port']))
        elif self.params['connection'] == '1':
            return "NOT EXISTS (SELECT port FROM LinksOut WHERE LinksOut.port = '{0}' && LinksOut.src_start = nodes.ipstart && LinksOut.src_end = nodes.ipend)".format(int(self.params['port']))

        elif self.params['connection'] == '2':
            return "EXISTS (SELECT port FROM LinksIn WHERE LinksIn.port = '{0}' && LinksIn.dst_start = nodes.ipstart && LinksIn.dst_end = nodes.ipend)".format(int(self.params['port']))
        elif self.params['connection'] == '3':
            return "NOT EXISTS (SELECT port FROM LinksIn WHERE LinksIn.port = '{0}' && LinksIn.dst_start = nodes.ipstart && LinksIn.dst_end = nodes.ipend)".format(int(self.params['port']))
        else:
            print ("Warning: no match for connection parameter of PortFilter when building WHERE clause. "
                   "({0}, type: {1})".format(self.params['connection'], type(self.params['connection'])))
        return ""

    def having(self):
        return ""


class ConnectionsFilter(Filter):
    def __init__(self, enabled):
        Filter.__init__(self, "connections", enabled)
        self.params['comparator'] = ""
        self.params['direction'] = ""
        self.params['limit'] = ""

    def where(self):
        return ""

    def having(self):
        HAVING = ""
        if self.params['comparator'] not in ['=', '<', '>']:
            return ""
        limit = int(self.params['limit'])
        if self.params['direction'] == "i":
            src = "conn_in"
        else:
            src = "conn_out"

        HAVING += "{src} {comparator} '{limit}'".format(src=src, comparator=self.params['comparator'], limit=limit)
        return HAVING


class TargetFilter(Filter):
    def __init__(self, enabled):
        Filter.__init__(self, "target", enabled)
        self.params['target'] = ""
        self.params['to'] = ""

    def where(self):
        # ip_segments = [int(x) for x in self.params['target'].split(".")]
        # target = common.IPtoInt(*ip_segments)
        r = common.determine_range_string(self.params['target'])
        if self.params['to'] == '0':
            return "EXISTS (SELECT 1 FROM Links WHERE Links.dst BETWEEN {lower} AND {upper} AND Links.src = nodes.ipstart)".format(lower=r[0], upper=r[1])
        elif self.params['to'] == '1':
            return "NOT EXISTS (SELECT 1 FROM Links WHERE Links.dst BETWEEN {lower} AND {upper} AND Links.src = nodes.ipstart)".format(lower=r[0], upper=r[1])
        
        if self.params['to'] == '2':
            return "EXISTS (SELECT 1 FROM Links WHERE Links.src BETWEEN {lower} AND {upper} AND Links.dst = nodes.ipstart)".format(lower=r[0], upper=r[1])
        elif self.params['to'] == '3':
            return "NOT EXISTS (SELECT 1 FROM Links WHERE Links.src BETWEEN {lower} AND {upper} AND Links.dst = nodes.ipstart)".format(lower=r[0], upper=r[1])

        else:
            print ("Warning: no match for 'to' parameter of TargetFilter when building WHERE clause. "
                   "({0}, type: {1})".format(self.params['to'], type(self.params['to'])))
        return ""

    def having(self):
        return ""


class TagsFilter(Filter):
    def __init__(self, enabled):
        Filter.__init__(self, "tags", enabled)
        self.params['has'] = ""
        self.params['tags'] = ""

    def where(self):
        tags = str(self.params['tags']).split(",")
        phrase = "EXISTS (SELECT 1 FROM Tags WHERE tag={0} AND Tags.ipstart <= nodes.ipstart AND Tags.ipend >= nodes.ipend)"
        if self.params['has'] != '1':
            phrase = "NOT " + phrase
        return "\n AND ".join([phrase.format(common.web.sqlquote(tag)) for tag in tags])

    def having(self):
        return ""


class RoleFilter(Filter):
    def __init__(self, enabled):
        Filter.__init__(self, "role", enabled)
        self.params['ratio'] = ""
        self.params['comparator'] = ""

    def where(self):
        return ""

    def having(self):
        cmp = self.params['comparator']
        if cmp not in ['<', '>']:
            cmp = '<'
        ratio = float(self.params['ratio'])
        return "(conn_in / (conn_in + conn_out)) {0} {1:.4f}".format(cmp, ratio)


filterTypes = [SubnetFilter,PortFilter,ConnectionsFilter,TagsFilter,MaskFilter,TargetFilter,RoleFilter]
filterTypes.sort(key=lambda x: str(x)) #sort classes by name


def readEncoded(filterString):
    filters = []
    for encodedFilter in filterString.split("|"):
        try:
            params = encodedFilter.split(";")
            typeIndex, enabled, params = params[0], params[1], params[2:]
            enabled = (enabled == "1") #convert to boolean
            filterClass = filterTypes[int(typeIndex)]
            f = filterClass(enabled)
            f.load(params)
            filters.append(f)
        except:
            print("ERROR: unable to decode filter: " + encodedFilter)
    return filters