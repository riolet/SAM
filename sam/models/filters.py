import sam.common
import re
from sam.models.settings import Settings
from sam.models.user import User


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

    def where(self, db):
        raise NotImplemented("This method must be overridden in the ({0}) class.".format(self.type))

    def having(self, db):
        raise NotImplemented("This method must be overridden in the ({0}) class.".format(self.type))

    def __eq__(self, other):
        if not isinstance(other, Filter):
            return False

        equal = (other.type == self.type and
                 other.enabled == self.enabled and
                 other.params == self.params)
        return equal


class SubnetFilter(Filter):
    def __init__(self, enabled=True, *args):
        Filter.__init__(self, "subnet", enabled)
        self.params['subnet'] = ""
        self.load(args)

    def where(self, db):
        subnet = int(self.params['subnet'])
        valid_subnets = [8, 16, 24, 32]
        if subnet not in valid_subnets:
            raise ValueError("Subnet is not valid. ({net} not in {valid})".format(net=subnet, valid=valid_subnets))

        return "nodes.subnet = {0}".format(subnet)

    def having(self, db):
        return ""


class MaskFilter(Filter):
    def __init__(self, enabled=True, *args):
        Filter.__init__(self, "mask", enabled)
        self.params['mask'] = ''
        self.load(args)

    def where(self, db):
        r = sam.common.determine_range_string(self.params['mask'])
        return "nodes.ipstart BETWEEN {0} AND {1}".format(r[0], r[1])

    def having(self, db):
        return ""


class PortFilter(Filter):
    def __init__(self, enabled=True, *args):
        Filter.__init__(self, "port", enabled)
        self.params['connection'] = ""
        self.params['port'] = ""
        self.load(args)
        # connections: 0, 1, 2, 3
        # 0: connects to port n
        # 1: doesn't connect to port n
        # 2: receives connection from port n
        # 3: doesn't receive connection from port n

    def where(self, db):
        if self.params['connection'] == '0':
            return "EXISTS (SELECT port FROM {{table_links_out}} AS `lo` WHERE lo.port = '{0}' AND lo.src_start = nodes.ipstart AND lo.src_end = nodes.ipend)".format(int(self.params['port']))
        elif self.params['connection'] == '1':
            return "NOT EXISTS (SELECT port FROM {{table_links_out}} AS `lo` WHERE lo.port = '{0}' AND lo.src_start = nodes.ipstart AND lo.src_end = nodes.ipend)".format(int(self.params['port']))

        elif self.params['connection'] == '2':
            return "EXISTS (SELECT port FROM {{table_links_in}} AS `li` WHERE li.port = '{0}' AND li.dst_start = nodes.ipstart AND li.dst_end = nodes.ipend)".format(int(self.params['port']))
        elif self.params['connection'] == '3':
            return "NOT EXISTS (SELECT port FROM {{table_links_in}} AS `li` WHERE li.port = '{0}' AND li.dst_start = nodes.ipstart AND li.dst_end = nodes.ipend)".format(int(self.params['port']))
        else:
            print ("Warning: no match for connection parameter of PortFilter when building WHERE clause. "
                   "({0}, type: {1})".format(self.params['connection'], type(self.params['connection'])))
        return ""

    def having(self, db):
        return ""


class ConnectionsFilter(Filter):
    def __init__(self, enabled=True, *args):
        Filter.__init__(self, "connections", enabled)
        self.params['comparator'] = ""
        self.params['direction'] = ""
        self.params['limit'] = ""
        self.load(args)

    def get_q(self):
        q = ""
        if self.params['comparator'] not in ['<', '>']:
            return ""
        limit = float(self.params['limit'])
        if self.params['direction'] == 'i':
            src = "conn_in / seconds"
            q += "{src} {comparator} '{limit}'".format(src=src, comparator=self.params['comparator'], limit=limit)
        elif self.params['direction'] == 'o':
            src = "conn_out / seconds"
            q += "{src} {comparator} '{limit}'".format(src=src, comparator=self.params['comparator'], limit=limit)
        elif self.params['direction'] == 'c':
            src = "(conn_in + conn_out) / seconds"
            q += "{src} {comparator} '{limit}'".format(src=src, comparator=self.params['comparator'], limit=limit)
        else:
            return ""
        return q

    def where(self, db):
        if db.dbname == 'sqlite':
            return self.get_q()
        else:
            return ''

    def having(self, db):
        if db.dbname == 'mysql':
            return self.get_q()
        else:
            return ''


