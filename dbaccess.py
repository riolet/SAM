import web
import common
import json
import time


def test_database():
    result = 0
    try:
        common.db.query("SELECT 1 FROM MasterNodes LIMIT 1;")
    except Exception as e:
        result = e[0]
        # see http://dev.mysql.com/doc/refman/5.7/en/error-messages-server.html for codes
        # if e[0] == 1049:  # Unknown database 'samapper'
        #     Common.create_database()
        #     return self.GET(name)
        # elif e[0] == 1045:  # Access Denied for '%s'@'%s' (using password: (YES|NO))
        #     rows = [e[1], "Check you username / password? (dbconfig_local.py)"]
    return result


def create_database():
    params = common.dbconfig.params.copy()
    params.pop('db')
    connection = web.database(**params)

    connection.query("CREATE DATABASE IF NOT EXISTS samapper;")

    exec_sql("./sql/setup_database.sql")

    reset_port_names()


def parse_sql_file(path):
    with open(path, 'r') as f:
        lines = f.readlines()
    # remove comment lines
    lines = [i for i in lines if not i.startswith("--")]
    # join into one long string
    script = " ".join(lines)
    # split string into a list of commands
    commands = script.split(";")
    # ignore empty statements (like trailing newlines)
    commands = filter(lambda x: bool(x.strip()), commands)
    return commands


def exec_sql(path):
    commands = parse_sql_file(path)
    for command in commands:
        common.db.query(command)


def reset_port_names():
    # drop and recreate the table
    exec_sql("./sql/setup_LUTs.sql")

    with open("./sql/default_port_data.json", 'rb') as f:
        port_data = json.loads("".join(f.readlines()))

    ports = port_data["ports"].values()
    for port in ports:
        if len(port['name']) > 10:
            port['name'] = port['name'][:10]
        if len(port['description']) > 255:
            port['description'] = port['description'][:255]

    common.db.multiple_insert('portLUT', values=ports)


def get_timerange():
    rows = common.db.query("SELECT MIN(timestamp) AS 'min', MAX(timestamp) AS 'max' FROM MasterLinks;")
    row = rows[0]
    return {'min': time.mktime(row['min'].timetuple()), 'max': time.mktime(row['max'].timetuple())}


def get_nodes(ip_start, ip_end):
    diff = ip_end - ip_start
    if diff > 16777215:
        # check Nodes8
        # rows = common.db.select("Nodes8")
        rows = common.db.select("MasterNodes", where="subnet=8")
    elif diff > 65536:
        # check Nodes16
        rows = common.db.select("MasterNodes", where="subnet=16 && ipstart BETWEEN {0} AND {1}".format(ip_start, ip_end))
    elif diff > 255:
        # check Nodes24
        rows = common.db.select("MasterNodes", where="subnet=24 && ipstart BETWEEN {0} AND {1}".format(ip_start, ip_end))
    elif diff > 0:
        # check Nodes32
        rows = common.db.select("MasterNodes", where="subnet=32 && ipstart BETWEEN {0} AND {1}".format(ip_start, ip_end))
    else:
        rows = []
    return rows


def get_links(ip_start, ip_end, inbound, port_filter=None, timerange=None):
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
    where = build_where_clause(timerange, port_filter)

    if ports:
        select = "src_start, src_end, dst_start, dst_end, port, sum(links) AS 'links'"
        group_by = "GROUP BY src_start, src_end, dst_start, dst_end, port"
    else:
        select = "src_start, src_end, dst_start, dst_end, sum(links) AS 'links'"
        group_by = "GROUP BY src_start, src_end, dst_start, dst_end"

    if inbound:
        query = """
        SELECT {select}
        FROM MasterLinksIn
        WHERE dst_start = $start && dst_end = $end
         {where}
        {group_by}
        """.format(where=where, select=select, group_by=group_by)
    else:
        query = """
        SELECT {select}
        FROM MasterLinksOut
        WHERE src_start = $start && src_end = $end
         {where}
        {group_by}
        """.format(where=where, select=select, group_by=group_by)
    qvars = {"start": ip_start, "end": ip_end}
    rows = list(common.db.query(query, vars=qvars))
    return rows


