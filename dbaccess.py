import web
import common
import json


def test_database():
    result = 0
    try:
        common.db.query("SELECT 1 FROM Syslog LIMIT 1;")
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


def determine_range(ip8=-1, ip16=-1, ip24=-1, ip32=-1):
    low = 0x00000000
    high = 0xFFFFFFFF
    quot = 1
    if 0 <= ip8 <= 255:
        low = (ip8 << 24)  # 172.0.0.0
        if 0 <= ip16 <= 255:
            low |= (ip16 << 16)  # 172.19.0.0
            if 0 <= ip24 <= 255:
                low |= (ip24 << 8)
                if 0 <= ip32 <= 255:
                    low |= ip32
                    high = low
                else:
                    high = low | 0xFF
                    quot = 0x1
            else:
                high = low | 0xFFFF
                quot = 0x100
        else:
            high = low | 0xFFFFFF
            quot = 0x10000
    else:
        quot = 0x1000000
    return low, high, quot


def get_nodes(ip8=-1, ip16=-1, ip24=-1, ip32=-1):
    if ip8 < 0 or ip8 > 255:
        # check Nodes8
        rows = common.db.select("Nodes8")
    elif ip16 < 0 or ip16 > 255:
        # check Nodes16
        rows = common.db.where("Nodes16",
                               ip8=ip8)
    elif ip24 < 0 or ip24 > 255:
        # check Nodes24
        rows = common.db.where("Nodes24",
                               ip8=ip8,
                               ip16=ip16)
    elif ip32 < 0 or ip32 > 255:
        # check Nodes32
        rows = common.db.where("Nodes32",
                               ip8=ip8,
                               ip16=ip16,
                               ip24=ip24)
    else:
        rows = []
    return rows


def build_links_query(ip, is_dest, ports, port_filter, timerange):
    """
    This helper function builds a query to fulfill the needs of the two "get_links_in/out" functions.

    :param ip: An array of integer ip segments. as in: "a.b.c.d" -> [a, b, c, d]
    :param is_dest: True if the IP specifies a destination. False if the IP specifies a source.
    :param ports: True if the user want's port information in the query. False to omit.
    :param filter: Either a port number to filter by, or None to do no filtering.
    :param timerange: A tuple of (start_timestamp, end_timestamp) to filter results by.
    :return: The db query as a string to get connection information from the database.
    """
    # FROM portion
    table = "Links" + str(len(ip) * 8)
    FROM = table

    # SELECT portion
    selects = ["source8", "dest8", "source16", "dest16", "source24", "dest24", "source32", "dest32"]
    SELECT = ", ".join(selects[:len(ip) * 2])
    if ports:
        SELECT += ", port".format(table)
    SELECT += ", SUM(links) as links, MAX(x1) as x1, MAX(y1) as y1, MAX(x2) as x2, MAX(y2) as y2"

    # WHERE portion
    if is_dest:
        parts = ["dest{0} = $seg{1}".format(i * 8, i) for i in range(1, len(ip) + 1)]
    else:
        parts = ["source{0} = $seg{1}".format(i * 8, i) for i in range(1, len(ip) + 1)]
    WHERE = "\n\t&& ".join(parts)
    if timerange:
        WHERE += "\n\t&& timestamp BETWEEN FROM_UNIXTIME($tstart) AND FROM_UNIXTIME($tend)"
    if port_filter:
        WHERE += "\n\t&& port = $filter"

    # GROUP BY portion
    GROUP_BY = ", ".join(selects[:len(ip) * 2])
    if ports:
        GROUP_BY += ", port"

    # replacement variables
    qvars = dict([("seg{0}".format(i + 1), str(v)) for i, v in enumerate(ip)])
    if port_filter:
        qvars['filter'] = port_filter
    if timerange:
        qvars['tstart'] = timerange[0]
        qvars['tend'] = timerange[1]

    # final query
    query = "SELECT {0}\nFROM {1}\nWHERE {2}\nGROUP BY {3}".format(SELECT, FROM, WHERE, GROUP_BY)
    query = common.db.query(query, vars=qvars, _test=True)

    return query


