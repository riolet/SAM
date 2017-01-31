import web
import common
from datetime import datetime
import time
import os
import re


def parse_sql_file(path, replacements):
    with open(path, 'r') as f:
        lines = f.readlines()
    # remove comment lines
    lines = [i for i in lines if not i.startswith("--")]
    # join into one long string
    script = " ".join(lines)
    # do any necessary string replacements
    if replacements:
        script = script.format(**replacements)
    # split string into a list of commands
    commands = script.split(";")
    # ignore empty statements (like trailing newlines)
    commands = filter(lambda x: bool(x.strip()), commands)
    return commands


def exec_sql(connection, path, replacements=None):
    if not replacements:
        commands = parse_sql_file(path, {})
    else:
        commands = parse_sql_file(path, replacements)
    for command in commands:
        connection.query(command)


def validate_ds_name(name):
    return name == name.strip() and re.match(r'^[a-z][a-z0-9_ ]*$', name, re.I)


def create_ds_tables(id):
    replacements = {"id": id}
    exec_sql(common.db, os.path.join(common.base_path, 'sql/setup_datasource.sql'), replacements)
    return 0


def create_datasource(name):
    if not validate_ds_name(name):
        return -1
    id = common.db.insert("Datasources", name=name)
    r = create_ds_tables(id)
    return r


def remove_datasource(id):
    settings = get_settings(all=True)
    ids = [ds['id'] for ds in settings['datasources']]

    # check id is valid
    if id not in ids:
        print("Removal stopped: data source to remove not found")
        return

    # select other data source in Settings
    alt_id = -1
    for n in ids:
        if n != id:
            alt_id = n
            break
    if alt_id == -1:
        print("Removal stopped: Cannot remove last data source")
        return
    set_settings(datasource=alt_id)

    # remove from live_dest if selected
    if settings['live_dest'] == id:
        set_settings(live_dest=None)

    # remove from Datasources
    common.db.delete("Datasources", "id = {0}".format(int(id)))
    # Drop relevant tables
    replacements = {"id": int(id)}
    exec_sql(common.db, os.path.join(common.base_path, 'sql/drop_datasource.sql'), replacements)


def get_syslog_size(datasource, buffer, _test=False):
    return common.db.select("ds_{0}_Syslog{1}".format(datasource, buffer),
                            what="COUNT(1) AS 'rows'",
                            _test=_test)[0].rows


def get_timerange(ds):
    dses = get_ds_list_cached()
    if ds not in dses:
        raise ValueError("Invalid data source specified. ({0} not in {1})".format(ds, dses))
    prefix = "ds_{0}_".format(ds)

    rows = common.db.query("SELECT MIN(timestamp) AS 'min', MAX(timestamp) AS 'max' "
                           "FROM {prefix}Links;".format(prefix=prefix))
    row = rows[0]
    if row['min'] is None or row['max'] is None:
        now = time.mktime(datetime.now().timetuple())
        return {'min': now, 'max': now}
    return {'min': time.mktime(row['min'].timetuple()), 'max': time.mktime(row['max'].timetuple())}


def get_nodes(ip_start, ip_end):
    diff = ip_end - ip_start
    if diff > 16777215:
        # check Nodes8
        # rows = common.db.select("Nodes8")
        rows = common.db.select("Nodes", where="subnet=8")
    elif diff > 65536:
        # check Nodes16
        rows = common.db.select("Nodes", where="subnet=16 && ipstart BETWEEN {0} AND {1}".format(ip_start, ip_end))
    elif diff > 255:
        # check Nodes24
        rows = common.db.select("Nodes", where="subnet=24 && ipstart BETWEEN {0} AND {1}".format(ip_start, ip_end))
    elif diff > 0:
        # check Nodes32
        rows = common.db.select("Nodes", where="subnet=32 && ipstart BETWEEN {0} AND {1}".format(ip_start, ip_end))
    else:
        rows = []
    return rows


