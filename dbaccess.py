import web
import common
import json


def test_database():
    result = 0
    try:
        rows = common.db.query("SELECT * FROM Syslog LIMIT 1;")
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
    with open(path, 'r') as file:
        lines = file.readlines()
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
        if len(port['shortname']) > 10:
            port['shortname'] = port['shortname'][:10]
        if len(port['longname']) > 255:
            port['longname'] = port['longname'][:255]

    common.db.multiple_insert('portLUT', values=ports)


def determineRange(ip1 = -1, ip2 = -1, ip3 = -1, ip4 = -1):
    min = 0x00000000
    max = 0xFFFFFFFF
    quot = 1
    if 0 <= ip1 <= 255:
        min = (ip1 << 24)   # 172.0.0.0
        if 0 <= ip2 <= 255:
            min |= (ip2 << 16)  # 172.19.0.0
            if 0 <= ip3 <= 255:
                min |= (ip3 << 8)
                if 0 <= ip4 <= 255:
                    min |= ip4
                    max = min
                else:
                    max = min | 0xFF
                    quot = 0x1
            else:
                max = min | 0xFFFF
                quot = 0x100
        else:
            max = min | 0xFFFFFF
            quot = 0x10000
    else:
        quot = 0x1000000
    return (min, max, quot)


def getNodes(ipSegment1 = -1, ipSegment2 = -1, ipSegment3 = -1):
    rows = []
    if ipSegment1 == -1 or ipSegment1 < 0 or ipSegment1 > 255:
        # check Nodes8
        rows = common.db.select("Nodes8")
    elif ipSegment2 == -1 or ipSegment2 < 0 or ipSegment2 > 255:
        # check Nodes16
        rows = common.db.where("Nodes16",
                               parent8 = ipSegment1)
    elif ipSegment3 == -1 or ipSegment3 < 0 or ipSegment3 > 255:
        # check Nodes24
        # TODO: This is broken :(
        rows = common.db.where("Nodes24",
                               parent8 = ipSegment1,
                               parent16 = ipSegment2)
    else:
        # check Nodes32
        rows = common.db.where("Nodes32",
                               parent8 = ipSegment1,
                               parent16 = ipSegment2,
                               parent24 = ipSegment3)
    return rows


def getLinksIn(ipSegment1, ipSegment2 = -1, ipSegment3 = -1, ipSegment4 = -1, filter=-1):
    inputs = []

    if ipSegment1 < 0 or ipSegment1 > 255:
        inputs = []
    elif ipSegment2 == -1 or ipSegment2 < 0 or ipSegment2 > 255:
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
        qvars = {'seg1': str(ipSegment1), 'filter':filter}
        inputs = list(common.db.query(query, vars=qvars))
    elif ipSegment3 == -1 or ipSegment3 < 0 or ipSegment3 > 255:
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
        qvars = {'seg1': str(ipSegment1), 'seg2': str(ipSegment2), 'filter':filter}
        inputs = list(common.db.query(query, vars=qvars))
    elif ipSegment4 == -1 or ipSegment4 < 0 or ipSegment4 > 255:
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
        qvars = {'seg1': str(ipSegment1), 'seg2': str(ipSegment2), 'seg3': str(ipSegment3), 'filter': filter}
        inputs = list(common.db.query(query, vars=qvars))
    else:
        if filter == -1:
            query = """
                SELECT source8, source16, source24, source32, dest8, dest16, dest24, dest32, Links32.port
                    , shortname, longname, links, x1, y1, x2, y2
                FROM Links32
                LEFT JOIN portLUT
                ON Links32.port = portLUT.port
                WHERE dest8 = $seg1
                    && dest16 = $seg2
                    && dest24 = $seg3
                    && dest32 = $seg4
                """
        else:
            query = """
                SELECT source8, source16, source24, source32, dest8, dest16, dest24, dest32, Links32.port
                    , shortname, longname, links, x1, y1, x2, y2
                FROM Links32
                LEFT JOIN portLUT
                ON Links32.port = portLUT.port
                WHERE dest8 = $seg1
                    && dest16 = $seg2
                    && dest24 = $seg3
                    && dest32 = $seg4
                    && Links32.port = $filter;
                """
        qvars = {'seg1': str(ipSegment1), 'seg2': str(ipSegment2), 'seg3': str(ipSegment3), 'seg4': str(ipSegment4), 'filter': filter}
        inputs = list(common.db.query(query, vars=qvars))

    return inputs