def build_where_clause(timestamp_range=None, port=None, rounding=True):
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

    qvars = {'tstart': t_start, 'tend': t_end, 'port': port}
    WHERE = str(web.db.reparam("\n    && ".join(clauses), qvars))
    if WHERE:
        WHERE = "    && " + WHERE
    return WHERE


def get_details_summary(ip_start, ip_end, timestamp_range=None, port=None):
    WHERE = build_where_clause(timestamp_range=timestamp_range, port=port)

    query = """
        SELECT (
            SELECT COUNT(DISTINCT src)
                FROM MasterLinks
                WHERE dst BETWEEN $start AND $end
                 {0}) AS 'unique_in'
            , (SELECT COUNT(DISTINCT dst)
                FROM MasterLinks
                WHERE src BETWEEN $start AND $end
                 {0}) AS 'unique_out'
            , (SELECT COUNT(DISTINCT port)
                FROM MasterLinks
                WHERE dst BETWEEN $start AND $end
                 {0}) AS 'unique_ports';""".format(WHERE)

    query2 = """
    SELECT `inputs`.ips AS 'unique_in'
        , `outputs`.ips AS 'unique_out'
        , `inputs`.ports AS 'unique_ports'
    FROM
      (SELECT COUNT(DISTINCT src) AS 'ips', COUNT(DISTINCT port) AS 'ports'
        FROM MasterLinks
        WHERE dst BETWEEN $start AND $end
    ) AS `inputs`
    JOIN (SELECT COUNT(DISTINCT dst) AS 'ips'
        FROM MasterLinks
        WHERE src BETWEEN $start AND $end
    ) AS `outputs`;""".format(WHERE)

    qvars = {'start': ip_start, 'end': ip_end}
    rows = common.db.query(query, vars=qvars)
    row = rows[0]
    return row


def get_details_connections(ip_start, ip_end, inbound, timestamp_range=None, port=None, page=1, page_size=50, order="-links"):
    sort_options = ['links', 'src', 'dst', 'port', 'sum_bytes', 'sum_packets', 'protocols', 'avg_duration']
    qvars = {
        'start': ip_start,
        'end': ip_end,
        'page': page_size * (page-1),
        'page_size': page_size,
        'WHERE': build_where_clause(timestamp_range, port)
    }
    if inbound:
        qvars['collected'] = "src"
        qvars['filtered'] = "dst"
    else:
        qvars['filtered'] = "src"
        qvars['collected'] = "dst"

    if order and order[0] == '-':
        sort_dir = "DESC"
    else:
        sort_dir = "ASC"
    if order and order[1:] in sort_options:
        sort_by = order[1:]
    else:
        sort_by = sort_options[0]
    if sort_by in ['port', 'src', 'dst']:
        sort_by = "`MasterLinks`." + sort_by

    qvars['order'] = "{0} {1}".format(sort_by, sort_dir)

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
            FROM MasterLinks
            WHERE {filtered} BETWEEN $start AND $end
             {WHERE}
            GROUP BY `MasterLinks`.src, `MasterLinks`.dst, `MasterLinks`.port
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
        'WHERE': build_where_clause(timestamp_range, port)
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
        FROM MasterLinks
        WHERE dst BETWEEN $start AND $end
         {WHERE}
        GROUP BY port
        ORDER BY {order}
        LIMIT $first, $size;
    """.format(**qvars)
    return list(common.db.query(query, vars=qvars))


def get_details_children(ip_range, subnet, page, page_size, order):
    sort_options = ['ipstart', 'hostname', 'endpoints', 'ratio']
    start = ip_range[0]
    end = ip_range[1]
    quotient = ip_range[2]
    child_subnet_start = subnet + 1
    child_subnet_end = subnet + 8
    first_result = (page - 1) * page_size
    qvars = {'ip_start': start,
             'ip_end': end,
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
        FROM MasterNodes AS `n`
        LEFT JOIN (
            SELECT dst_start DIV $quot * $quot AS 'low'
                , dst_end DIV $quot * $quot + $quot_1 AS 'high'
                , sum(links) AS 'links'
            FROM MasterLinksIn
            GROUP BY low, high
            ) AS `l_in`
        ON `l_in`.low = `n`.ipstart AND `l_in`.high = `n`.ipend
        LEFT JOIN (
            SELECT src_start DIV $quot * $quot AS 'low'
                , src_end DIV $quot * $quot + $quot_1 AS 'high'
                , sum(links) AS 'links'
            FROM MasterLinksOut
            GROUP BY low, high
            ) AS `l_out`
        ON `l_out`.low = `n`.ipstart AND `l_out`.high = `n`.ipend
        LEFT JOIN (
            SELECT ipstart DIV $quot * $quot AS 'low'
                , ipend DIV $quot * $quot + $quot_1 AS 'high'
                , COUNT(ipstart) AS 'kids'
            FROM MasterNodes
            WHERE ipstart = ipend
            GROUP BY low, high
            ) AS `sn`
        ON `sn`.low = `n`.ipstart AND `sn`.high = `n`.ipend
        WHERE `n`.ipstart BETWEEN $ip_start AND $ip_end
            AND `n`.subnet BETWEEN $s_start AND $s_end
        ORDER BY {order}
        LIMIT $first, $size;
        """.format(order=qvars['order'])
    return list(common.db.query(query, vars=qvars))