def build_where_clause(timestamp_range=None, port=None, protocol=None, rounding=True):
    clauses = []
    t_start = 0
    t_end = 0

    if timestamp_range:
        t_start = timestamp_range[0]
        t_end = timestamp_range[1]
        if rounding:
            # rounding to 5 minutes, for use with the Syslog table
            if t_start > 150:
                t_start -= 150
            if t_end <= 2 ** 31 - 150:
                t_end += 149
        clauses.append("timestamp BETWEEN FROM_UNIXTIME($tstart) AND FROM_UNIXTIME($tend)")

    if port:
        clauses.append("port = $port")

    if protocol:
        clauses.append("protocols LIKE $protocol")
        protocol = "%{0}%".format(protocol)

    qvars = {'tstart': t_start, 'tend': t_end, 'port': port, 'protocol': protocol}
    WHERE = str(web.db.reparam("\n    && ".join(clauses), qvars))
    if WHERE:
        WHERE = "    && " + WHERE
    return WHERE


def get_details_summary(ds, ip_start, ip_end, timestamp_range=None, port=None):
    WHERE = build_where_clause(timestamp_range=timestamp_range, port=port)
    dses = get_ds_list_cached()
    if ds not in dses:
        raise ValueError("Invalid data source specified. ({0} not in {1})".format(ds, dses))
    prefix = "ds_{0}_".format(ds)

    # TODO: seconds has a magic number 300 added to account for DB time quantization.
    query = """
    SELECT `inputs`.ips AS 'unique_in'
        , `outputs`.ips AS 'unique_out'
        , `inputs`.ports AS 'unique_ports'
    FROM
      (SELECT COUNT(DISTINCT src) AS 'ips', COUNT(DISTINCT port) AS 'ports'
        FROM {prefix}Links
        WHERE dst BETWEEN $start AND $end
         {where}
    ) AS `inputs`
    JOIN (SELECT COUNT(DISTINCT dst) AS 'ips'
        FROM {prefix}Links
        WHERE src BETWEEN $start AND $end
         {where}
    ) AS `outputs`;""".format(where=WHERE, prefix=prefix)

    qvars = {'start': ip_start, 'end': ip_end}
    rows = common.db.query(query, vars=qvars)
    row = rows[0]
    return row


def get_details_connections(ds, ip_start, ip_end, inbound, timestamp_range=None, port=None, page=1, page_size=50, order="-links", simple=False):
    sort_options = ['links', 'src', 'dst', 'port', 'sum_bytes', 'sum_packets', 'protocols', 'avg_duration']
    sort_options_simple = ['links', 'src', 'dst', 'port']
    dses = get_ds_list_cached()
    if ds not in dses:
        raise ValueError("Invalid data source specified. ({0} not in {1})".format(ds, dses))
    prefix = "ds_{0}_".format(ds)

    qvars = {
        'start': ip_start,
        'end': ip_end,
        'page': page_size * (page-1),
        'page_size': page_size,
        'WHERE': build_where_clause(timestamp_range, port),
        'prefix': prefix
    }
    if inbound:
        qvars['collected'] = "src"
        qvars['filtered'] = "dst"
    else:
        qvars['filtered'] = "src"
        qvars['collected'] = "dst"

    # determine the sort direction
    if order and order[0] == '-':
        sort_dir = "DESC"
    else:
        sort_dir = "ASC"
    # determine the sort column
    if simple:
        if order and order[1:] in sort_options_simple:
            sort_by = order[1:]
        else:
            sort_by = sort_options_simple[0]
    else:
        if order and order[1:] in sort_options:
            sort_by = order[1:]
        else:
            sort_by = sort_options[0]
    # add table prefix for some columns
    if sort_by in ['port', 'src', 'dst']:
        sort_by = "`links`." + sort_by

    qvars['order'] = "{0} {1}".format(sort_by, sort_dir)

    if simple:
        query = """
SELECT decodeIP({collected}) AS '{collected}'
    , port AS 'port'
    , sum(links) AS 'links'
FROM {prefix}Links AS `links`
WHERE {filtered} BETWEEN $start AND $end
 {WHERE}
GROUP BY `links`.src, `links`.dst, `links`.port
ORDER BY {order}
LIMIT {page}, {page_size}
        """.format(**qvars)
    else:
        query = """
SELECT src, dst, port, links, protocols
    , sum_bytes
    , (sum_bytes / links) AS 'avg_bytes'
    , sum_packets
    , (sum_packets / links) AS 'avg_packets'
    , (_duration / links) AS 'avg_duration'
FROM(
    SELECT decodeIP(src) AS 'src'
        , decodeIP(dst) AS 'dst'
        , port AS 'port'
        , sum(links) AS 'links'
        , GROUP_CONCAT(DISTINCT protocol SEPARATOR ", ") AS 'protocols'
        , SUM(bytes_sent + COALESCE(bytes_received, 0)) AS 'sum_bytes'
        , SUM(packets_sent + COALESCE(packets_received, 0)) AS 'sum_packets'
        , SUM(duration*links) AS '_duration'
    FROM {prefix}Links AS `links`
    WHERE {filtered} BETWEEN $start AND $end
     {WHERE}
    GROUP BY `links`.src, `links`.dst, `links`.port
    ORDER BY {order}
    LIMIT {page}, {page_size}
) AS precalc;
        """.format(**qvars)
    return list(common.db.query(query, vars=qvars))


