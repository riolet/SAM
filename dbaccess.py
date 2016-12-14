import web
import common
from datetime import datetime
import time
import os
import re


def parse_sql_file(path, replacements=None):
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
    # check id is valid
    rows = list(common.db.select("Datasources", where={'id': int(id)}))
    print("|==>--")
    print("before")
    print(rows)
    if len(rows) != 1:
        print("Removal stopped: data source to remove not found")
        return

    print("after")

    # select other data source in Settings
    alternativeDS = common.db.select("Datasources", where="id != {0}".format(int(id)), limit=1)
    if len(alternativeDS) != 1:
        print("Removal stopped: No alternative data source available")
        return
    alt_id = alternativeDS[0].id
    common.db.update("Settings", "1=1", datasource=alt_id)
    # remove from Datasources
    common.db.delete("Datasources", "id = {0}".format(int(id)))
    # Drop relevant tables
    replacements = {"id": int(id)}
    exec_sql(common.db, os.path.join(common.base_path, 'sql/drop_datasource.sql'), replacements)


def get_syslog_size():
    return common.db.select("{0}Syslog".format(get_settings_cached()['prefix'])
                            , what="COUNT(1) AS 'rows'")[0].rows


def get_timerange():
    prefix = get_settings_cached()['prefix']
    rows = common.db.query("SELECT MIN(timestamp) AS 'min', MAX(timestamp) AS 'max' "
                           "FROM {prefix}Links;".format(prefix=prefix))
    row = rows[0]
    if row['min'] == None or row['max'] == None:
        return {'min': time.mktime(datetime.now().timetuple()), 'max': time.mktime(datetime.now().timetuple())}
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
        rows = common.db.select("Nodes", where="subnet=32 && ipstart BETWEEN {0} AND {1}".format(r[0], r[1]))
    else:
        rows = []
    return rows


def get_links(ip_start, ip_end, inbound, port_filter=None, timerange=None, protocol=None):
    """
    This function returns a list of the connections coming in to a given node from the rest of the graph.

    * The connections are aggregated into groups based on the first diverging ancestor.
        that means that connections to destination 1.2.3.4
        that come from source 1.9.*.* will be grouped together as a single connection.

    * for /8, /16, and /24, `IP to IP` is a unique connection.
    * for /32, `IP to IP on Port` make a unique connection.

    * If filter is provided, only connections over the given port are considered.

    * If timerange is provided, only connections that occur within the given time range are considered.

    :param ipstart:  integer indicating the low end of the IP address range constraint
    :param ipend:  integer indicating the high end of the IP address range constraint
    :param inbound:  boolean, the direction of links to consider:
        If True, only consider links that terminate in the ip_range specified.
        If False, only consider links that originate in the ip_range specified,
    :param port_filter:  Only consider connections using this destination port. Default is no filtering.
    :param timerange:  Tuple of (start, end) timestamps. Only connections happening
    during this time period are considered.
    :return: A list of db results formated as web.storage objects (used like dictionaries)
    """
    ports = (ip_start == ip_end)  # include ports in the results?
    where = build_where_clause(timerange, port_filter, protocol)
    prefix = get_settings_cached()['prefix']

    if ports:
        select = "src_start, src_end, dst_start, dst_end, port, sum(links) AS 'links', GROUP_CONCAT(DISTINCT protocols SEPARATOR ',') AS 'protocols'"
        group_by = "GROUP BY src_start, src_end, dst_start, dst_end, port"
    else:
        select = "src_start, src_end, dst_start, dst_end, sum(links) AS 'links', GROUP_CONCAT(DISTINCT protocols SEPARATOR ',') AS 'protocols'"
        group_by = "GROUP BY src_start, src_end, dst_start, dst_end"

    if inbound:
        query = """
        SELECT {select}
        FROM {prefix}LinksIn
        WHERE dst_start = $start && dst_end = $end
         {where}
        {group_by}
        """.format(where=where, select=select, group_by=group_by, prefix=prefix)
    else:
        query = """
        SELECT {select}
        FROM {prefix}LinksOut
        WHERE src_start = $start && src_end = $end
         {where}
        {group_by}
        """.format(where=where, select=select, group_by=group_by, prefix=prefix)

    qvars = {"start": ip_start, "end": ip_end}
    rows = list(common.db.query(query, vars=qvars))
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


def get_details_summary(ip_start, ip_end, timestamp_range=None, port=None):
    WHERE = build_where_clause(timestamp_range=timestamp_range, port=port)
    prefix = get_settings_cached()['prefix']

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