def get_tags(address):
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


def get_node_info(address):
    ipstart, ipend = common.determine_range_string(address)
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
        FROM (
            SELECT ipstart, subnet, alias AS 'hostname'
            FROM MasterNodes
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
            FROM MasterLinks
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
            FROM MasterLinks
            WHERE dst BETWEEN $start AND $end
            GROUP BY 's1'
        ) AS l_in
            ON n.ipstart = l_in.s1
        LEFT JOIN (
            SELECT $start AS 's1'
            , COUNT(ipstart) AS 'endpoints'
            FROM MasterNodes
            WHERE ipstart = ipend AND ipstart BETWEEN $start AND $end
        ) AS children
            ON n.ipstart = children.s1
        LEFT JOIN (
            SELECT $start AS 's1'
                , (MAX(TIME_TO_SEC(timestamp)) - MIN(TIME_TO_SEC(timestamp))) AS 'seconds'
            FROM MasterLinks
            GROUP BY 's1'
        ) AS t
            ON n.ipstart = t.s1
        LIMIT 1;
    """
    qvars = {"start": ipstart, "end": ipend}
    results = common.db.query(query, vars=qvars)

    if len(results) == 1:
        return results[0]
    else:
        return {}


def set_node_info(address, data):
    print("-" * 50)
    print("Setting node info!")
    print("type data: " + str(type(data)))
    print(data)
    print("-" * 50)
    r = common.determine_range_string(address)
    where = {"ipstart": r[0], "ipend": r[1]}
    common.db.update('Nodes', where, **data)


def get_port_info(port):
    if isinstance(port, list):
        arg = "("
        for i in port:
            arg += str(i) + ","
        arg = arg[:-1] + ")"
    else:
        arg = "({0})".format(port)
    query = """
        SELECT portLUT.port, portLUT.active, portLUT.name, portLUT.description,
            portAliasLUT.name AS alias_name,
            portAliasLUT.description AS alias_description
        FROM portLUT
        LEFT JOIN portAliasLUT
            ON portLUT.port=portAliasLUT.port
        WHERE portLUT.port IN {0}
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

    # update portAliasLUT database of names to include the new information
    exists = common.db.select('portAliasLUT', what="1", where={"port": port})

    if len(exists) == 1:
        kwargs = {}
        if 'alias_name' in data:
            kwargs['name'] = alias_name
        if 'alias_description' in data:
            kwargs['description'] = alias_description
        if kwargs:
            common.db.update('portAliasLUT', {"port": port}, **kwargs)
    else:
        common.db.insert('portAliasLUT', port=port, name=alias_name, description=alias_description)

    # update portLUT database of default values to include the missing information
    exists = common.db.select('portLUT', what="1", where={"port": port})
    if len(exists) == 1:
        if 'active' in data:
            common.db.update('portLUT', {"port": port}, active=active)
    else:
        common.db.insert('portLUT', port=port, active=active, tcp=1, udp=1, name="", description="")