def get_details_ports(ds, ip_start, ip_end, timestamp_range=None, port=None, page=1, page_size=50, order="-links"):
    sort_options = ['links', 'port']
    first_result = (page - 1) * page_size
    dses = get_ds_list_cached()
    if ds not in dses:
        raise ValueError("Invalid data source specified. ({0} not in {1})".format(ds, dses))
    prefix = "ds_{0}_".format(ds)

    qvars = {
        'start': ip_start,
        'end': ip_end,
        'first': first_result,
        'size': page_size,
        'WHERE': build_where_clause(timestamp_range, port),
        'prefix': prefix
    }

    if order and order[0] == '-':
        sort_dir = "DESC"
    else:
        sort_dir = "ASC"
    if order and order[1:] in sort_options:
        sort_by = order[1:]
    else:
        sort_by = sort_options[0]
    qvars['order'] = "{0} {1}".format(sort_by, sort_dir)

    query = """
        SELECT port AS 'port', sum(links) AS 'links'
        FROM {prefix}Links
        WHERE dst BETWEEN $start AND $end
         {WHERE}
        GROUP BY port
        ORDER BY {order}
        LIMIT $first, $size;
    """.format(**qvars)
    return list(common.db.query(query, vars=qvars))


def get_details_children(ds, ip_start, ip_end, page, page_size, order):
    sort_options = ['ipstart', 'hostname', 'endpoints', 'ratio']
    dses = get_ds_list_cached()
    if ds not in dses:
        raise ValueError("Invalid data source specified. ({0} not in {1})".format(ds, dses))
    prefix = "ds_{0}_".format(ds)

    ip_diff = ip_end - ip_start
    if ip_diff == 0:
        return []
    elif ip_diff == 255:
        quotient = 1
        child_subnet_start = 25
        child_subnet_end = 32
    elif ip_diff == 65535:
        quotient = 256
        child_subnet_start = 17
        child_subnet_end = 24
    elif ip_diff == 16777215:
        quotient = 65536
        child_subnet_start = 9
        child_subnet_end = 16
    else:
        quotient = 16777216
        child_subnet_start = 1
        child_subnet_end = 8
    first_result = (page - 1) * page_size
    qvars = {'ip_start': ip_start,
             'ip_end': ip_end,
             's_start': child_subnet_start,
             's_end': child_subnet_end,
             'first': first_result,
             'size': page_size,
             'quot': quotient,
             'quot_1': quotient - 1}

    if order and order[0] == '-':
        sort_dir = "DESC"
    else:
        sort_dir = "ASC"
    if order and order[1:] in sort_options:
        sort_by = order[1:]
    else:
        sort_by = sort_options[0]
    qvars['order'] = "{0} {1}".format(sort_by, sort_dir)

    query = """
        SELECT decodeIP(`n`.ipstart) AS 'address'
          , COALESCE(`n`.alias, '') AS 'hostname'
          , `n`.subnet AS 'subnet'
          , `sn`.kids AS 'endpoints'
          , COALESCE(COALESCE(`l_in`.links,0) / (COALESCE(`l_in`.links,0) + COALESCE(`l_out`.links,0)), 0) AS 'ratio'
        FROM Nodes AS `n`
        LEFT JOIN (
            SELECT dst_start DIV $quot * $quot AS 'low'
                , dst_end DIV $quot * $quot + $quot_1 AS 'high'
                , sum(links) AS 'links'
            FROM {prefix}LinksIn
            GROUP BY low, high
            ) AS `l_in`
        ON `l_in`.low = `n`.ipstart AND `l_in`.high = `n`.ipend
        LEFT JOIN (
            SELECT src_start DIV $quot * $quot AS 'low'
                , src_end DIV $quot * $quot + $quot_1 AS 'high'
                , sum(links) AS 'links'
            FROM {prefix}LinksOut
            GROUP BY low, high
            ) AS `l_out`
        ON `l_out`.low = `n`.ipstart AND `l_out`.high = `n`.ipend
        LEFT JOIN (
            SELECT ipstart DIV $quot * $quot AS 'low'
                , ipend DIV $quot * $quot + $quot_1 AS 'high'
                , COUNT(ipstart) AS 'kids'
            FROM Nodes
            WHERE ipstart = ipend
            GROUP BY low, high
            ) AS `sn`
        ON `sn`.low = `n`.ipstart AND `sn`.high = `n`.ipend
        WHERE `n`.ipstart BETWEEN $ip_start AND $ip_end
            AND `n`.subnet BETWEEN $s_start AND $s_end
        ORDER BY {order}
        LIMIT $first, $size;
        """.format(order=qvars['order'], prefix=prefix)
    return list(common.db.query(query, vars=qvars))


