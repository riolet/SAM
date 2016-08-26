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


def exec_sql(path):
    with open(path, 'r') as f:
        lines = f.readlines()
    # remove comment lines
    lines = [i for i in lines if not i.startswith("--")]
    # join into one long string
    script = " ".join(lines)
    # split string into a list of commands
    commands = script.split(";")

    for command in commands:
        # ignore empty statements (like trailing newlines)
        if command.strip(" \n") == "":
            continue
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


def determineRange(ip8=-1, ip16=-1, ip24=-1, ip32=-1):
    low = 0x00000000
    high = 0xFFFFFFFF
    quot = 1
    if 0 <= ip8 <= 255:
        low = (ip8 << 24)   # 172.0.0.0
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


def getNodes(ip8=-1, ip16=-1, ip24=-1):
    ip8 = int(ip8)
    ip16 = int(ip16)
    ip24 = int(ip24)

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
    else:
        # check Nodes32
        rows = common.db.where("Nodes32",
                               ip8=ip8,
                               ip16=ip16,
                               ip24=ip24)
    return rows


def getLinksIn(ip8, ip16=-1, ip24=-1, ip32=-1, filter=-1):
    if 0 <= ip32 <= 255:
        if filter == -1:
            query = """
                SELECT source8, source16, source24, source32, dest8, dest16, dest24, dest32, Links32.port
                    , links, x1, y1, x2, y2
                FROM Links32
                WHERE dest8 = $seg1
                    && dest16 = $seg2
                    && dest24 = $seg3
                    && dest32 = $seg4
                """
        else:
            query = """
                SELECT source8, source16, source24, source32, dest8, dest16, dest24, dest32, Links32.port
                    , links, x1, y1, x2, y2
                FROM Links32
                WHERE dest8 = $seg1
                    && dest16 = $seg2
                    && dest24 = $seg3
                    && dest32 = $seg4
                    && Links32.port = $filter;
                """
        qvars = {'seg1': str(ip8), 'seg2': str(ip16), 'seg3': str(ip24), 'seg4': str(ip32), 'filter': filter}
        inputs = list(common.db.query(query, vars=qvars))
    elif 0 <= ip24 <= 255:
        if filter == -1:
            query = """
                SELECT source8, source16, source24, dest8, dest16, dest24
                    , SUM(links) as links, MAX(x1) as x1, MAX(y1) as y1, MAX(x2) as x2, MAX(y2) as y2
                FROM Links24
                WHERE dest8 = $seg1
                    && dest16 = $seg2
                    && dest24 = $seg3
                GROUP BY source8, source16, source24, dest8, dest16, dest24;
                """
        else:
            query = """
                SELECT source8, source16, source24, dest8, dest16, dest24, links, x1, y1, x2, y2
                FROM Links24
                WHERE dest8 = $seg1
                    && dest16 = $seg2
                    && dest24 = $seg3
                    && port = $filter;
                """
        qvars = {'seg1': str(ip8), 'seg2': str(ip16), 'seg3': str(ip24), 'filter': filter}
        inputs = list(common.db.query(query, vars=qvars))
    elif 0 <= ip16 <= 255:
        if filter == -1:
            query = """
                SELECT source8, source16, dest8, dest16
                    , SUM(links) as links, MAX(x1) as x1, MAX(y1) as y1, MAX(x2) as x2, MAX(y2) as y2
                FROM Links16
                WHERE dest8 = $seg1
                    && dest16 = $seg2
                GROUP BY source8, source16, dest8, dest16;
                """
        else:
            query = """
                SELECT source8, source16, dest8, dest16, links, x1, y1, x2, y2
                FROM Links16
                WHERE dest8 = $seg1
                    && dest16 = $seg2
                    && port = $filter;
                """
        qvars = {'seg1': str(ip8), 'seg2': str(ip16), 'filter': filter}
        inputs = list(common.db.query(query, vars=qvars))
    elif 0 <= ip8 <= 255:
        if filter == -1:
            query = """
                SELECT source8, dest8
                    , SUM(links) as links, MAX(x1) as x1, MAX(y1) as y1, MAX(x2) as x2, MAX(y2) as y2
                FROM Links8
                WHERE dest8 = $seg1
                GROUP BY source8, dest8;
                """
        else:
            query = """
                SELECT source8, dest8, links, x1, y1, x2, y2
                FROM Links8
                WHERE dest8 = $seg1
                    && port = $filter;
                """
        qvars = {'seg1': str(ip8), 'filter': filter}
        inputs = list(common.db.query(query, vars=qvars))
    else:
        inputs = []

    return inputs