def getLinksOut(ipSegment1, ipSegment2 = -1, ipSegment3 = -1, ipSegment4 = -1, filter=-1):
    outputs = []

    if ipSegment1 < 0 or ipSegment1 > 255:
        outputs = []
    elif ipSegment2 == -1 or ipSegment2 < 0 or ipSegment2 > 255:
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
        qvars = {'seg1': str(ipSegment1), 'filter': filter}
        outputs = list(common.db.query(query, vars=qvars))
    elif ipSegment3 == -1 or ipSegment3 < 0 or ipSegment3 > 255:
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
        qvars = {'seg1': str(ipSegment1), 'seg2': str(ipSegment2), 'filter': filter}
        outputs = list(common.db.query(query, vars=qvars))
    elif ipSegment4 == -1 or ipSegment4 < 0 or ipSegment4 > 255:
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
        qvars = {'seg1': str(ipSegment1), 'seg2': str(ipSegment2), 'seg3': str(ipSegment3), 'filter': filter}
        outputs = list(common.db.query(query, vars=qvars))
    else:
        if filter == -1:
            query = """
                SELECT source8, source16, source24, source32, dest8, dest16, dest24, dest32, Links32.port
                    , shortname, longname, links, x1, y1, x2, y2
                FROM Links32
                LEFT JOIN portLUT
                ON Links32.port = portLUT.port
                WHERE source8 = $seg1
                    && source16 = $seg2
                    && source24 = $seg3
                    && source32 = $seg4
                """
        else:
            query = """
                SELECT source8, source16, source24, source32, dest8, dest16, dest24, dest32, Links32.port
                    , shortname, longname, links, x1, y1, x2, y2
                FROM Links32
                LEFT JOIN portLUT
                ON Links32.port = portLUT.port
                WHERE source8 = $seg1
                    && source16 = $seg2
                    && source24 = $seg3
                    && source32 = $seg4
                    && Links32.port = $filter;
                """
        qvars = {'seg1': str(ipSegment1), 'seg2': str(ipSegment2), 'seg3': str(ipSegment3), 'seg4': str(ipSegment4), 'filter': filter}
        outputs = list(common.db.query(query, vars=qvars))

    return outputs


def getDetails(ipSegment1, ipSegment2 = -1, ipSegment3 = -1, ipSegment4 = -1):
    details = {}
    ipRangeStart, ipRangeEnd, ipQuotient = determineRange(ipSegment1, ipSegment2, ipSegment3, ipSegment4)

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
        SELECT SourceIP AS 'ip', COUNT(*) AS links
            FROM Syslog
            WHERE DestinationIP >= $start && DestinationIP <= $end
            GROUP BY ip
            ORDER BY links DESC
            LIMIT 50;
    """
    qvars = {'start': ipRangeStart, 'end': ipRangeEnd}
    details['conn_in'] = list(common.db.query(query, vars=qvars))

    query = """
        SELECT DestinationIP AS 'ip', COUNT(*) AS links
            FROM Syslog
            WHERE SourceIP >= $start && SourceIP <= $end
            GROUP BY ip
            ORDER BY links DESC
            LIMIT 50;
    """
    qvars = {'start': ipRangeStart, 'end': ipRangeEnd}
    details['conn_out'] = list(common.db.query(query, vars=qvars))

    query = """
        SELECT DestinationPort AS port, COUNT(*) AS links
            FROM Syslog
            WHERE DestinationIP >= $start && DestinationIP <= $end
            GROUP BY port
            ORDER BY links DESC
            LIMIT 50;
    """
    qvars = {'start': ipRangeStart, 'end': ipRangeEnd}
    details['ports_in'] = list(common.db.query(query, vars=qvars))

    return details


def printLink(row):
    if "source32" in row:
        print formatLink(row.source8, row.source16, row.source24, row.source32, row.dest8, row.dest16, row.dest24, row.dest32)
    elif "source24" in row:
        print formatLink(row.source8, row.source16, row.source24, 0, row.dest8, row.dest16, row.dest24, 0)
    elif "source16" in row:
        print formatLink(row.source8, row.source16, 0, 0, row.dest8, row.dest16, 0, 0)
    elif "source8" in row:
        print formatLink(row.source8, 0, 0, 0, row.dest8, 0, 0, 0)


def formatLink(src8 = 0, src16 = 0, src24 = 0, src32 = 0, dst8 = 0, dst16 = 0, dst24 = 0, dst32 = 0):
    return "{0:>15s} --> {1:<15s}".format("{0:d}.{1:d}.{2:d}.{3:d}".format(src8, src16, src24, src32), "{0:d}.{1:d}.{2:d}.{3:d}".format(dst8, dst16, dst24, dst32))


def getTableSizes():
    tableSizes= {};

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