def get_protocol_list(ds):
    dses = get_ds_list_cached()
    if ds not in dses:
        raise ValueError("Invalid data source specified. ({0} not in {1})".format(ds, dses))
    prefix = "ds_{0}_".format(ds)
    table = "{0}Links".format(prefix)
    return [row.protocol for row in common.db.select(table, what="DISTINCT protocol") if row.protocol]


def get_port_info(port):
    if isinstance(port, list):
        arg = "({0})".format(",".join(map(str, port)))
    else:
        arg = "({0})".format(port)

    query = """
        SELECT Ports.port, Ports.active, Ports.name, Ports.description,
            PortAliases.name AS alias_name,
            PortAliases.description AS alias_description
        FROM Ports
        LEFT JOIN PortAliases
            ON Ports.port=PortAliases.port
        WHERE Ports.port IN {0}
    """.format(arg)
    info = list(common.db.query(query))
    return info


def set_port_info(data):
    MAX_NAME_LENGTH = 10
    MAX_DESCRIPTION_LENGTH = 255

    if 'port' not in data:
        print "Error setting port info: no port specified"
        return
    port = data['port']

    alias_name = ''
    alias_description = ''
    active = 0
    if 'alias_name' in data:
        alias_name = data['alias_name'][:MAX_NAME_LENGTH]
    if 'alias_description' in data:
        alias_description = data['alias_description'][:MAX_DESCRIPTION_LENGTH]
    if 'active' in data:
        active = 1 if data['active'] == '1' or data['active'] == 1 else 0

    # update PortAliases database of names to include the new information
    exists = common.db.select('PortAliases', what="1", where={"port": port})

    if len(exists) == 1:
        kwargs = {}
        if 'alias_name' in data:
            kwargs['name'] = alias_name
        if 'alias_description' in data:
            kwargs['description'] = alias_description
        if kwargs:
            common.db.update('PortAliases', {"port": port}, **kwargs)
    else:
        common.db.insert('PortAliases', port=port, name=alias_name, description=alias_description)

    # update Ports database of default values to include the missing information
    exists = common.db.select('Ports', what="1", where={"port": port})
    if len(exists) == 1:
        if 'active' in data:
            common.db.update('Ports', {"port": port}, active=active)
    else:
        common.db.insert('Ports', port=port, active=active, tcp=1, udp=1, name="", description="")