def getLinksOut(ip8, ip16=-1, ip24=-1, ip32=-1, filter=-1):

    if ip8 < 0 or ip8 > 255:
        outputs = []
    elif ip16 == -1 or ip16 < 0 or ip16 > 255:
        if filter == -1:
            query = """
                SELECT source8, dest8
                    , SUM(links) as links, MAX(x1) as x1, MAX(y1) as y1, MAX(x2) as x2, MAX(y2) as y2
                FROM Links8
                WHERE source8 = $seg1
                GROUP BY source8, dest8;
                """
        else:
            query = """
                SELECT source8, dest8, links, x1, y1, x2, y2
                FROM Links8
                WHERE source8 = $seg1
                    && port = $filter;
                """
        qvars = {'seg1': str(ip8), 'filter': filter}
        outputs = list(common.db.query(query, vars=qvars))
    elif ip24 == -1 or ip24 < 0 or ip24 > 255:
        if filter == -1:
            query = """
                SELECT source8, source16, dest8, dest16
                    , SUM(links) as links, MAX(x1) as x1, MAX(y1) as y1, MAX(x2) as x2, MAX(y2) as y2
                FROM Links16
                WHERE source8 = $seg1
                    && source16 = $seg2
                GROUP BY source8, source16, dest8, dest16;
                """
        else:
            query = """
                SELECT source8, source16, dest8, dest16, links, x1, y1, x2, y2
                FROM Links16
                WHERE source8 = $seg1
                    && source16 = $seg2
                    && port = $filter;
                """
        qvars = {'seg1': str(ip8), 'seg2': str(ip16), 'filter': filter}
        outputs = list(common.db.query(query, vars=qvars))
    elif ip32 == -1 or ip32 < 0 or ip32 > 255:
        if filter == -1:
            query = """
                SELECT source8, source16, source24, dest8, dest16, dest24
                    , SUM(links) as links, MAX(x1) as x1, MAX(y1) as y1, MAX(x2) as x2, MAX(y2) as y2
                FROM Links24
                WHERE source8 = $seg1
                    && source16 = $seg2
                    && source24 = $seg3
                GROUP BY source8, source16, source24, dest8, dest16, dest24;
                """
        else:
            query = """
                SELECT source8, source16, source24, dest8, dest16, dest24, links, x1, y1, x2, y2
                FROM Links24
                WHERE source8 = $seg1
                    && source16 = $seg2
                    && source24 = $seg3
                    && port = $filter;
                """
        qvars = {'seg1': str(ip8), 'seg2': str(ip16), 'seg3': str(ip24), 'filter': filter}
        outputs = list(common.db.query(query, vars=qvars))
    else:
        if filter == -1:
            query = """
                SELECT source8, source16, source24, source32, dest8, dest16, dest24, dest32, Links32.port
                    , links, x1, y1, x2, y2
                FROM Links32
                WHERE source8 = $seg1
                    && source16 = $seg2
                    && source24 = $seg3
                    && source32 = $seg4
                """
        else:
            query = """
                SELECT source8, source16, source24, source32, dest8, dest16, dest24, dest32, Links32.port
                    , links, x1, y1, x2, y2
                FROM Links32
                WHERE source8 = $seg1
                    && source16 = $seg2
                    && source24 = $seg3
                    && source32 = $seg4
                    && Links32.port = $filter;
                """
        qvars = {'seg1': str(ip8),
                 'seg2': str(ip16),
                 'seg3': str(ip24),
                 'seg4': str(ip32),
                 'filter': filter}
        outputs = list(common.db.query(query, vars=qvars))

    return outputs


def getDetails(ip8, ip16=-1, ip24=-1, ip32=-1):
    details = {}
    ipRangeStart, ipRangeEnd, ipQuotient = determineRange(ip8, ip16, ip24, ip32)

    query = """
        SELECT tableA.unique_in, tableB.unique_out, tableC.unique_ports
        FROM
            (SELECT COUNT(DISTINCT(SourceIP)) AS 'unique_in'
            FROM Syslog
            WHERE DestinationIP >= $start && DestinationIP <= $end)
            AS tableA
        JOIN
            (SELECT COUNT(DISTINCT(DestinationIP)) AS 'unique_out'
            FROM Syslog
            WHERE SourceIP >= $start && SourceIP <= $end)
            AS tableB
        JOIN
            (SELECT COUNT(DISTINCT(DestinationPort)) AS 'unique_ports'
            FROM Syslog
            WHERE DestinationIP >= $start && DestinationIP <= $end)
            AS tableC;
    """
    qvars = {'start': ipRangeStart, 'end': ipRangeEnd}
    rows = common.db.query(query, vars=qvars)
    row = rows[0]
    details['unique_out'] = row.unique_out
    details['unique_in'] = row.unique_in
    details['unique_ports'] = row.unique_ports

    query = """
        SELECT ip, temp.port, links
        FROM
            (SELECT Syslog.SourceIP AS 'ip'
                , Syslog.DestinationPort as 'port'
                , COUNT(*) AS 'links'
            FROM Syslog
            WHERE DestinationIP >= $start && DestinationIP <= $end
            GROUP BY Syslog.SourceIP, Syslog.DestinationPort)
            AS temp
        ORDER BY links DESC
        LIMIT 50;
    """
    qvars = {'start': ipRangeStart, 'end': ipRangeEnd}
    details['conn_in'] = list(common.db.query(query, vars=qvars))

    query = """
        SELECT ip, temp.port, links
        FROM
            (SELECT Syslog.DestinationIP AS 'ip'
                , Syslog.DestinationPort as 'port'
                , COUNT(*) AS 'links'
            FROM Syslog
            WHERE SourceIP >= $start && SourceIP <= $end
            GROUP BY Syslog.DestinationIP, Syslog.DestinationPort)
            AS temp
        ORDER BY links DESC
        LIMIT 50;
    """
    qvars = {'start': ipRangeStart, 'end': ipRangeEnd}
    details['conn_out'] = list(common.db.query(query, vars=qvars))

    query = """
        SELECT temp.port, links
        FROM
            (SELECT DestinationPort AS port, COUNT(*) AS links
            FROM Syslog
            WHERE DestinationIP >= $start && DestinationIP <= $end
            GROUP BY port
            ) AS temp
        ORDER BY links DESC
        LIMIT 50;
    """
    qvars = {'start': ipRangeStart, 'end': ipRangeEnd}
    details['ports_in'] = list(common.db.query(query, vars=qvars))

    return details


