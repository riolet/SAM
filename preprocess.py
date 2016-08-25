"""
Preprocess the data in the database's upload table Syslog
"""

import common
import dbaccess


def clean_tables():
    common.db.query("DROP TABLE IF EXISTS Links32;")
    common.db.query("DROP TABLE IF EXISTS Links24;")
    common.db.query("DROP TABLE IF EXISTS Links16;")
    common.db.query("DROP TABLE IF EXISTS Links8;")
    common.db.query("DROP TABLE IF EXISTS Nodes32;")
    common.db.query("DROP TABLE IF EXISTS Nodes24;")
    common.db.query("DROP TABLE IF EXISTS Nodes16;")
    common.db.query("DROP TABLE IF EXISTS Nodes8;")

    dbaccess.exec_sql("./sql/setup_tables.sql")


def import_nodes():

    # count(children) / 127.5 + 0.5) gives a number between 0.5 and 2.5
    # radius used to be:
    #    (COUNT(cluster.child) / 127.5 + 0.5) * 6000
    # instead of:
    #    6000

    # Get all /8 nodes. Load them into Nodes8
    query = """
        INSERT INTO Nodes8 (address, connections, children, x, y, radius)
        SELECT cluster.nip AS address
            , SUM(cluster.conns) AS connections
            , COUNT(cluster.child) AS children
            , (331776 * (cluster.nip % 16) / 7.5 - 331776) as x
            , (331776 * (cluster.nip DIV 16) / 7.5 - 331776) as y
            , 20736 as radius
        FROM
            (SELECT ip DIV 16777216 AS 'nip'
                , (ip - (ip DIV 16777216) * 16777216) DIV 65536 AS 'child'
                , COUNT(*) AS 'conns'
            FROM (
                (SELECT SourceIP AS ip
                FROM Syslog)
                UNION ALL
                (SELECT DestinationIP AS ip
                FROM Syslog)
            ) AS result
            GROUP BY nip, child
        ) AS cluster
        GROUP BY address;
    """
    qvars = {"radius": 331776}
    common.db.query(query, vars=qvars)

    # Get all the /16 nodes. Load these into Nodes16
    query = """
        INSERT INTO Nodes16 (parent8, address, connections, children, x, y, radius)
        SELECT cluster.parent8, cluster.address, cluster.connections, cluster.children
            , ((Nodes8.radius * (cluster.address MOD 16) / 7.5 - Nodes8.radius) + Nodes8.x) as x
            , ((Nodes8.radius * (cluster.address DIV 16) / 7.5 - Nodes8.radius) + Nodes8.y) as y
            , 864 as radius
        FROM
            (SELECT aggregate.pip8 AS parent8, aggregate.nip AS address
                , SUM(aggregate.conns) AS connections, COUNT(aggregate.child) AS children
            FROM
                (SELECT ip DIV 16777216 AS 'pip8'
                    , (ip MOD 16777216) DIV 65536 AS 'nip'
                    , (ip MOD 65536) DIV 256 AS 'child'
                    , COUNT(*) AS 'conns'
                FROM (
                    (SELECT SourceIP AS ip
                    FROM Syslog)
                    UNION ALL
                    (SELECT DestinationIP AS ip
                    FROM Syslog)
                ) as result
                GROUP BY pip8, nip, child
            ) AS aggregate
            GROUP BY parent8, address) as cluster
            JOIN Nodes8
            ON Nodes8.address = cluster.parent8
        """
    common.db.query(query)

    # Get all the /24 nodes. Load these into Nodes24
    query = """
        INSERT INTO Nodes24 (parent8, parent16, address, connections, children, x, y, radius)
        SELECT cluster.parent8, cluster.parent16, cluster.address, cluster.connections, cluster.children
            , ((Nodes16.radius * (cluster.address MOD 16) / 7.5 - Nodes16.radius) + Nodes16.x) as x
            , ((Nodes16.radius * (cluster.address DIV 16) / 7.5 - Nodes16.radius) + Nodes16.y) as y
            , 36 as radius
        FROM
            (SELECT aggregate.pip8 AS parent8, aggregate.pip16 AS parent16, aggregate.nip AS address
                , SUM(aggregate.conns) AS connections, COUNT(aggregate.child) AS children
            FROM
                (SELECT ip DIV 16777216 AS 'pip8'
                    , (ip MOD 16777216) DIV 65536 AS 'pip16'
                    , (ip MOD 65536) DIV 256 AS 'nip'
                    , (ip MOD 256) AS 'child'
                    , COUNT(*) AS 'conns'
                FROM (
                    (SELECT SourceIP AS ip
                    FROM Syslog)
                    UNION ALL
                    (SELECT DestinationIP AS ip
                    FROM Syslog)
                ) as result
                GROUP BY pip8, pip16, nip, child
            ) AS aggregate
            GROUP BY parent8, parent16, address) AS cluster
            JOIN Nodes16
            ON Nodes16.address = cluster.parent16 && Nodes16.parent8 = cluster.parent8;
        """
    common.db.query(query)

    # Get all the /32 nodes. Load these into Nodes32
    query = """
        INSERT INTO Nodes32 (parent8, parent16, parent24, address, connections, children, x, y, radius)
        SELECT cluster.parent8, cluster.parent16, cluster.parent24, cluster.address, cluster.connections, cluster.children
            , ((Nodes24.radius * (cluster.address MOD 16) / 7.5 - Nodes24.radius) + Nodes24.x) as x
            , ((Nodes24.radius * (cluster.address DIV 16) / 7.5 - Nodes24.radius) + Nodes24.y) as y
            , 1.5 as radius
        FROM
            (SELECT aggregate.pip8 AS parent8
                , aggregate.pip16 AS parent16
                , aggregate.pip24 AS parent24
                , aggregate.nip AS address
                , SUM(aggregate.conns) AS connections
                , COUNT(aggregate.child) AS children
            FROM
                (SELECT ip DIV 16777216 AS 'pip8'
                    , (ip MOD 16777216) DIV 65536 AS 'pip16'
                    , (ip MOD 65536) DIV 256 AS 'pip24'
                    , (ip MOD 256) AS 'nip'
                    , 0 AS 'child'
                    , COUNT(*) AS 'conns'
                FROM (
                    (SELECT SourceIP AS ip
                    FROM Syslog)
                    UNION ALL
                    (SELECT DestinationIP AS ip
                    FROM Syslog)
                ) as result
                GROUP BY pip8, pip16, pip24, nip, child
            ) AS aggregate
            GROUP BY parent8, parent16, parent24, address) AS cluster
            JOIN Nodes24
            ON Nodes24.address = cluster.parent24 && Nodes24.parent16 = cluster.parent16 && Nodes24.parent8 = cluster.parent8;
        """
    common.db.query(query)