def get_table_info(clauses, page, page_size, order_by, order_dir):
    WHERE = " && ".join(clause.where() for clause in clauses if clause.where() and clause.enabled)
    if WHERE:
        WHERE = "WHERE " + WHERE

    HAVING = " && ".join(clause.having() for clause in clauses if clause.having() and clause.enabled)
    if HAVING:
        HAVING = "HAVING " + HAVING

    print("\t=====" * 10)
    print("Sort By!")
    print("order_by = {0}".format(order_by))
    print("order_dir = {0}".format(order_dir))

    #      ['address', 'alias', 'role', 'environment', 'tags', 'bytes', 'packets']
    cols = ['nodes.ipstart', 'nodes.alias', '(conn_in / (conn_in + conn_out))', 'env', 'CONCAT(tags, parent_tags)', '(bytes_in + bytes_out)', '(packets_in + packets_out)']
    ORDERBY = ""
    if 0 <= order_by < len(cols) and order_dir in ['asc', 'desc']:
        ORDERBY = "ORDER BY {0} {1}".format(cols[order_by], order_dir)
    print("ORDER BY {0}".format(ORDERBY))
    print("\t=====" * 10)
    # note: group concat max length is default at 1024.
    # if info is lost, try:
    # SET group_concat_max_len = 2048
    query = """
    SELECT CONCAT(decodeIP(ipstart), CONCAT('/', subnet)) AS 'address'
        , COALESCE(nodes.alias, '') AS 'alias'
        , COALESCE((
            SELECT env
            FROM MasterNodes nz
            WHERE nodes.ipstart >= nz.ipstart AND nodes.ipend <= nz.ipend AND env IS NOT NULL AND env != "inherit"
            ORDER BY (nodes.ipstart - nz.ipstart + nz.ipend - nodes.ipend) ASC
            LIMIT 1
        ), 'production') AS "env"
        , COALESCE((SELECT SUM(links)
            FROM MasterLinksOut AS l_out
            WHERE l_out.src_start = nodes.ipstart
              AND l_out.src_end = nodes.ipend
         ),0) AS 'conn_out'
        , COALESCE((SELECT SUM(links)
            FROM MasterLinksIn AS l_in
            WHERE l_in.dst_start = nodes.ipstart
              AND l_in.dst_end = nodes.ipend
         ),0) AS 'conn_in'
        , COALESCE((SELECT SUM(bytes)
            FROM MasterLinksOut AS l_out
            WHERE l_out.src_start = nodes.ipstart
              AND l_out.src_end = nodes.ipend
         ),0) AS 'bytes_out'
        , COALESCE((SELECT SUM(bytes)
            FROM MasterLinksIn AS l_in
            WHERE l_in.dst_start = nodes.ipstart
              AND l_in.dst_end = nodes.ipend
         ),0) AS 'bytes_in'
        , COALESCE((SELECT SUM(packets)
            FROM MasterLinksOut AS l_out
            WHERE l_out.src_start = nodes.ipstart
              AND l_out.src_end = nodes.ipend
         ),0) AS 'packets_out'
        , COALESCE((SELECT SUM(packets)
            FROM MasterLinksIn AS l_in
            WHERE l_in.dst_start = nodes.ipstart
              AND l_in.dst_end = nodes.ipend
         ),0) AS 'packets_in'
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
    FROM MasterNodes AS nodes
    {WHERE}
    {HAVING}
    {ORDER}
    LIMIT {START},{RANGE};
    """.format(
        WHERE=WHERE,
        HAVING=HAVING,
        ORDER=ORDERBY,
        START=page * page_size,
        RANGE=page_size + 1)

    info = list(common.db.query(query))
    return info