def get_table_info(ds, clauses, page, page_size, order_by, order_dir):
    dses = get_ds_list_cached()
    if ds not in dses:
        raise ValueError("Invalid data source specified. ({0} not in {1})".format(ds, dses))
    prefix = "ds_{0}_".format(ds)

    WHERE = " && ".join(clause.where() for clause in clauses if clause.where())
    if WHERE:
        WHERE = "WHERE " + WHERE

    HAVING = " && ".join(clause.having() for clause in clauses if clause.having())
    if HAVING:
        HAVING = "HAVING (conn_out + conn_in != 0) && " + HAVING
    else:
        HAVING = "HAVING (conn_out + conn_in != 0)"

    #      ['address', 'alias', 'role', 'environment', 'tags', 'bytes', 'packets', 'protocols']
    cols = ['nodes.ipstart', 'nodes.alias', '(conn_in / (conn_in + conn_out))', 'env', 'CONCAT(tags, parent_tags)', '(bytes_in + bytes_out)', '(packets_in + packets_out)', 'CONCAT(proto_in, proto_out)']
    ORDERBY = ""
    if 0 <= order_by < len(cols) and order_dir in ['asc', 'desc']:
        ORDERBY = "ORDER BY {0} {1}".format(cols[order_by], order_dir)

    #TODO: seconds has a magic number 300 added to account for DB time quantization.
    # note: group concat max length is default at 1024.
    # if any data is lost due to max length, try:
    # SET group_concat_max_len = 2048
    query = """
    SELECT CONCAT(decodeIP(ipstart), CONCAT('/', subnet)) AS 'address'
        , COALESCE(nodes.alias, '') AS 'alias'
        , COALESCE((
            SELECT env
            FROM Nodes nz
            WHERE nodes.ipstart >= nz.ipstart AND nodes.ipend <= nz.ipend AND env IS NOT NULL AND env != "inherit"
            ORDER BY (nodes.ipstart - nz.ipstart + nz.ipend - nodes.ipend) ASC
            LIMIT 1
        ), 'production') AS "env"
        , COALESCE((SELECT SUM(links)
            FROM {prefix}LinksOut AS l_out
            WHERE l_out.src_start = nodes.ipstart
              AND l_out.src_end = nodes.ipend
         ),0) AS 'conn_out'
        , COALESCE((SELECT SUM(links)
            FROM {prefix}LinksIn AS l_in
            WHERE l_in.dst_start = nodes.ipstart
              AND l_in.dst_end = nodes.ipend
         ),0) AS 'conn_in'
        , COALESCE((SELECT SUM(bytes)
            FROM {prefix}LinksOut AS l_out
            WHERE l_out.src_start = nodes.ipstart
              AND l_out.src_end = nodes.ipend
         ),0) AS 'bytes_out'
        , COALESCE((SELECT SUM(bytes)
            FROM {prefix}LinksIn AS l_in
            WHERE l_in.dst_start = nodes.ipstart
              AND l_in.dst_end = nodes.ipend
         ),0) AS 'bytes_in'
        , COALESCE((SELECT SUM(packets)
            FROM {prefix}LinksOut AS l_out
            WHERE l_out.src_start = nodes.ipstart
              AND l_out.src_end = nodes.ipend
         ),0) AS 'packets_out'
        , COALESCE((SELECT SUM(packets)
            FROM {prefix}LinksIn AS l_in
            WHERE l_in.dst_start = nodes.ipstart
              AND l_in.dst_end = nodes.ipend
         ),0) AS 'packets_in'
        , COALESCE((SELECT (MAX(TIME_TO_SEC(timestamp)) - MIN(TIME_TO_SEC(timestamp)) + 300)
            FROM {prefix}Links AS l
        ),0) AS 'seconds'
        , COALESCE((SELECT GROUP_CONCAT(DISTINCT protocols SEPARATOR ',')
            FROM {prefix}LinksIn AS l_in
            WHERE l_in.dst_start = nodes.ipstart AND l_in.dst_end = nodes.ipend
         ),"") AS 'proto_in'
        , COALESCE((SELECT GROUP_CONCAT(DISTINCT protocols SEPARATOR ',')
            FROM {prefix}LinksOut AS l_out
            WHERE l_out.src_start = nodes.ipstart AND l_out.src_end = nodes.ipend
         ),"") AS 'proto_out'
        , COALESCE((SELECT GROUP_CONCAT(tag SEPARATOR ', ')
            FROM Tags
            WHERE Tags.ipstart = nodes.ipstart AND Tags.ipend = nodes.ipend
            GROUP BY ipstart, ipend
         ),"") AS 'tags'
        , COALESCE((SELECT GROUP_CONCAT(tag SEPARATOR ', ')
            FROM Tags
            WHERE (Tags.ipstart <= nodes.ipstart AND Tags.ipend > nodes.ipend) OR (Tags.ipstart < nodes.ipstart AND Tags.ipend >= nodes.ipend)
            GROUP BY nodes.ipstart, nodes.ipend
         ),"") AS 'parent_tags'
    FROM Nodes AS nodes
    {WHERE}
    {HAVING}
    {ORDER}
    LIMIT {START},{RANGE};
    """.format(
        WHERE=WHERE,
        HAVING=HAVING,
        ORDER=ORDERBY,
        START=page * page_size,
        RANGE=page_size + 1,
        prefix=prefix)

    info = list(common.db.query(query))
    return info