def import_links():
    # Populate Links8
    links = get_links8()
    for link in links:
        position_link(link)
    set_links8(links)

    # Populate Links16
    links = get_links16()
    for link in links:
        position_link(link)
    set_links16(links)


    # Populate Links24
    links = get_links24()
    for link in links:
        position_link(link)
    set_links24(links)


    # Populate Links32
    links = get_links32()
    for link in links:
        position_link(link)
    set_links32(links)


def position_link(link):
    dx = link.dx - link.sx
    dy = link.dy - link.sy
    io_offset = 0.2

    if abs(dx) > abs(dy):
        # more horizontal distance
        if dx < 0:
            # leftward flowing
            link.sx -= link.sr
            link.dx += link.dr
            link.sy += link.sr * io_offset
            link.dy += link.dr * io_offset
        else:
            # rightward flowing
            link.sx += link.sr
            link.dx -= link.dr
            link.sy -= link.sr * io_offset
            link.dy -= link.dr * io_offset
    else:
        # more vertical distance
        if dy < 0:
            link.sy -= link.sr
            link.dy += link.dr
            link.sx += link.sr * io_offset
            link.dx += link.dr * io_offset
        else:
            link.sy += link.sr
            link.dy -= link.dr
            link.sx -= link.sr * io_offset
            link.dx -= link.dr * io_offset


def get_links8():

    query = """
        SELECT source8, dest8, port, conns, ts,
            src.x AS sx, src.y AS sy, src.radius AS sr,
            dst.x AS dx, dst.y AS dy, dst.radius AS dr
        FROM
            (SELECT SourceIP DIV 16777216 AS source8
                 , DestinationIP DIV 16777216 AS dest8
                 , DestinationPort as port
                 , SUBSTRING(TIMESTAMPADD(MINUTE, -(MINUTE(Timestamp) MOD 5), Timestamp), 1, 16) as ts
                 , COUNT(*) AS conns
            FROM Syslog
            GROUP BY source8, dest8, port, ts) AS main
            JOIN
            (SELECT address, x, y, radius FROM Nodes8) AS src
            ON (source8 = src.address)
            JOIN
            (SELECT address, x, y, radius FROM Nodes8) AS dst
            ON (dest8 = dst.address)
        """
    rows = list(common.db.query(query))
    return rows


def set_links8(links):
    values = [{
        "source8": i.source8,
        "dest8": i.dest8,
        "port": i.port,
        "links": i.conns,
        "x1": i.sx,
        "y1": i.sy,
        "x2": i.dx,
        "y2": i.dy,
        "timestamp": i.ts
    } for i in links]
    common.db.multiple_insert('Links8', values=values)