def get_links_in(ip8, ip16=-1, ip24=-1, ip32=-1, port_filter=None, timerange=None):
    """
    This function returns a list of the connections coming in to a given node from the rest of the graph.

    * The connections are aggregated into groups based on the first diverging ancestor.
        that means that connections to destination 1.2.3.4
        that come from source 1.9.*.* will be grouped together as a single connection.

    * for /8, /16, and /24, `SourceIP` -> `DestIP` make a unique connection.
    * for /32, `SourceIP` -> `DestIP` : `Port` make a unique connection.

    * If filter is provided, only connections over the given port are considered.

    * If timerange is provided, only connections that occur within the given time range are considered.

    :param ip8:  The first  segment of the IPv4 address: __.xx.xx.xx
    :param ip16: The second segment of the IPv4 address: xx.__.xx.xx
    :param ip24: The third  segment of the IPv4 address: xx.xx.__.xx
    :param ip32: The fourth segment of the IPv4 address: xx.xx.xx.__
    :param filter:  Only consider connections using this destination port. Default is no filtering.
    :param timerange:  Tuple of (start, end) timestamps. Only connections happening
    during this time period are considered.
    :return: A list of db results formated as web.storage objects (used like dictionaries)
    """
    if 0 <= ip32 <= 255:
        query = build_links_query([ip8, ip16, ip24, ip32], is_dest=True, ports=True, port_filter=port_filter,
                                  timerange=timerange)
        inputs = list(common.db.query(query))
    elif 0 <= ip24 <= 255:
        query = build_links_query([ip8, ip16, ip24], is_dest=True, ports=False, port_filter=port_filter,
                                  timerange=timerange)
        inputs = list(common.db.query(query))
    elif 0 <= ip16 <= 255:
        query = build_links_query([ip8, ip16], is_dest=True, ports=False, port_filter=port_filter,
                                  timerange=timerange)
        inputs = list(common.db.query(query))
    elif 0 <= ip8 <= 255:
        query = build_links_query([ip8], is_dest=True, ports=False, port_filter=port_filter,
                                  timerange=timerange)
        inputs = list(common.db.query(query))
    else:
        inputs = []
    return inputs


def get_links_out(ip8, ip16=-1, ip24=-1, ip32=-1, port_filter=None, timerange=None):
    """
    This function returns a list of the connections going out of a given node from the rest of the graph.

    * The connections are aggregated into groups based on the first diverging ancestor.
        that means that connections to destination 1.2.3.4
        that come from source 1.9.*.* will be grouped together as a single connection.

    * for /8, /16, and /24, `SourceIP` -> `DestIP` make a unique connection.
    * for /32, `SourceIP` -> `DestIP` : `Port` make a unique connection.

    * If filter is provided, only connections over the given port are considered.

    * If timerange is provided, only connections that occur within the given time range are considered.

    :param ip8:  The first  segment of the IPv4 address: __.xx.xx.xx
    :param ip16: The second segment of the IPv4 address: xx.__.xx.xx
    :param ip24: The third  segment of the IPv4 address: xx.xx.__.xx
    :param ip32: The fourth segment of the IPv4 address: xx.xx.xx.__
    :param filter:  Only consider connections using this destination port. Default is no filtering.
    :param timerange:  Tuple of (start, end) timestamps. Only connections happening
    during this time period are considered.
    :return: A list of db results formated as web.storage objects (used like dictionaries)
    """
    if 0 <= ip32 <= 255:
        query = build_links_query([ip8, ip16, ip24, ip32], is_dest=False, ports=True, port_filter=port_filter,
                                  timerange=timerange)
        outputs = list(common.db.query(query))
    elif 0 <= ip24 <= 255:
        query = build_links_query([ip8, ip16, ip24], is_dest=False, ports=False, port_filter=port_filter,
                                  timerange=timerange)
        outputs = list(common.db.query(query))
    elif 0 <= ip16 <= 255:
        query = build_links_query([ip8, ip16], is_dest=False, ports=False, port_filter=port_filter,
                                  timerange=timerange)
        outputs = list(common.db.query(query))
    elif 0 <= ip8 <= 255:
        query = build_links_query([ip8], is_dest=False, ports=False, port_filter=port_filter,
                                  timerange=timerange)
        outputs = list(common.db.query(query))
    else:
        outputs = []
    return outputs


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
        clauses.append("Timestamp BETWEEN FROM_UNIXTIME($tstart) AND FROM_UNIXTIME($tend)")

    if port:
        clauses.append("DestinationPort = $port")

    qvars = {'tstart': t_start, 'tend': t_end, 'port': port}
    WHERE = str(web.db.reparam("\n    && ".join(clauses), qvars))
    if WHERE:
        WHERE = "    && " + WHERE
    return WHERE


def get_details_summary(ip_range, timestamp_range=None, port=None):
    WHERE = build_where_clause(timestamp_range=timestamp_range, port=port)
    query = """
           SELECT tableA.unique_in, tableB.unique_out, tableC.unique_ports
           FROM
               (SELECT COUNT(DISTINCT(SourceIP)) AS 'unique_in'
               FROM Syslog
               WHERE DestinationIP >= $start && DestinationIP <= $end
                {0})
               AS tableA
           JOIN
               (SELECT COUNT(DISTINCT(DestinationIP)) AS 'unique_out'
               FROM Syslog
               WHERE SourceIP >= $start && SourceIP <= $end
                {0})
               AS tableB
           JOIN
               (SELECT COUNT(DISTINCT(DestinationPort)) AS 'unique_ports'
               FROM Syslog
               WHERE DestinationIP >= $start && DestinationIP <= $end
                {0})
               AS tableC;
       """.format(WHERE)
    qvars = {'start': ip_range[0], 'end': ip_range[1]}
    rows = common.db.query(query, vars=qvars)
    row = rows[0]
    return row


