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


def get_syslog_size(datasource, buffer, _test=False):
    return common.db.select("ds_{0}_Syslog{1}".format(datasource, buffer),
                            what="COUNT(1) AS 'rows'",
                            _test=_test)[0].rows


def get_timerange(ds):
    dses = common.datasources.dses
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


def print_dict(d, indent = 0):
    for k,v in d.iteritems():
        if type(v) == dict:
            print("{0}{1:>20s}: ".format(indent * 4 * " ", k))
            print_dict(v, indent + 1)
        else:
            print("{0}{1:>20s}: {2}".format(indent*4*" ", k, repr(v)))