def get_links16():
    # This seems like a big query. Some explanation:
    # The query creates a larger table (union) from a few query results:
    #    a.b -> a.c
    #    a.* -> b.c
    #    a.b -> c.*
    query = """
        SELECT source8, source16, dest8, dest16, port, conns, ts,
            src.x AS sx, src.y AS sy, src.radius AS sr,
            dst.x AS dx, dst.y AS dy, dst.radius AS dr
        FROM
            (SELECT SourceIP DIV 16777216 AS source8
                     , (SourceIP - (SourceIP DIV 16777216) * 16777216) DIV 65536 AS source16
                     , DestinationIP DIV 16777216 AS dest8
                     , (DestinationIP - (DestinationIP DIV 16777216) * 16777216) DIV 65536 AS dest16
                     , DestinationPort as port
                     , SUBSTRING(TIMESTAMPADD(MINUTE, -(MINUTE(Timestamp) MOD 5), Timestamp), 1, 16) as ts
                     , COUNT(*) AS conns
                FROM Syslog
                WHERE (SourceIP DIV 16777216) = (DestinationIP DIV 16777216)
                GROUP BY source8, source16, dest8, dest16, port, ts)
                AS main
            JOIN
                (SELECT parent8, address, x, y, radius
                FROM Nodes16)
                AS src
                ON (source8 = src.parent8 && source16 = src.address)
            JOIN
                (SELECT parent8, address, x, y, radius
                FROM Nodes16)
                AS dst
                ON (dest8 = dst.parent8 && dest16 = dst.address)
        UNION
        SELECT source8, 256 AS source16, dest8, dest16, port, conns, ts,
            src.x AS sx, src.y AS sy, src.radius AS sr,
            dst.x AS dx, dst.y AS dy, dst.radius AS dr
        FROM
            (SELECT SourceIP DIV 16777216 AS source8
                     , DestinationIP DIV 16777216 AS dest8
                     , (DestinationIP - (DestinationIP DIV 16777216) * 16777216) DIV 65536 AS dest16
                     , DestinationPort as port
                     , SUBSTRING(TIMESTAMPADD(MINUTE, -(MINUTE(Timestamp) MOD 5), Timestamp), 1, 16) as ts
                     , COUNT(*) AS conns
                FROM Syslog
                WHERE (SourceIP DIV 16777216) != (DestinationIP DIV 16777216)
                GROUP BY source8, dest8, dest16, port, ts)
                AS main
            JOIN
                (SELECT address, x, y, radius
                FROM Nodes8)
                AS src
                ON (source8 = src.address)
            JOIN
                (SELECT parent8, address, x, y, radius
                FROM Nodes16)
                AS dst
                ON (dest8 = dst.parent8 && dest16 = dst.address)
        UNION
        SELECT source8, source16, dest8, 256 AS dest16, port, conns, ts,
            src.x AS sx, src.y AS sy, src.radius AS sr,
            dst.x AS dx, dst.y AS dy, dst.radius AS dr
        FROM
            (SELECT SourceIP DIV 16777216 AS source8
                     , (SourceIP - (SourceIP DIV 16777216) * 16777216) DIV 65536 AS source16
                     , DestinationIP DIV 16777216 AS dest8
                     , DestinationPort as port
                     , SUBSTRING(TIMESTAMPADD(MINUTE, -(MINUTE(Timestamp) MOD 5), Timestamp), 1, 16) as ts
                     , COUNT(*) AS conns
                FROM Syslog
                WHERE (SourceIP DIV 16777216) != (DestinationIP DIV 16777216)
                GROUP BY source8, source16, dest8, port, ts)
                AS main
            JOIN
                (SELECT parent8, address, x, y, radius
                FROM Nodes16)
                AS src
                ON (source8 = src.parent8 && source16 = src.address)
            JOIN
                (SELECT address, x, y, radius
                FROM Nodes8)
                AS dst
                ON (dest8 = dst.address);"""
    rows = list(common.db.query(query))
    return rows


def set_links16(links):
    values = [{
        "source8": i.source8,
        "source16": i.source16,
        "dest8": i.dest8,
        "dest16": i.dest16,
        "port": i.port,
        "links": i.conns,
        "x1": i.sx,
        "y1": i.sy,
        "x2": i.dx,
        "y2": i.dy,
        "timestamp": i.ts
    } for i in links]
    common.db.multiple_insert('Links16', values=values)