def get_details_connections(ip_start, ip_end, inbound, timestamp_range=None, port=None, page=1, page_size=50, order="-links", simple=False):
    sort_options = ['links', 'src', 'dst', 'port', 'sum_bytes', 'sum_packets', 'protocols', 'avg_duration']
    sort_options_simple = ['links', 'src', 'dst', 'port']
    qvars = {
        'start': ip_start,
        'end': ip_end,
        'page': page_size * (page-1),
        'page_size': page_size,
        'WHERE': build_where_clause(timestamp_range, port),
        'prefix': get_settings_cached()['prefix']
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
        sort_by = "`{prefix}Links`." + sort_by

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
    , avg_duration
FROM(
    SELECT decodeIP(src) AS 'src'
        , decodeIP(dst) AS 'dst'
        , port AS 'port'
        , sum(links) AS 'links'
        , GROUP_CONCAT(DISTINCT protocol SEPARATOR ", ") AS 'protocols'
        , SUM(bytes_sent + COALESCE(bytes_received, 0)) AS 'sum_bytes'
        , SUM(packets_sent + COALESCE(packets_received, 0)) AS 'sum_packets'
        , AVG(duration) AS 'avg_duration'
    FROM {prefix}Links AS `links`
    WHERE {filtered} BETWEEN $start AND $end
     {WHERE}
    GROUP BY `links`.src, `links`.dst, `links`.port
    ORDER BY {order}
    LIMIT {page}, {page_size}
) AS precalc;
        """.format(**qvars)
    return list(common.db.query(query, vars=qvars))


def get_details_ports(ip_start, ip_end, timestamp_range=None, port=None, page=1, page_size=50, order="-links"):
    sort_options = ['links', 'port']
    first_result = (page - 1) * page_size
    qvars = {
        'start': ip_start,
        'end': ip_end,
        'first': first_result,
        'size': page_size,
        'WHERE': build_where_clause(timestamp_range, port),
        'prefix': get_settings_cached()['prefix']
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


def get_details_children(ip_start, ip_end, page, page_size, order):
    sort_options = ['ipstart', 'hostname', 'endpoints', 'ratio']
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
          , COALESCE(`l_in`.links,0) / (COALESCE(`l_in`.links,0) + COALESCE(`l_out`.links,0)) AS 'ratio'
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
        """.format(order=qvars['order'], prefix=get_settings_cached()['prefix'])
    return list(common.db.query(query, vars=qvars))


def get_tags(address):
    """
    Gets all directly assigned tags and inherited parent tags for a given addresss

    :param address: A string dotted-decimal IP address such as "192.168.2.100" or "21.66" or "1.2.0.0/16"
    :return: A dict of lists of strings, with keys 'tags' and 'p_tags' where p_tags are inherited tags from parent nodes
    """
    ipstart, ipend = common.determine_range_string(address)
    WHERE = 'ipstart <= $start AND ipend >= $end'
    qvars = {'start': ipstart, 'end': ipend}
    data = common.db.select("Tags", vars=qvars, where=WHERE)
    parent_tags = []
    tags = []
    for row in data:
        if row.ipend == ipend and row.ipstart == ipstart:
            tags.append(row.tag)
        else:
            parent_tags.append(row.tag)
    return {"p_tags": parent_tags, "tags": tags}


def get_tag_list():
    return [row.tag for row in common.db.select("Tags", what="DISTINCT tag") if row.tag]


def set_tags(address, new_tags):
    """
    Assigns a new set of tags to an address overwriting any existing tag assignments.

    :param address: A string dotted-decimal IP address such as "192.168.2.100" or "21.66" or "1.2.0.0/16"
    :param new_tags: A list of tag strings. e.g. ['tag_one', 'tag_two', 'tag_three']
    :return: None
    """
    table = 'Tags'
    what = "ipstart, ipend, tag"
    r = common.determine_range_string(address)
    row = {"ipstart": r[0], "ipend": r[1]}
    where = "ipstart = $ipstart AND ipend = $ipend"

    existing = list(common.db.select(table, vars=row, what=what, where=where))
    old_tags = [x.tag for x in existing]
    removals = [x for x in old_tags if x not in new_tags]
    additions = [x for x in new_tags if x not in old_tags]

    # print("-"*70, '\n', '-'*70)
    # print("TAG FACTORY")
    # print("old_tags: " + repr(old_tags))
    # print("new_tags: " + repr(new_tags))
    # print("additions: " + repr(additions))
    # print("removals: " + repr(removals))
    # print("-"*70, '\n', '-'*70)

    for tag in additions:
        row['tag'] = tag
        common.db.insert("Tags", **row)

    for tag in removals:
        row['tag'] = tag
        where = "ipstart = $ipstart AND ipend = $ipend AND tag = $tag"
        common.db.delete("Tags", where=where, vars=row)


def get_env(address):
    ipstart, ipend = common.determine_range_string(address)
    WHERE = 'ipstart <= $start AND ipend >= $end'
    qvars = {'start': ipstart, 'end': ipend}
    data = common.db.select("Nodes", vars=qvars, where=WHERE, what="ipstart, ipend, env")
    parent_env = "production"
    env = "inherit"
    nearest_distance = -1
    for row in data:
        if row.ipend == ipend and row.ipstart == ipstart:
            if row.env:
                env = row.env
        else:
            dist = row.ipend - ipend + ipstart - row.ipstart
            if nearest_distance == -1 or dist < nearest_distance:
                if row.env and row.env != "inherit":
                    parent_env = row.env
    return {"env": env, "p_env": parent_env}


def get_env_list():
    envs = set(row.env for row in common.db.select("Nodes", what="DISTINCT env") if row.env)
    envs.add("production")
    envs.add("inherit")
    envs.add("dev")
    return envs


def set_env(address, env):
    r = common.determine_range_string(address)
    where = {"ipstart": r[0], "ipend": r[1]}
    common.db.update('Nodes', where, env=env)


def get_protocol_list():
    prefix = get_settings_cached()['prefix']
    table = "{0}Links".format(prefix)
    return [row.protocol for row in common.db.select(table, what="DISTINCT protocol") if row.protocol]


def get_node_info(address):
    ipstart, ipend = common.determine_range_string(address)
    prefix = get_settings_cached()['prefix']
    qvars = {"start": ipstart, "end": ipend}

    query = """
        SELECT CONCAT(decodeIP(n.ipstart), CONCAT('/', n.subnet)) AS 'address'
            , COALESCE(n.hostname, '') AS 'hostname'
            , COALESCE(l_out.unique_out_ip, 0) AS 'unique_out_ip'
            , COALESCE(l_out.unique_out_conn, 0) AS 'unique_out_conn'
            , COALESCE(l_out.total_out, 0) AS 'total_out'
            , l_out.b_s AS 'out_bytes_sent'
            , l_out.b_r AS 'out_bytes_received'
            , l_out.max_bps AS 'out_max_bps'
            , l_out.min_bps AS 'out_min_bps'
            , (l_out.sum_b / l_out.duration) AS 'out_avg_bps'
            , l_out.p_s AS 'out_packets_sent'
            , l_out.p_r AS 'out_packets_received'
            , (l_out.duration / COALESCE(l_out.total_out, 1)) AS 'out_duration'
            , COALESCE(l_in.unique_in_ip, 0) AS 'unique_in_ip'
            , COALESCE(l_in.unique_in_conn, 0) AS 'unique_in_conn'
            , COALESCE(l_in.total_in, 0) AS 'total_in'
            , l_in.b_s AS 'in_bytes_sent'
            , l_in.b_r AS 'in_bytes_received'
            , l_in.max_bps AS 'in_max_bps'
            , l_in.min_bps AS 'in_min_bps'
            , (l_in.sum_b / l_in.duration) AS 'in_avg_bps'
            , l_in.p_s AS 'in_packets_sent'
            , l_in.p_r AS 'in_packets_received'
            , (l_in.duration / COALESCE(l_in.total_in, 1)) AS 'in_duration'
            , COALESCE(l_in.ports_used, 0) AS 'ports_used'
            , children.endpoints AS 'endpoints'
            , t.seconds
            , COALESCE(l_in.protocol, "") AS 'in_protocols'
            , COALESCE(l_out.protocol, "") AS 'out_protocols'
        FROM (
            SELECT ipstart, subnet, alias AS 'hostname'
            FROM Nodes
            WHERE ipstart = $start AND ipend = $end
        ) AS n
        LEFT JOIN (
            SELECT $start AS 's1'
            , COUNT(DISTINCT dst) AS 'unique_out_ip'
            , COUNT(DISTINCT src, dst, port) AS 'unique_out_conn'
            , SUM(links) AS 'total_out'
            , SUM(bytes_sent) AS 'b_s'
            , SUM(bytes_received) AS 'b_r'
            , MAX((bytes_sent + bytes_received) / duration) AS 'max_bps'
            , MIN((bytes_sent + bytes_received) / duration) AS 'min_bps'
            , SUM(bytes_sent + bytes_received) AS 'sum_b'
            , SUM(packets_sent) AS 'p_s'
            , SUM(packets_received) AS 'p_r'
            , SUM(duration * links) AS 'duration'
            , GROUP_CONCAT(DISTINCT protocol SEPARATOR ",") AS 'protocol'
            FROM {prefix}Links
            WHERE src BETWEEN $start AND $end
            GROUP BY 's1'
        ) AS l_out
            ON n.ipstart = l_out.s1
        LEFT JOIN (
            SELECT $start AS 's1'
            , COUNT(DISTINCT src) AS 'unique_in_ip'
            , COUNT(DISTINCT src, dst, port) AS 'unique_in_conn'
            , SUM(links) AS 'total_in'
            , SUM(bytes_sent) AS 'b_s'
            , SUM(bytes_received) AS 'b_r'
            , MAX((bytes_sent + bytes_received) / duration) AS 'max_bps'
            , MIN((bytes_sent + bytes_received) / duration) AS 'min_bps'
            , SUM(bytes_sent + bytes_received) AS 'sum_b'
            , SUM(packets_sent) AS 'p_s'
            , SUM(packets_received) AS 'p_r'
            , SUM(duration) AS 'duration'
            , COUNT(DISTINCT port) AS 'ports_used'
            , GROUP_CONCAT(DISTINCT protocol SEPARATOR ",") AS 'protocol'
            FROM {prefix}Links
            WHERE dst BETWEEN $start AND $end
            GROUP BY 's1'
        ) AS l_in
            ON n.ipstart = l_in.s1
        LEFT JOIN (
            SELECT $start AS 's1'
            , COUNT(ipstart) AS 'endpoints'
            FROM Nodes
            WHERE ipstart = ipend AND ipstart BETWEEN $start AND $end
        ) AS children
            ON n.ipstart = children.s1
        LEFT JOIN (
            SELECT $start AS 's1'
                , (MAX(TIME_TO_SEC(timestamp)) - MIN(TIME_TO_SEC(timestamp))) AS 'seconds'
            FROM {prefix}Links
            GROUP BY 's1'
        ) AS t
            ON n.ipstart = t.s1
        LIMIT 1;
    """.format(prefix=prefix)
    results = common.db.query(query, vars=qvars)

    if len(results) == 1:
        return results[0]
    else:
        return {}


def set_node_info(address, data):
    r = common.determine_range_string(address)
    where = {"ipstart": r[0], "ipend": r[1]}
    common.db.update('Nodes', where, **data)


def get_port_info(port):
    if isinstance(port, list):
        arg = "({0})".format(",".join(port))
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


def get_table_info(clauses, page, page_size, order_by, order_dir):
    WHERE = " && ".join(clause.where() for clause in clauses if clause.where())
    if WHERE:
        WHERE = "WHERE " + WHERE

    HAVING = " && ".join(clause.having() for clause in clauses if clause.having())
    if HAVING:
        HAVING = "HAVING " + HAVING

    #      ['address', 'alias', 'role', 'environment', 'tags', 'bytes', 'packets', 'protocols']
    cols = ['nodes.ipstart', 'nodes.alias', '(conn_in / (conn_in + conn_out))', 'env', 'CONCAT(tags, parent_tags)', '(bytes_in + bytes_out)', '(packets_in + packets_out)', 'CONCAT(proto_in, proto_out)']
    ORDERBY = ""
    if 0 <= order_by < len(cols) and order_dir in ['asc', 'desc']:
        ORDERBY = "ORDER BY {0} {1}".format(cols[order_by], order_dir)

    # note: group concat max length is default at 1024.
    # if info is lost, try:
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
        prefix=get_settings_cached()['prefix'])

    info = list(common.db.query(query))
    return info


