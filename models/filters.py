import common
import re


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
            return "EXISTS (SELECT port FROM {{table_links_out}} AS `lo` WHERE lo.port = '{0}' && lo.src_start = nodes.ipstart && lo.src_end = nodes.ipend)".format(int(self.params['port']))
        elif self.params['connection'] == '1':
            return "NOT EXISTS (SELECT port FROM {{table_links_out}} AS `lo` WHERE lo.port = '{0}' && lo.src_start = nodes.ipstart && lo.src_end = nodes.ipend)".format(int(self.params['port']))

        elif self.params['connection'] == '2':
            return "EXISTS (SELECT port FROM {{table_links_in}} AS `li` WHERE li.port = '{0}' && li.dst_start = nodes.ipstart && li.dst_end = nodes.ipend)".format(int(self.params['port']))
        elif self.params['connection'] == '3':
            return "NOT EXISTS (SELECT port FROM {{table_links_in}} AS `li` WHERE li.port = '{0}' && li.dst_start = nodes.ipstart && li.dst_end = nodes.ipend)".format(int(self.params['port']))
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
        if self.params['comparator'] not in ['<', '>']:
            return ""
        limit = float(self.params['limit'])
        if self.params['direction'] == 'i':
            src = "conn_in / seconds"
            HAVING += "{src} {comparator} '{limit}'".format(src=src, comparator=self.params['comparator'], limit=limit)
        elif self.params['direction'] == 'o':
            src = "conn_out / seconds"
            HAVING += "{src} {comparator} '{limit}'".format(src=src, comparator=self.params['comparator'], limit=limit)
        elif self.params['direction'] == 'c':
            src = "(conn_in + conn_out) / seconds"
            HAVING += "{src} {comparator} '{limit}'".format(src=src, comparator=self.params['comparator'], limit=limit)
        else:
            return ""
        return HAVING


class TargetFilter(Filter):
    def __init__(self, enabled):
        Filter.__init__(self, "target", enabled)
        self.params['target'] = ""
        self.params['to'] = ""
        # for variable `to`:
        #   0: hosts connect to target
        #   1: hosts do NOT connect to target
        #   2: hosts receive connections from target
        #   3: hosts do NOT receive connections from target

    def where(self):
        ipstart, ipend = common.determine_range_string(self.params['target'])
        if self.params['to'] == '0':
            return "EXISTS (SELECT 1 FROM {{table_links}} AS `l` WHERE l.dst BETWEEN {lower} AND {upper} " \
                   "AND l.src BETWEEN nodes.ipstart AND nodes.ipend)".format(lower=ipstart, upper=ipend)
        elif self.params['to'] == '1':
            return "NOT EXISTS (SELECT 1 FROM {{table_links}} AS `l` WHERE l.dst BETWEEN {lower} AND {upper} " \
                   "AND l.src BETWEEN nodes.ipstart AND nodes.ipend)".format(lower=ipstart, upper=ipend)
        
        if self.params['to'] == '2':
            return "EXISTS (SELECT 1 FROM {{table_links}} AS `l` WHERE l.src BETWEEN {lower} AND {upper} " \
                   "AND l.dst BETWEEN nodes.ipstart AND nodes.ipend)".format(lower=ipstart, upper=ipend)
        elif self.params['to'] == '3':
            return "NOT EXISTS (SELECT 1 FROM {{table_links}} AS `l` WHERE l.src BETWEEN {lower} AND {upper} " \
                   "AND l.dst BETWEEN nodes.ipstart AND nodes.ipend)".format(lower=ipstart, upper=ipend)
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
        phrase = "EXISTS (SELECT 1 FROM {{table_tags}} AS `f_tags` WHERE tag={0} AND f_tags.ipstart <= nodes.ipstart AND f_tags.ipend >= nodes.ipend)"
        if self.params['has'] != '1':
            phrase = "NOT " + phrase
        return "\n AND ".join([phrase.format(common.web.sqlquote(tag)) for tag in tags])

    def having(self):
        return ""


class EnvFilter(Filter):
    def __init__(self, enabled):
        Filter.__init__(self, "env", enabled)
        self.params['env'] = ""

    def where(self):
        return ""

    def having(self):
        env = self.params['env']
        return "env = {0}".format(common.web.sqlquote(env))


class RoleFilter(Filter):
    def __init__(self, enabled):
        Filter.__init__(self, "role", enabled)
        self.params['comparator'] = ""
        self.params['ratio'] = ""

    def where(self):
        return ""

    def having(self):
        cmp = self.params['comparator']
        if cmp not in ['<', '>']:
            cmp = '<'
        ratio = float(self.params['ratio'])
        return "(conn_in / (conn_in + conn_out)) {0} {1:.4f}".format(cmp, ratio)


class ProtocolFilter(Filter):
    def __init__(self, enabled):
        Filter.__init__(self, "protocol", enabled)
        self.params['handles'] = ""
        self.params['protocol'] = ""

    def where(self):
        return ""

    def having(self):
        handles = '0'
        if self.params['handles'] in ['0', '1', '2', '3']:
            handles = self.params['handles']
        protocol = common.web.sqlquote("%" + self.params['protocol'] + "%")

        if handles == '0':
            return "proto_in LIKE {protocol}".format(protocol=protocol)
        if handles == '1':
            return "proto_in NOT LIKE {protocol}".format(protocol=protocol)
        if handles == '2':
            return "proto_out LIKE {protocol}".format(protocol=protocol)
        if handles == '3':
            return "proto_out NOT LIKE {protocol}".format(protocol=protocol)

        return ""


filterTypes = [SubnetFilter,PortFilter,ConnectionsFilter,TagsFilter,MaskFilter,TargetFilter,RoleFilter,EnvFilter,ProtocolFilter]
filterTypes.sort(key=lambda x: str(x)) #sort classes by name


def readEncoded(filterString):
    filters = []
    fstrings = filterString.split("|")

    # identify data source
    ds_match = re.search("(\d+)", fstrings[0])
    if ds_match:
        ds = int(ds_match.group())
    else:
        ds = dbaccess.get_settings_cached()['datasource']['id']

    for encodedFilter in fstrings[1:]:
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
    return ds, filters