def getNodeInfo(*address):
    print("-"*50)
    print("getting node info:")
    print("type: " + str(type(address)))
    print(address)
    print("-"*50)
    pass


def setNodeInfo(address, data):
    print("-"*50)
    print("Setting node info!")
    ips = address.split(".")
    print("type data: " + str(type(data)))
    print(data)
    print("-"*50)
    if len(ips) == 1:
        common.db.update('Nodes8', {"address": ips[0]}, **data)
    if len(ips) == 2:
        common.db.update('Nodes16', {"parent8": ips[0], "address": ips[1]}, **data)
    if len(ips) == 3:
        common.db.update('Nodes24', {"parent8": ips[0], "parent16": ips[1], "address": ips[2]}, **data)
    if len(ips) == 4:
        common.db.update('Nodes32', {"parent8": ips[0], "parent16": ips[1],
                                     "parent24": ips[2], "address": ips[3]}, **data)


def getPortInfo(port):
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
    info = common.db.query(query)
    return info


def setPortInfo(data):
    # update portAliasLUT database of names to include the new information
    exists = common.db.select('portAliasLUT', what="1", where={"port": data['port']})
    if len(exists) == 1:
        common.db.update('portAliasLUT',
                         {"port": data['port']},
                         name=data['alias_name'],
                         description=data['alias_description'])
    else:
        common.db.insert('portAliasLUT', port=data.port, name=data.alias_name, description=data.alias_description)

    # update portLUT database of default values to include the missing information
    exists = common.db.select('portLUT', what="1", where={"port": data['port']})
    if len(exists) == 1:
        common.db.update('portLUT',
                         {"port": data['port']},
                         active=data['active'])
    else:
        common.db.insert('portLUT', port=data.port, active=data['active'], tcp=1, udp=1, name="", description="")


def printLink(row):
    if "source32" in row:
        print formatLink(row.source8, row.source16, row.source24, row.source32,
                         row.dest8, row.dest16, row.dest24, row.dest32)
    elif "source24" in row:
        print formatLink(row.source8, row.source16, row.source24, 0,
                         row.dest8, row.dest16, row.dest24, 0)
    elif "source16" in row:
        print formatLink(row.source8, row.source16, 0, 0,
                         row.dest8, row.dest16, 0, 0)
    elif "source8" in row:
        print formatLink(row.source8, 0, 0, 0,
                         row.dest8, 0, 0, 0)


def formatLink(src8=0, src16=0, src24=0, src32=0, dst8=0, dst16=0, dst24=0, dst32=0):
    return "{0:>15s} --> {1:<15s}".format("{0:d}.{1:d}.{2:d}.{3:d}".format(src8, src16, src24, src32), 
                                          "{0:d}.{1:d}.{2:d}.{3:d}".format(dst8, dst16, dst24, dst32))


def getTableSizes():
    tableSizes = {}

    rows = common.db.select("Nodes8", what="COUNT(*)")
    tableSizes["Nodes8"] = rows[0]["COUNT(*)"]

    rows = common.db.select("Nodes16", what="COUNT(*)")
    tableSizes["Nodes16"] = rows[0]["COUNT(*)"]

    rows = common.db.select("Nodes24", what="COUNT(*)")
    tableSizes["Nodes24"] = rows[0]["COUNT(*)"]

    rows = common.db.select("Nodes32", what="COUNT(*)")
    tableSizes["Nodes32"] = rows[0]["COUNT(*)"]

    rows = common.db.select("Links8", what="COUNT(*)")
    tableSizes["Links8"] = rows[0]["COUNT(*)"]

    rows = common.db.select("Links16", what="COUNT(*)")
    tableSizes["Links16"] = rows[0]["COUNT(*)"]

    rows = common.db.select("Links24", what="COUNT(*)")
    tableSizes["Links24"] = rows[0]["COUNT(*)"]

    rows = common.db.select("Links32", what="COUNT(*)")
    tableSizes["Links32"] = rows[0]["COUNT(*)"]

    rows = common.db.select("Syslog", what="COUNT(*)")
    tableSizes["Syslog"] = rows[0]["COUNT(*)"]

    return tableSizes