settingsCache = {}


def get_settings_cached():
    global settingsCache
    if not settingsCache:
        settingsCache = get_settings()
    settingsCache['prefix'] = "ds_{0}_".format(str(settingsCache['datasource']['id']))
    return settingsCache


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
    else:
        where = "id={0}".format(settings['datasource'])
        ds = common.db.select("Datasources", where=where, limit=1)
        if len(ds) == 1:
            settings['datasource'] = dict(ds[0])
        else:
            settings['datasource'] = None

    # keep the cache up to date
    global settingsCache
    settingsCache = settings

    return settings


def get_datasource(id):
    rows = common.db.select("Datasources", where="id={0}".format(int(id)), limit=1)
    if len(rows) == 1:
        return rows[0]
    return None


def delete_custom_tags():
    common.db.delete("Tags", "1")

def delete_custom_envs():
    common.db.update("Nodes", "1", env=common.web.sqlliteral("NULL"))

def delete_custom_hostnames():
    common.db.update("Nodes", "1", alias=common.web.sqlliteral("NULL"))

def delete_connections(ds):
    if len(common.db.select("Datasources", where={'id': ds})) == 1:
        prefix = "ds_{0}_".format(ds)
        common.db.delete("{0}Links".format(prefix), "1")
        common.db.delete("{0}LinksIn".format(prefix), "1")
        common.db.delete("{0}LinksOut".format(prefix), "1")


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
    settingsCache = {}


def print_dict(d, indent = 0):
    for k,v in d.iteritems():
        if type(v) == dict:
            print("{0}{1:>20s}: ".format(indent * 4 * " ", k))
            print_dict(v, indent + 1)
        else:
            print("{0}{1:>20s}: {2}".format(indent*4*" ", k, repr(v)))