def get_details_connections(ip_range, inbound, timestamp_range=None, port=None, limit=50):
    qvars = {
        'start': ip_range[0],
        'end': ip_range[1],
        'limit': limit,
        'WHERE': build_where_clause(timestamp_range, port)
    }
    if inbound:
        qvars['collected'] = "Syslog.SourceIP"
        qvars['filtered'] = "Syslog.DestinationIP"
    else:
        qvars['filtered'] = "Syslog.SourceIP"
        qvars['collected'] = "Syslog.DestinationIP"

    query = """
        SELECT ip, temp.port, links
        FROM
            (SELECT {collected} AS 'ip'
                , Syslog.DestinationPort as 'port'
                , COUNT(*) AS 'links'
            FROM Syslog
            WHERE {filtered} >= $start && {filtered} <= $end
             {WHERE}
            GROUP BY {collected}, Syslog.DestinationPort)
            AS temp
        ORDER BY links DESC
        LIMIT $limit;
    """.format(**qvars)
    return list(common.db.query(query, vars=qvars))


def get_details_ports(ip_range, timestamp_range=None, port=None, limit=50):
    WHERE = build_where_clause(timestamp_range, port)
    query = """
            SELECT temp.port, links
            FROM
                (SELECT DestinationPort AS port, COUNT(*) AS links
                FROM Syslog
                WHERE DestinationIP >= $start && DestinationIP <= $end
                 {0}
                GROUP BY port
                ) AS temp
            ORDER BY links DESC
            LIMIT $limit;
        """.format(WHERE)
    qvars = {'start': ip_range[0], 'end': ip_range[1], 'limit': limit}
    return list(common.db.query(query, vars=qvars))


def get_node_info(address):
    print("-" * 50)
    print("getting node info:")
    print("type: " + str(type(address)))
    print(address)
    print("-" * 50)
    # TODO: placeholder for use getting meta about hosts
    ips = map(int, address.split("."))
    subnet = 8 * len(ips)
    table = "Nodes" + str(subnet)
    WHERE = " && ".join(["ip{0}={1}".format((i+1)*8, ip) for i, ip in enumerate(ips)])
    results = common.db.select(table, where=WHERE, limit=1)

    if len(results) == 1:
        return results[0]
    else:
        return {}


def set_node_info(address, data):
    print("-" * 50)
    print("Setting node info!")
    ips = address.split(".")
    print("type data: " + str(type(data)))
    print(data)
    print("-" * 50)
    if len(ips) == 1:
        common.db.update('Nodes8', {"ip8": ips[0]}, **data)
    if len(ips) == 2:
        common.db.update('Nodes16', {"ip8": ips[0], "ip16": ips[1]}, **data)
    if len(ips) == 3:
        common.db.update('Nodes24', {"ip8": ips[0], "ip16": ips[1],
                                     "ip24": ips[2]}, **data)
    if len(ips) == 4:
        common.db.update('Nodes32', {"ip8": ips[0], "ip16": ips[1],
                                     "ip24": ips[2], "ip32": ips[3]}, **data)


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


def get_table_info(clauses, page, page_size):
    WHERE = " && ".join(clause.where() for clause in clauses if clause.where())
    if WHERE:
        WHERE = "WHERE " + WHERE


    HAVING = " && ".join(clause.having() for clause in clauses if clause.having())
    if HAVING:
        HAVING = "HAVING " + HAVING

    query = """
SELECT CONCAT(decodeIP(ipstart), CONCAT('/', subnet)) AS address
    , alias
    ,COALESCE((SELECT SUM(links)
        FROM LinksOut AS l_out
        WHERE l_out.src_start = nodes.ipstart
          AND l_out.src_end = nodes.ipend
     ),0) AS "conn_out"
    ,COALESCE((SELECT SUM(links)
        FROM LinksIn AS l_in
        WHERE l_in.dst_start = nodes.ipstart
          AND l_in.dst_end = nodes.ipend
     ),0) AS "conn_in"
FROM Nodes AS nodes
{0}
{1}
LIMIT {2},{3};""".format(WHERE, HAVING, page * page_size, page_size + 1)
    info = list(common.db.query(query))
    return info