class TargetFilter(Filter):
    def __init__(self, enabled=True, *args):
        Filter.__init__(self, "target", enabled)
        self.params['target'] = ""
        self.params['to'] = ""
        self.load(args)
        # for variable `to`:
        #   0: hosts connect to target
        #   1: hosts do NOT connect to target
        #   2: hosts receive connections from target
        #   3: hosts do NOT receive connections from target

    def where(self, db):
        ipstart, ipend = sam.common.determine_range_string(self.params['target'])
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

    def having(self, db):
        return ""


class TagsFilter(Filter):
    def __init__(self, enabled=True, *args):
        Filter.__init__(self, "tags", enabled)
        self.params['has'] = ""  # '1' or not '1'
        self.params['tags'] = ""
        self.load(args)

    def where(self, db):
        tags = str(self.params['tags']).split(",")
        phrase = "EXISTS (SELECT 1 FROM {{table_tags}} AS `f_tags` WHERE tag={0} AND f_tags.ipstart <= nodes.ipstart AND f_tags.ipend >= nodes.ipend)"
        if self.params['has'] != '1':
            phrase = "NOT " + phrase
        return "\n AND ".join([phrase.format(sam.common.web.sqlquote(tag)) for tag in tags])

    def having(self, db):
        return ""


class EnvFilter(Filter):
    def __init__(self, enabled=True, *args):
        Filter.__init__(self, "env", enabled)
        self.params['env'] = ""
        self.load(args)

    def get_q(self):
        env = self.params['env']
        return "computed_env = {0}".format(sam.common.web.sqlquote(env))

    def where(self, db):
        if db.dbname == 'sqlite':
            return self.get_q()
        else:
            return ''

    def having(self, db):
        if db.dbname == 'mysql':
            return self.get_q()
        else:
            return ''


class RoleFilter(Filter):
    def __init__(self, enabled=True, *args):
        Filter.__init__(self, "role", enabled)
        self.params['comparator'] = ""
        self.params['ratio'] = ""
        self.load(args)

    def get_q(self):
        cmp = self.params['comparator']
        if cmp not in ['<', '>']:
            cmp = '<'
        ratio = float(self.params['ratio'])
        return "(conn_in * 1.0 / (conn_in + conn_out)) {0} {1:.4f}".format(cmp, ratio)

    def where(self, db):
        if db.dbname == 'sqlite':
            return self.get_q()
        else:
            return ''

    def having(self, db):
        if db.dbname == 'mysql':
            return self.get_q()
        else:
            return ''


class ProtocolFilter(Filter):
    def __init__(self, enabled=True, *args):
        Filter.__init__(self, "protocol", enabled)
        self.params['handles'] = ""
        self.params['protocol'] = ""
        self.load(args)
        # handles:
        #   0: inbound protocol
        #   1: NOT inbound protocol
        #   2: outbound protocol
        #   3: NOT outbound protocol

    def get_q(self):
        handles = '0'
        if self.params['handles'] in ['0', '1', '2', '3']:
            handles = self.params['handles']
        protocol = sam.common.web.sqlquote("%" + self.params['protocol'] + "%")

        if handles == '0':
            return "proto_in LIKE {protocol}".format(protocol=protocol)
        if handles == '1':
            return "proto_in NOT LIKE {protocol}".format(protocol=protocol)
        if handles == '2':
            return "proto_out LIKE {protocol}".format(protocol=protocol)
        if handles == '3':
            return "proto_out NOT LIKE {protocol}".format(protocol=protocol)

        return ""

    def where(self, db):
        if db.dbname == 'sqlite':
            return self.get_q()
        else:
            return ''

    def having(self, db):
        if db.dbname == 'mysql':
            return self.get_q()
        else:
            return ''


filterTypes = [SubnetFilter,PortFilter,ConnectionsFilter,TagsFilter,MaskFilter,TargetFilter,RoleFilter,EnvFilter,ProtocolFilter]
filterTypes.sort(key=lambda x: str(x)) #sort classes by name


def readEncoded(db, sub_id, filterString):
    """
    :param filterString:
     :type filterString: unicode
    :return: 
    :rtype: tuple[ int, list[ Filter ] ]
    """
    filters = []
    fstrings = filterString.split("|")

    # identify data source
    ds_match = re.search("(\d+)", fstrings[0])
    if ds_match:
        ds = int(ds_match.group())
    else:
        settings_model = Settings(db, {}, sub_id)
        ds = settings_model['datasource']

    for encodedFilter in fstrings[1:]:
        try:
            params = encodedFilter.split(";")
            typeIndex, enabled, params = params[0], params[1], params[2:]
            enabled = (enabled == "1") #convert to boolean
            filterClass = filterTypes[int(typeIndex)]
            f = filterClass(enabled, *params)
            #f.load(params)
            filters.append(f)
        except:
            print("ERROR: unable to decode filter: " + encodedFilter)
    return ds, filters