settingsCache = {}
dsCache = []


def get_settings_cached():
    global settingsCache
    if not settingsCache:
        settingsCache.update(get_settings())
    settingsCache['prefix'] = "ds_{0}_".format(str(settingsCache['datasource']['id']))
    return settingsCache


def get_ds_list_cached():
    global dsCache
    if not dsCache:
        dsCache = [src.id for src in common.db.select("Datasources")]
    return dsCache


def get_settings(all=False):
    settings = dict(common.db.select("Settings", limit=1)[0])
    if all:
        sources = map(dict, common.db.select("Datasources"))
        settings['datasources'] = sources
        target = settings['datasource']
        settings['datasource'] = None
        for ds_index in range(len(sources)):
            if sources[ds_index]['id'] == target:
                settings['datasource'] = sources[ds_index]
        global dsCache
        dsCache = [src['id'] for src in sources]
    else:
        where = "id={0}".format(settings['datasource'])
        ds = common.db.select("Datasources", where=where, limit=1)
        if len(ds) == 1:
            settings['datasource'] = dict(ds[0])
        else:
            settings['datasource'] = None

    # keep the cache up to date
    global settingsCache
    settingsCache.update(settings)

    return settings


def set_settings(**kwargs):
    if "datasource" in kwargs:
        new_ds = kwargs.pop('datasource')
        common.db.update("Settings", "1", datasource=new_ds)

    ds = 0
    if "ds" in kwargs:
        ds = kwargs.pop('ds')

    if ds and kwargs:
        common.db.update("Datasources", ds, **kwargs)
    elif kwargs:
        common.db.update("Settings JOIN Datasources ON Settings.datasource = Datasources.id", "1", **kwargs)

    # clear the cache
    global settingsCache
    global dsCache
    settingsCache = {}
    dsCache = []


def get_datasource(id):
    rows = common.db.select("Datasources", where="id={0}".format(int(id)), limit=1)
    if len(rows) == 1:
        return rows[0]
    return None


def delete_custom_hostnames():
    common.db.update("Nodes", "1", alias=common.web.sqlliteral("NULL"))


def delete_connections(ds):
    if len(common.db.select("Datasources", where={'id': ds})) == 1:
        prefix = "ds_{0}_".format(ds)
        common.db.delete("{0}Links".format(prefix), "1")
        common.db.delete("{0}LinksIn".format(prefix), "1")
        common.db.delete("{0}LinksOut".format(prefix), "1")


def print_dict(d, indent = 0):
    for k,v in d.iteritems():
        if type(v) == dict:
            print("{0}{1:>20s}: ".format(indent * 4 * " ", k))
            print_dict(v, indent + 1)
        else:
            print("{0}{1:>20s}: {2}".format(indent*4*" ", k, repr(v)))