def get_links24():
    # This seems like a big query. Some explanation:
    # The query creates a larger table (union) from a few query results:
    #    a.b.c -> a.b.d
    #    a.b.* -> a.c.d
    #    a.*.* -> b.c.d
    #    a.b.c -> a.d.*
    #    a.b.c -> d.*.*
    query = """
        SELECT source8, source16, source24, dest8, dest16, dest24, port, conns, ts,
            src.x AS sx, src.y AS sy, src.radius AS sr,
            dst.x AS dx, dst.y AS dy, dst.radius AS dr
        FROM
            (SELECT SourceIP DIV 16777216 AS source8
                     , (SourceIP - (SourceIP DIV 16777216) * 16777216) DIV 65536 AS source16
                     , (SourceIP - (SourceIP DIV 65536) * 65536) DIV 256 AS source24
                     , DestinationIP DIV 16777216 AS dest8
                     , (DestinationIP - (DestinationIP DIV 16777216) * 16777216) DIV 65536 AS dest16
                     , (DestinationIP - (DestinationIP DIV 65536) * 65536) DIV 256 AS dest24
                     , DestinationPort as port
                     , SUBSTRING(TIMESTAMPADD(MINUTE, -(MINUTE(Timestamp) MOD 5), Timestamp), 1, 16) as ts
                     , COUNT(*) AS conns
                FROM Syslog
                WHERE (SourceIP DIV 16777216) = (DestinationIP DIV 16777216)
                    AND (SourceIP - (SourceIP DIV 16777216) * 16777216) DIV 65536 = (DestinationIP - (DestinationIP DIV 16777216) * 16777216) DIV 65536
                GROUP BY source8, source16, source24, dest8, dest16, dest24, port, ts) AS main
            JOIN
                (SELECT parent8, parent16, address, x, y, radius
                FROM Nodes24)
                AS src
                ON (source8 = src.parent8 && source16 = src.parent16 && source24 = src.address)
            JOIN
                (SELECT parent8, parent16, address, x, y, radius
                FROM Nodes24)
                AS dst
                ON (dest8 = dst.parent8 && dest16 = dst.parent16 && dest24 = dst.address)
        UNION
        SELECT source8, source16, 256, dest8, dest16, dest24, port, conns, ts,
            src.x AS sx, src.y AS sy, src.radius AS sr,
            dst.x AS dx, dst.y AS dy, dst.radius AS dr
        FROM
            (SELECT SourceIP DIV 16777216 AS source8
                     , (SourceIP - (SourceIP DIV 16777216) * 16777216) DIV 65536 AS source16
                     , DestinationIP DIV 16777216 AS dest8
                     , (DestinationIP - (DestinationIP DIV 16777216) * 16777216) DIV 65536 AS dest16
                     , (DestinationIP - (DestinationIP DIV 65536) * 65536) DIV 256 AS dest24
                     , DestinationPort as port
                     , SUBSTRING(TIMESTAMPADD(MINUTE, -(MINUTE(Timestamp) MOD 5), Timestamp), 1, 16) as ts
                     , COUNT(*) AS conns
                FROM Syslog
                WHERE (SourceIP DIV 16777216) = (DestinationIP DIV 16777216)
                    AND (SourceIP - (SourceIP DIV 16777216) * 16777216) DIV 65536 != (DestinationIP - (DestinationIP DIV 16777216) * 16777216) DIV 65536
                GROUP BY source8, source16, dest8, dest16, dest24, port, ts) AS main
            JOIN
                (SELECT parent8, address, x, y, radius
                FROM Nodes16)
                AS src
                ON (source8 = src.parent8 && source16 = src.address)
            JOIN
                (SELECT parent8, parent16, address, x, y, radius
                FROM Nodes24)
                AS dst
                ON (dest8 = dst.parent8 && dest16 = dst.parent16 && dest24 = dst.address)
        UNION
        SELECT source8, 256, 256, dest8, dest16, dest24, port, conns, ts,
            src.x AS sx, src.y AS sy, src.radius AS sr,
            dst.x AS dx, dst.y AS dy, dst.radius AS dr
        FROM
            (SELECT SourceIP DIV 16777216 AS source8
                     , DestinationIP DIV 16777216 AS dest8
                     , (DestinationIP - (DestinationIP DIV 16777216) * 16777216) DIV 65536 AS dest16
                     , (DestinationIP - (DestinationIP DIV 65536) * 65536) DIV 256 AS dest24
                     , DestinationPort as port
                     , SUBSTRING(TIMESTAMPADD(MINUTE, -(MINUTE(Timestamp) MOD 5), Timestamp), 1, 16) as ts
                     , COUNT(*) AS conns
                FROM Syslog
                WHERE (SourceIP DIV 16777216) != (DestinationIP DIV 16777216)
                GROUP BY source8, dest8, dest16, dest24, port, ts) AS main
            JOIN
                (SELECT address, x, y, radius
                FROM Nodes8)
                AS src
                ON (source8 = src.address)
            JOIN
                (SELECT parent8, parent16, address, x, y, radius
                FROM Nodes24)
                AS dst
                ON (dest8 = dst.parent8 && dest16 = dst.parent16 && dest24 = dst.address)
        UNION
        SELECT source8, source16, source24, dest8, dest16, 256, port, conns, ts,
            src.x AS sx, src.y AS sy, src.radius AS sr,
            dst.x AS dx, dst.y AS dy, dst.radius AS dr
        FROM
            (SELECT SourceIP DIV 16777216 AS source8
                     , (SourceIP - (SourceIP DIV 16777216) * 16777216) DIV 65536 AS source16
                     , (SourceIP - (SourceIP DIV 65536) * 65536) DIV 256 AS source24
                     , DestinationIP DIV 16777216 AS dest8
                     , (DestinationIP - (DestinationIP DIV 16777216) * 16777216) DIV 65536 AS dest16
                     , DestinationPort as port
                     , SUBSTRING(TIMESTAMPADD(MINUTE, -(MINUTE(Timestamp) MOD 5), Timestamp), 1, 16) as ts
                     , COUNT(*) AS conns
                FROM Syslog
                WHERE (SourceIP DIV 16777216) = (DestinationIP DIV 16777216)
                    AND (SourceIP - (SourceIP DIV 16777216) * 16777216) DIV 65536 != (DestinationIP - (DestinationIP DIV 16777216) * 16777216) DIV 65536
                GROUP BY source8, source16, source24, dest8, dest16, port, ts) AS main
            JOIN
                (SELECT parent8, parent16, address, x, y, radius
                FROM Nodes24)
                AS src
                ON (source8 = src.parent8 && source16 = src.parent16 && source24 = src.address)
            JOIN
                (SELECT parent8, address, x, y, radius
                FROM Nodes16)
                AS dst
                ON (dest8 = dst.parent8 && dest16 = dst.address)
        UNION
        SELECT source8, source16, source24, dest8, 256, 256, port, conns, ts,
            src.x AS sx, src.y AS sy, src.radius AS sr,
            dst.x AS dx, dst.y AS dy, dst.radius AS dr
        FROM
            (SELECT SourceIP DIV 16777216 AS source8
                     , (SourceIP - (SourceIP DIV 16777216) * 16777216) DIV 65536 AS source16
                     , (SourceIP - (SourceIP DIV 65536) * 65536) DIV 256 AS source24
                     , DestinationIP DIV 16777216 AS dest8
                     , DestinationPort as port
                     , SUBSTRING(TIMESTAMPADD(MINUTE, -(MINUTE(Timestamp) MOD 5), Timestamp), 1, 16) as ts
                     , COUNT(*) AS conns
                FROM Syslog
                WHERE (SourceIP DIV 16777216) != (DestinationIP DIV 16777216)
                GROUP BY source8, source16, source24, dest8, port, ts) AS main
            JOIN
                (SELECT parent8, parent16, address, x, y, radius
                FROM Nodes24)
                AS src
                ON (source8 = src.parent8 && source16 = src.parent16 && source24 = src.address)
            JOIN
                (SELECT address, x, y, radius
                FROM Nodes8)
                AS dst
                ON (dest8 = dst.address);
    """
    rows = list(common.db.query(query))
    return rows


def set_links24(links):
    values = [{
        "source8": i.source8,
        "source16": i.source16,
        "source24": i.source24,
        "dest8": i.dest8,
        "dest16": i.dest16,
        "dest24": i.dest24,
        "port": i.port,
        "links": i.conns,
        "x1": i.sx,
        "y1": i.sy,
        "x2": i.dx,
        "y2": i.dy,
        "timestamp": i.ts
    } for i in links]
    common.db.multiple_insert('Links24', values=values)


def get_links32():
    # This seems like a big query. Some explanation:
    # The query creates a larger table (union) from a few query results:
    #    a.b.c.d -> a.b.c.e
    #    a.b.c.* -> a.b.d.e
    #    a.b.*.* -> a.c.d.e
    #    a.*.*.* -> b.c.d.e
    #    a.b.c.d -> a.b.e.*
    #    a.b.c.d -> a.e.*.*
    #    a.b.c.d -> e.*.*.*
    query = """
        SELECT source8, source16, source24, source32, dest8, dest16, dest24, dest32, port, conns, ts,
            src.x AS sx, src.y AS sy, src.radius AS sr,
            dst.x AS dx, dst.y AS dy, dst.radius AS dr
        FROM
            (SELECT SourceIP DIV 16777216 AS source8
                     , (SourceIP - (SourceIP DIV 16777216) * 16777216) DIV 65536 AS source16
                     , (SourceIP - (SourceIP DIV 65536) * 65536) DIV 256 AS source24
                     , (SourceIP - (SourceIP DIV 256) * 256) AS source32
                     , DestinationIP DIV 16777216 AS dest8
                     , (DestinationIP - (DestinationIP DIV 16777216) * 16777216) DIV 65536 AS dest16
                     , (DestinationIP - (DestinationIP DIV 65536) * 65536) DIV 256 AS dest24
                     , (DestinationIP - (DestinationIP DIV 256) * 256) AS dest32
                     , DestinationPort AS port
                     , SUBSTRING(TIMESTAMPADD(MINUTE, -(MINUTE(Timestamp) MOD 5), Timestamp), 1, 16) as ts
                     , COUNT(*) AS conns
                FROM Syslog
                WHERE (SourceIP DIV 16777216) = (DestinationIP DIV 16777216)
                    AND (SourceIP - (SourceIP DIV 16777216) * 16777216) DIV 65536 = (DestinationIP - (DestinationIP DIV 16777216) * 16777216) DIV 65536
                    AND (SourceIP - (SourceIP DIV 65536) * 65536) DIV 256 = (DestinationIP - (DestinationIP DIV 65536) * 65536) DIV 256
                GROUP BY source8, source16, source24, source32, dest8, dest16, dest24, dest32, port, ts) AS main
            JOIN
                (SELECT parent8, parent16, parent24, address, x, y, radius
                FROM Nodes32)
                AS src
                ON (source8 = src.parent8 && source16 = src.parent16 && source24 = src.parent24 && source32 = src.address)
            JOIN
                (SELECT parent8, parent16, parent24, address, x, y, radius
                FROM Nodes32)
                AS dst
                ON (dest8 = dst.parent8 && dest16 = dst.parent16 && dest24 = dst.parent24 && dest32 = dst.address)
        UNION
        SELECT source8, source16, source24, 256, dest8, dest16, dest24, dest32, port, conns, ts,
            src.x AS sx, src.y AS sy, src.radius AS sr,
            dst.x AS dx, dst.y AS dy, dst.radius AS dr
        FROM
            (SELECT SourceIP DIV 16777216 AS source8
                     , (SourceIP - (SourceIP DIV 16777216) * 16777216) DIV 65536 AS source16
                     , (SourceIP - (SourceIP DIV 65536) * 65536) DIV 256 AS source24
                     , DestinationIP DIV 16777216 AS dest8
                     , (DestinationIP - (DestinationIP DIV 16777216) * 16777216) DIV 65536 AS dest16
                     , (DestinationIP - (DestinationIP DIV 65536) * 65536) DIV 256 AS dest24
                     , (DestinationIP - (DestinationIP DIV 256) * 256) AS dest32
                     , DestinationPort AS port
                     , SUBSTRING(TIMESTAMPADD(MINUTE, -(MINUTE(Timestamp) MOD 5), Timestamp), 1, 16) as ts
                     , COUNT(*) AS conns
                FROM Syslog
                WHERE (SourceIP DIV 16777216) = (DestinationIP DIV 16777216)
                    AND (SourceIP - (SourceIP DIV 16777216) * 16777216) DIV 65536 = (DestinationIP - (DestinationIP DIV 16777216) * 16777216) DIV 65536
                    AND (SourceIP - (SourceIP DIV 65536) * 65536) DIV 256 != (DestinationIP - (DestinationIP DIV 65536) * 65536) DIV 256
                GROUP BY source8, source16, source24, dest8, dest16, dest24, dest32, port, ts) AS main
            JOIN
                (SELECT parent8, parent16, address, x, y, radius
                FROM Nodes24)
                AS src
                ON (source8 = src.parent8 && source16 = src.parent16 && source24 = src.address)
            JOIN
                (SELECT parent8, parent16, parent24, address, x, y, radius
                FROM Nodes32)
                AS dst
                ON (dest8 = dst.parent8 && dest16 = dst.parent16 && dest24 = dst.parent24 && dest32 = dst.address)
        UNION
        SELECT source8, source16, 256, 256, dest8, dest16, dest24, dest32, port, conns, ts,
            src.x AS sx, src.y AS sy, src.radius AS sr,
            dst.x AS dx, dst.y AS dy, dst.radius AS dr
        FROM
            (SELECT SourceIP DIV 16777216 AS source8
                     , (SourceIP - (SourceIP DIV 16777216) * 16777216) DIV 65536 AS source16
                     , DestinationIP DIV 16777216 AS dest8
                     , (DestinationIP - (DestinationIP DIV 16777216) * 16777216) DIV 65536 AS dest16
                     , (DestinationIP - (DestinationIP DIV 65536) * 65536) DIV 256 AS dest24
                     , (DestinationIP - (DestinationIP DIV 256) * 256) AS dest32
                     , DestinationPort AS port
                     , SUBSTRING(TIMESTAMPADD(MINUTE, -(MINUTE(Timestamp) MOD 5), Timestamp), 1, 16) as ts
                     , COUNT(*) AS conns
                FROM Syslog
                WHERE (SourceIP DIV 16777216) = (DestinationIP DIV 16777216)
                    AND (SourceIP - (SourceIP DIV 16777216) * 16777216) DIV 65536 != (DestinationIP - (DestinationIP DIV 16777216) * 16777216) DIV 65536
                GROUP BY source8, source16, dest8, dest16, dest24, dest32, port, ts) AS main
            JOIN
                (SELECT parent8, address, x, y, radius
                FROM Nodes16)
                AS src
                ON (source8 = src.parent8 && source16 = src.address)
            JOIN
                (SELECT parent8, parent16, parent24, address, x, y, radius
                FROM Nodes32)
                AS dst
                ON (dest8 = dst.parent8 && dest16 = dst.parent16 && dest24 = dst.parent24 && dest32 = dst.address)
        UNION
        SELECT source8, 256, 256, 256, dest8, dest16, dest24, dest32, port, conns, ts,
            src.x AS sx, src.y AS sy, src.radius AS sr,
            dst.x AS dx, dst.y AS dy, dst.radius AS dr
        FROM
            (SELECT SourceIP DIV 16777216 AS source8
                     , DestinationIP DIV 16777216 AS dest8
                     , (DestinationIP - (DestinationIP DIV 16777216) * 16777216) DIV 65536 AS dest16
                     , (DestinationIP - (DestinationIP DIV 65536) * 65536) DIV 256 AS dest24
                     , (DestinationIP - (DestinationIP DIV 256) * 256) AS dest32
                     , DestinationPort AS port
                     , SUBSTRING(TIMESTAMPADD(MINUTE, -(MINUTE(Timestamp) MOD 5), Timestamp), 1, 16) as ts
                     , COUNT(*) AS conns
                FROM Syslog
                WHERE (SourceIP DIV 16777216) != (DestinationIP DIV 16777216)
                GROUP BY source8, dest8, dest16, dest24, dest32, port, ts) AS main
            JOIN
                (SELECT address, x, y, radius
                FROM Nodes8)
                AS src
                ON (source8 = src.address)
            JOIN
                (SELECT parent8, parent16, parent24, address, x, y, radius
                FROM Nodes32)
                AS dst
                ON (dest8 = dst.parent8 && dest16 = dst.parent16 && dest24 = dst.parent24 && dest32 = dst.address)
        UNION
        SELECT source8, source16, source24, source32, dest8, dest16, dest24, 256, port, conns, ts,
            src.x AS sx, src.y AS sy, src.radius AS sr,
            dst.x AS dx, dst.y AS dy, dst.radius AS dr
        FROM
            (SELECT SourceIP DIV 16777216 AS source8
                     , (SourceIP - (SourceIP DIV 16777216) * 16777216) DIV 65536 AS source16
                     , (SourceIP - (SourceIP DIV 65536) * 65536) DIV 256 AS source24
                     , (SourceIP - (SourceIP DIV 256) * 256) AS source32
                     , DestinationIP DIV 16777216 AS dest8
                     , (DestinationIP - (DestinationIP DIV 16777216) * 16777216) DIV 65536 AS dest16
                     , (DestinationIP - (DestinationIP DIV 65536) * 65536) DIV 256 AS dest24
                     , DestinationPort AS port
                     , SUBSTRING(TIMESTAMPADD(MINUTE, -(MINUTE(Timestamp) MOD 5), Timestamp), 1, 16) as ts
                     , COUNT(*) AS conns
                FROM Syslog
                WHERE (SourceIP DIV 16777216) = (DestinationIP DIV 16777216)
                    AND (SourceIP - (SourceIP DIV 16777216) * 16777216) DIV 65536 = (DestinationIP - (DestinationIP DIV 16777216) * 16777216) DIV 65536
                    AND (SourceIP - (SourceIP DIV 65536) * 65536) DIV 256 != (DestinationIP - (DestinationIP DIV 65536) * 65536) DIV 256
                GROUP BY source8, source16, source24, source32, dest8, dest16, dest24, port, ts) AS main
            JOIN
                (SELECT parent8, parent16, parent24, address, x, y, radius
                FROM Nodes32)
                AS src
                ON (source8 = src.parent8 && source16 = src.parent16 && source24 = src.parent24 && source32 = src.address)
            JOIN
                (SELECT parent8, parent16, address, x, y, radius
                FROM Nodes24)
                AS dst
                ON (dest8 = dst.parent8 && dest16 = dst.parent16 && dest24 = dst.address)
        UNION
        SELECT source8, source16, source24, source32, dest8, dest16, 256, 256, port, conns, ts,
            src.x AS sx, src.y AS sy, src.radius AS sr,
            dst.x AS dx, dst.y AS dy, dst.radius AS dr
        FROM
            (SELECT SourceIP DIV 16777216 AS source8
                     , (SourceIP - (SourceIP DIV 16777216) * 16777216) DIV 65536 AS source16
                     , (SourceIP - (SourceIP DIV 65536) * 65536) DIV 256 AS source24
                     , (SourceIP - (SourceIP DIV 256) * 256) AS source32
                     , DestinationIP DIV 16777216 AS dest8
                     , (DestinationIP - (DestinationIP DIV 16777216) * 16777216) DIV 65536 AS dest16
                     , DestinationPort AS port
                     , SUBSTRING(TIMESTAMPADD(MINUTE, -(MINUTE(Timestamp) MOD 5), Timestamp), 1, 16) as ts
                     , COUNT(*) AS conns
                FROM Syslog
                WHERE (SourceIP DIV 16777216) = (DestinationIP DIV 16777216)
                    AND (SourceIP - (SourceIP DIV 16777216) * 16777216) DIV 65536 != (DestinationIP - (DestinationIP DIV 16777216) * 16777216) DIV 65536
                GROUP BY source8, source16, source24, source32, dest8, dest16, port, ts) AS main
            JOIN
                (SELECT parent8, parent16, parent24, address, x, y, radius
                FROM Nodes32)
                AS src
                ON (source8 = src.parent8 && source16 = src.parent16 && source24 = src.parent24 && source32 = src.address)
            JOIN
                (SELECT parent8, address, x, y, radius
                FROM Nodes16)
                AS dst
                ON (dest8 = dst.parent8 && dest16 = dst.address)
        UNION
        SELECT source8, source16, source24, source32, dest8, 256, 256, 256, port, conns, ts,
            src.x AS sx, src.y AS sy, src.radius AS sr,
            dst.x AS dx, dst.y AS dy, dst.radius AS dr
        FROM
            (SELECT SourceIP DIV 16777216 AS source8
                     , (SourceIP - (SourceIP DIV 16777216) * 16777216) DIV 65536 AS source16
                     , (SourceIP - (SourceIP DIV 65536) * 65536) DIV 256 AS source24
                     , (SourceIP - (SourceIP DIV 256) * 256) AS source32
                     , DestinationIP DIV 16777216 AS dest8
                     , DestinationPort AS port
                     , SUBSTRING(TIMESTAMPADD(MINUTE, -(MINUTE(Timestamp) MOD 5), Timestamp), 1, 16) as ts
                     , COUNT(*) AS conns
                FROM Syslog
                WHERE (SourceIP DIV 16777216) != (DestinationIP DIV 16777216)
                GROUP BY source8, source16, source24, source32, dest8, port, ts) AS main
            JOIN
                (SELECT parent8, parent16, parent24, address, x, y, radius
                FROM Nodes32)
                AS src
                ON (source8 = src.parent8 && source16 = src.parent16 && source24 = src.parent24 && source32 = src.address)
            JOIN
                (SELECT address, x, y, radius
                FROM Nodes8)
                AS dst
                ON (dest8 = dst.address);
    """
    rows = list(common.db.query(query))
    return rows


def set_links32(links):
    values = [{
        "source8": i.source8,
        "source16": i.source16,
        "source24": i.source24,
        "source32": i.source32,
        "dest8": i.dest8,
        "dest16": i.dest16,
        "dest24": i.dest24,
        "dest32": i.dest32,
        "port": i.port,
        "links": i.conns,
        "x1": i.sx,
        "y1": i.sy,
        "x2": i.dx,
        "y2": i.dy,
        "timestamp": i.ts
    } for i in links]
    common.db.multiple_insert('Links32', values=values)


def preprocess_log():
    clean_tables()
    import_nodes()
    import_links()
    print("Pre-processing completed successfully.")

# If running as a script
if __name__ == "__main__":
    access = dbaccess.test_database()
    if access == 1049:
        dbaccess.create_database()
    elif access == 1045:
        print("Database access denied. Check you username / password? (dbconfig_local.py)")
    else:
        preprocess_log()

