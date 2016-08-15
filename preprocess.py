"""
Preprocess the data in the database's upload table Syslog
"""

import common
import dbaccess
import random
import math


def clean_tables():
    common.db.query("DROP TABLE IF EXISTS Links32;")
    common.db.query("DROP TABLE IF EXISTS Links24;")
    common.db.query("DROP TABLE IF EXISTS Links16;")
    common.db.query("DROP TABLE IF EXISTS Links8;")
    common.db.query("DROP TABLE IF EXISTS Nodes32;")
    common.db.query("DROP TABLE IF EXISTS Nodes24;")
    common.db.query("DROP TABLE IF EXISTS Nodes16;")
    common.db.query("DROP TABLE IF EXISTS Nodes8;")

    with open("./sql/setup_tables.sql", 'r') as file:
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
    query = """
        INSERT INTO Links8 (source8, dest8, port, links, x1, y1, x2, y2)
        SELECT source8, dest8, port, conns, src.x, src.y, dst.x, dst.y
        FROM
            (SELECT SourceIP DIV 16777216 AS source8
                 , DestinationIP DIV 16777216 AS dest8
                 , DestinationPort as port
                 , COUNT(*) AS conns
            FROM Syslog
            GROUP BY source8, dest8, port) AS main
            JOIN
            (SELECT address, x, y FROM Nodes8) AS src
            ON (source8 = src.address)
            JOIN
            (SELECT address, x, y FROM Nodes8) AS dst
            ON (dest8 = dst.address);
        """
    common.db.query(query)

    # Populate Links16
    #
    # This seems like a big query. Some explanation:
    # The query creates a larger table (union) from a few query results
    #    and inserts the larger table into Links16)

    query = """
        INSERT INTO Links16 (source8, source16, dest8, dest16, port, links, x1, y1, x2, y2)
        SELECT source8, source16, dest8, dest16, port, conns, src.x, src.y, dst.x, dst.y
        FROM
            (SELECT SourceIP DIV 16777216 AS source8
                     , (SourceIP - (SourceIP DIV 16777216) * 16777216) DIV 65536 AS source16
                     , DestinationIP DIV 16777216 AS dest8
                     , (DestinationIP - (DestinationIP DIV 16777216) * 16777216) DIV 65536 AS dest16
                     , DestinationPort as port
                     , COUNT(*) AS conns
                FROM Syslog
                WHERE (SourceIP DIV 16777216) = (DestinationIP DIV 16777216)
                GROUP BY source8, source16, dest8, dest16, port)
                AS main
            JOIN
                (SELECT parent8, address, x, y
                FROM Nodes16)
                AS src
                ON (source8 = src.parent8 && source16 = src.address)
            JOIN
                (SELECT parent8, address, x, y
                FROM Nodes16)
                AS dst
                ON (dest8 = dst.parent8 && dest16 = dst.address)
        UNION
        SELECT source8, 256 AS source16, dest8, dest16, port, conns, src.x, src.y, dst.x, dst.y
        FROM
            (SELECT SourceIP DIV 16777216 AS source8
                     , DestinationIP DIV 16777216 AS dest8
                     , (DestinationIP - (DestinationIP DIV 16777216) * 16777216) DIV 65536 AS dest16
                     , DestinationPort as port
                     , COUNT(*) AS conns
                FROM Syslog
                WHERE (SourceIP DIV 16777216) != (DestinationIP DIV 16777216)
                GROUP BY source8, dest8, dest16, port)
                AS main
            JOIN
                (SELECT address, x, y
                FROM Nodes8)
                AS src
                ON (source8 = src.address)
            JOIN
                (SELECT parent8, address, x, y
                FROM Nodes16)
                AS dst
                ON (dest8 = dst.parent8 && dest16 = dst.address)
        UNION
        SELECT source8, source16, dest8, 256 AS dest16, port, conns, src.x, src.y, dst.x, dst.y
        FROM
            (SELECT SourceIP DIV 16777216 AS source8
                     , (SourceIP - (SourceIP DIV 16777216) * 16777216) DIV 65536 AS source16
                     , DestinationIP DIV 16777216 AS dest8
                     , DestinationPort as port
                     , COUNT(*) AS conns
                FROM Syslog
                WHERE (SourceIP DIV 16777216) != (DestinationIP DIV 16777216)
                GROUP BY source8, source16, dest8, port)
                AS main
            JOIN
                (SELECT parent8, address, x, y
                FROM Nodes16)
                AS src
                ON (source8 = src.parent8 && source16 = src.address)
            JOIN
                (SELECT address, x, y
                FROM Nodes8)
                AS dst
                ON (dest8 = dst.address);
    """
    common.db.query(query)

    # Populate Links24
    #
    # This seems like a big query. Some explanation:
    # The query creates a larger table (union) from a few query results
    #    and inserts the larger table into Links24)
    # This query is set up like this to group together queries from very different IP addresses
    # (i.e. from a different /8 or /16 address)
    query = """
        INSERT INTO Links24 (source8, source16, source24, dest8, dest16, dest24, port, links, x1, y1, x2, y2)
        SELECT source8, source16, source24, dest8, dest16, dest24, port, conns, src.x, src.y, dst.x, dst.y
        FROM
            (SELECT SourceIP DIV 16777216 AS source8
                     , (SourceIP - (SourceIP DIV 16777216) * 16777216) DIV 65536 AS source16
                     , (SourceIP - (SourceIP DIV 65536) * 65536) DIV 256 AS source24
                     , DestinationIP DIV 16777216 AS dest8
                     , (DestinationIP - (DestinationIP DIV 16777216) * 16777216) DIV 65536 AS dest16
                     , (DestinationIP - (DestinationIP DIV 65536) * 65536) DIV 256 AS dest24
                     , DestinationPort as port
                     , COUNT(*) AS conns
                FROM Syslog
                WHERE (SourceIP DIV 16777216) = (DestinationIP DIV 16777216)
                    AND (SourceIP - (SourceIP DIV 16777216) * 16777216) DIV 65536 = (DestinationIP - (DestinationIP DIV 16777216) * 16777216) DIV 65536
                GROUP BY source8, source16, source24, dest8, dest16, dest24, port) AS main
            JOIN
                (SELECT parent8, parent16, address, x, y
                FROM Nodes24)
                AS src
                ON (source8 = src.parent8 && source16 = src.parent16 && source24 = src.address)
            JOIN
                (SELECT parent8, parent16, address, x, y
                FROM Nodes24)
                AS dst
                ON (dest8 = dst.parent8 && dest16 = dst.parent16 && dest24 = dst.address)
        UNION
        SELECT source8, source16, 256, dest8, dest16, dest24, port, conns, src.x, src.y, dst.x, dst.y
        FROM
            (SELECT SourceIP DIV 16777216 AS source8
                     , (SourceIP - (SourceIP DIV 16777216) * 16777216) DIV 65536 AS source16
                     , DestinationIP DIV 16777216 AS dest8
                     , (DestinationIP - (DestinationIP DIV 16777216) * 16777216) DIV 65536 AS dest16
                     , (DestinationIP - (DestinationIP DIV 65536) * 65536) DIV 256 AS dest24
                     , DestinationPort as port
                     , COUNT(*) AS conns
                FROM Syslog
                WHERE (SourceIP DIV 16777216) = (DestinationIP DIV 16777216)
                    AND (SourceIP - (SourceIP DIV 16777216) * 16777216) DIV 65536 != (DestinationIP - (DestinationIP DIV 16777216) * 16777216) DIV 65536
                GROUP BY source8, source16, dest8, dest16, dest24, port) AS main
            JOIN
                (SELECT parent8, address, x, y
                FROM Nodes16)
                AS src
                ON (source8 = src.parent8 && source16 = src.address)
            JOIN
                (SELECT parent8, parent16, address, x, y
                FROM Nodes24)
                AS dst
                ON (dest8 = dst.parent8 && dest16 = dst.parent16 && dest24 = dst.address)
        UNION
        SELECT source8, 256, 256, dest8, dest16, dest24, port, conns, src.x, src.y, dst.x, dst.y
        FROM
            (SELECT SourceIP DIV 16777216 AS source8
                     , DestinationIP DIV 16777216 AS dest8
                     , (DestinationIP - (DestinationIP DIV 16777216) * 16777216) DIV 65536 AS dest16
                     , (DestinationIP - (DestinationIP DIV 65536) * 65536) DIV 256 AS dest24
                     , DestinationPort as port
                     , COUNT(*) AS conns
                FROM Syslog
                WHERE (SourceIP DIV 16777216) != (DestinationIP DIV 16777216)
                GROUP BY source8, dest8, dest16, dest24, port) AS main
            JOIN
                (SELECT address, x, y
                FROM Nodes8)
                AS src
                ON (source8 = src.address)
            JOIN
                (SELECT parent8, parent16, address, x, y
                FROM Nodes24)
                AS dst
                ON (dest8 = dst.parent8 && dest16 = dst.parent16 && dest24 = dst.address)
        UNION
        SELECT source8, source16, source24, dest8, dest16, 256, port, conns, src.x, src.y, dst.x, dst.y
        FROM
            (SELECT SourceIP DIV 16777216 AS source8
                     , (SourceIP - (SourceIP DIV 16777216) * 16777216) DIV 65536 AS source16
                     , (SourceIP - (SourceIP DIV 65536) * 65536) DIV 256 AS source24
                     , DestinationIP DIV 16777216 AS dest8
                     , (DestinationIP - (DestinationIP DIV 16777216) * 16777216) DIV 65536 AS dest16
                     , DestinationPort as port
                     , COUNT(*) AS conns
                FROM Syslog
                WHERE (SourceIP DIV 16777216) = (DestinationIP DIV 16777216)
                    AND (SourceIP - (SourceIP DIV 16777216) * 16777216) DIV 65536 != (DestinationIP - (DestinationIP DIV 16777216) * 16777216) DIV 65536
                GROUP BY source8, source16, source24, dest8, dest16, port) AS main
            JOIN
                (SELECT parent8, parent16, address, x, y
                FROM Nodes24)
                AS src
                ON (source8 = src.parent8 && source16 = src.parent16 && source24 = src.address)
            JOIN
                (SELECT parent8, address, x, y
                FROM Nodes16)
                AS dst
                ON (dest8 = dst.parent8 && dest16 = dst.address)
        UNION
        SELECT source8, source16, source24, dest8, 256, 256, port, conns, src.x, src.y, dst.x, dst.y
        FROM
            (SELECT SourceIP DIV 16777216 AS source8
                     , (SourceIP - (SourceIP DIV 16777216) * 16777216) DIV 65536 AS source16
                     , (SourceIP - (SourceIP DIV 65536) * 65536) DIV 256 AS source24
                     , DestinationIP DIV 16777216 AS dest8
                     , DestinationPort as port
                     , COUNT(*) AS conns
                FROM Syslog
                WHERE (SourceIP DIV 16777216) != (DestinationIP DIV 16777216)
                GROUP BY source8, source16, source24, dest8, port) AS main
            JOIN
                (SELECT parent8, parent16, address, x, y
                FROM Nodes24)
                AS src
                ON (source8 = src.parent8 && source16 = src.parent16 && source24 = src.address)
            JOIN
                (SELECT address, x, y
                FROM Nodes8)
                AS dst
                ON (dest8 = dst.address);
    """
    common.db.query(query)

    # Populate Links32
    query = """
        INSERT INTO Links32 (source8, source16, source24, source32, dest8, dest16, dest24, dest32, port, links, x1, y1, x2, y2)
        SELECT source8, source16, source24, source32, dest8, dest16, dest24, dest32, port, conns, src.x, src.y, dst.x, dst.y
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
                     , COUNT(*) AS conns
                FROM Syslog
                WHERE (SourceIP DIV 16777216) = (DestinationIP DIV 16777216)
                    AND (SourceIP - (SourceIP DIV 16777216) * 16777216) DIV 65536 = (DestinationIP - (DestinationIP DIV 16777216) * 16777216) DIV 65536
                    AND (SourceIP - (SourceIP DIV 65536) * 65536) DIV 256 = (DestinationIP - (DestinationIP DIV 65536) * 65536) DIV 256
                GROUP BY source8, source16, source24, source32, dest8, dest16, dest24, dest32, port) AS main
            JOIN
                (SELECT parent8, parent16, parent24, address, x, y
                FROM Nodes32)
                AS src
                ON (source8 = src.parent8 && source16 = src.parent16 && source24 = src.parent24 && source32 = src.address)
            JOIN
                (SELECT parent8, parent16, parent24, address, x, y
                FROM Nodes32)
                AS dst
                ON (dest8 = dst.parent8 && dest16 = dst.parent16 && dest24 = dst.parent24 && dest32 = dst.address)
        UNION
        SELECT source8, source16, source24, 256, dest8, dest16, dest24, dest32, port, conns, src.x, src.y, dst.x, dst.y
        FROM
            (SELECT SourceIP DIV 16777216 AS source8
                     , (SourceIP - (SourceIP DIV 16777216) * 16777216) DIV 65536 AS source16
                     , (SourceIP - (SourceIP DIV 65536) * 65536) DIV 256 AS source24
                     , DestinationIP DIV 16777216 AS dest8
                     , (DestinationIP - (DestinationIP DIV 16777216) * 16777216) DIV 65536 AS dest16
                     , (DestinationIP - (DestinationIP DIV 65536) * 65536) DIV 256 AS dest24
                     , (DestinationIP - (DestinationIP DIV 256) * 256) AS dest32
                     , DestinationPort AS port
                     , COUNT(*) AS conns
                FROM Syslog
                WHERE (SourceIP DIV 16777216) = (DestinationIP DIV 16777216)
                    AND (SourceIP - (SourceIP DIV 16777216) * 16777216) DIV 65536 = (DestinationIP - (DestinationIP DIV 16777216) * 16777216) DIV 65536
                    AND (SourceIP - (SourceIP DIV 65536) * 65536) DIV 256 != (DestinationIP - (DestinationIP DIV 65536) * 65536) DIV 256
                GROUP BY source8, source16, source24, dest8, dest16, dest24, dest32, port) AS main
            JOIN
                (SELECT parent8, parent16, address, x, y
                FROM Nodes24)
                AS src
                ON (source8 = src.parent8 && source16 = src.parent16 && source24 = src.address)
            JOIN
                (SELECT parent8, parent16, parent24, address, x, y
                FROM Nodes32)
                AS dst
                ON (dest8 = dst.parent8 && dest16 = dst.parent16 && dest24 = dst.parent24 && dest32 = dst.address)
        UNION
        SELECT source8, source16, 256, 256, dest8, dest16, dest24, dest32, port, conns, src.x, src.y, dst.x, dst.y
        FROM
            (SELECT SourceIP DIV 16777216 AS source8
                     , (SourceIP - (SourceIP DIV 16777216) * 16777216) DIV 65536 AS source16
                     , DestinationIP DIV 16777216 AS dest8
                     , (DestinationIP - (DestinationIP DIV 16777216) * 16777216) DIV 65536 AS dest16
                     , (DestinationIP - (DestinationIP DIV 65536) * 65536) DIV 256 AS dest24
                     , (DestinationIP - (DestinationIP DIV 256) * 256) AS dest32
                     , DestinationPort AS port
                     , COUNT(*) AS conns
                FROM Syslog
                WHERE (SourceIP DIV 16777216) = (DestinationIP DIV 16777216)
                    AND (SourceIP - (SourceIP DIV 16777216) * 16777216) DIV 65536 != (DestinationIP - (DestinationIP DIV 16777216) * 16777216) DIV 65536
                GROUP BY source8, source16, dest8, dest16, dest24, dest32, port) AS main
            JOIN
                (SELECT parent8, address, x, y
                FROM Nodes16)
                AS src
                ON (source8 = src.parent8 && source16 = src.address)
            JOIN
                (SELECT parent8, parent16, parent24, address, x, y
                FROM Nodes32)
                AS dst
                ON (dest8 = dst.parent8 && dest16 = dst.parent16 && dest24 = dst.parent24 && dest32 = dst.address)
        UNION
        SELECT source8, 256, 256, 256, dest8, dest16, dest24, dest32, port, conns, src.x, src.y, dst.x, dst.y
        FROM
            (SELECT SourceIP DIV 16777216 AS source8
                     , DestinationIP DIV 16777216 AS dest8
                     , (DestinationIP - (DestinationIP DIV 16777216) * 16777216) DIV 65536 AS dest16
                     , (DestinationIP - (DestinationIP DIV 65536) * 65536) DIV 256 AS dest24
                     , (DestinationIP - (DestinationIP DIV 256) * 256) AS dest32
                     , DestinationPort AS port
                     , COUNT(*) AS conns
                FROM Syslog
                WHERE (SourceIP DIV 16777216) != (DestinationIP DIV 16777216)
                GROUP BY source8, dest8, dest16, dest24, dest32, port) AS main
            JOIN
                (SELECT address, x, y
                FROM Nodes8)
                AS src
                ON (source8 = src.address)
            JOIN
                (SELECT parent8, parent16, parent24, address, x, y
                FROM Nodes32)
                AS dst
                ON (dest8 = dst.parent8 && dest16 = dst.parent16 && dest24 = dst.parent24 && dest32 = dst.address)
        UNION
        SELECT source8, source16, source24, source32, dest8, dest16, dest24, 256, port, conns, src.x, src.y, dst.x, dst.y
        FROM
            (SELECT SourceIP DIV 16777216 AS source8
                     , (SourceIP - (SourceIP DIV 16777216) * 16777216) DIV 65536 AS source16
                     , (SourceIP - (SourceIP DIV 65536) * 65536) DIV 256 AS source24
                     , (SourceIP - (SourceIP DIV 256) * 256) AS source32
                     , DestinationIP DIV 16777216 AS dest8
                     , (DestinationIP - (DestinationIP DIV 16777216) * 16777216) DIV 65536 AS dest16
                     , (DestinationIP - (DestinationIP DIV 65536) * 65536) DIV 256 AS dest24
                     , DestinationPort AS port
                     , COUNT(*) AS conns
                FROM Syslog
                WHERE (SourceIP DIV 16777216) = (DestinationIP DIV 16777216)
                    AND (SourceIP - (SourceIP DIV 16777216) * 16777216) DIV 65536 = (DestinationIP - (DestinationIP DIV 16777216) * 16777216) DIV 65536
                    AND (SourceIP - (SourceIP DIV 65536) * 65536) DIV 256 != (DestinationIP - (DestinationIP DIV 65536) * 65536) DIV 256
                GROUP BY source8, source16, source24, source32, dest8, dest16, dest24, port) AS main
            JOIN
                (SELECT parent8, parent16, parent24, address, x, y
                FROM Nodes32)
                AS src
                ON (source8 = src.parent8 && source16 = src.parent16 && source24 = src.parent24 && source32 = src.address)
            JOIN
                (SELECT parent8, parent16, address, x, y
                FROM Nodes24)
                AS dst
                ON (dest8 = dst.parent8 && dest16 = dst.parent16 && dest24 = dst.address)
        UNION
        SELECT source8, source16, source24, source32, dest8, dest16, 256, 256, port, conns, src.x, src.y, dst.x, dst.y
        FROM
            (SELECT SourceIP DIV 16777216 AS source8
                     , (SourceIP - (SourceIP DIV 16777216) * 16777216) DIV 65536 AS source16
                     , (SourceIP - (SourceIP DIV 65536) * 65536) DIV 256 AS source24
                     , (SourceIP - (SourceIP DIV 256) * 256) AS source32
                     , DestinationIP DIV 16777216 AS dest8
                     , (DestinationIP - (DestinationIP DIV 16777216) * 16777216) DIV 65536 AS dest16
                     , DestinationPort AS port
                     , COUNT(*) AS conns
                FROM Syslog
                WHERE (SourceIP DIV 16777216) = (DestinationIP DIV 16777216)
                    AND (SourceIP - (SourceIP DIV 16777216) * 16777216) DIV 65536 != (DestinationIP - (DestinationIP DIV 16777216) * 16777216) DIV 65536
                GROUP BY source8, source16, source24, source32, dest8, dest16, port) AS main
            JOIN
                (SELECT parent8, parent16, parent24, address, x, y
                FROM Nodes32)
                AS src
                ON (source8 = src.parent8 && source16 = src.parent16 && source24 = src.parent24 && source32 = src.address)
            JOIN
                (SELECT parent8, address, x, y
                FROM Nodes16)
                AS dst
                ON (dest8 = dst.parent8 && dest16 = dst.address)
        UNION
        SELECT source8, source16, source24, source32, dest8, 256, 256, 256, port, conns, src.x, src.y, dst.x, dst.y
        FROM
            (SELECT SourceIP DIV 16777216 AS source8
                     , (SourceIP - (SourceIP DIV 16777216) * 16777216) DIV 65536 AS source16
                     , (SourceIP - (SourceIP DIV 65536) * 65536) DIV 256 AS source24
                     , (SourceIP - (SourceIP DIV 256) * 256) AS source32
                     , DestinationIP DIV 16777216 AS dest8
                     , DestinationPort AS port
                     , COUNT(*) AS conns
                FROM Syslog
                WHERE (SourceIP DIV 16777216) != (DestinationIP DIV 16777216)
                GROUP BY source8, source16, source24, source32, dest8, port) AS main
            JOIN
                (SELECT parent8, parent16, parent24, address, x, y
                FROM Nodes32)
                AS src
                ON (source8 = src.parent8 && source16 = src.parent16 && source24 = src.parent24 && source32 = src.address)
            JOIN
                (SELECT address, x, y
                FROM Nodes8)
                AS dst
                ON (dest8 = dst.address);
    """
    common.db.query(query)


def getLinks8():
    query = """
        SELECT source8, dest8, port, conns, src.x, src.y, dst.x, dst.y
        FROM
            (SELECT SourceIP DIV 16777216 AS source8
                 , DestinationIP DIV 16777216 AS dest8
                 , DestinationPort as port
                 , COUNT(*) AS conns
            FROM Syslog
            GROUP BY source8, dest8, port) AS main
            JOIN
            (SELECT address, x, y FROM Nodes8) AS src
            ON (source8 = src.address)
            JOIN
            (SELECT address, x, y FROM Nodes8) AS dst
            ON (dest8 = dst.address);
        """
    rows = list(common.db.query(query))
    return rows


def preprocess_log():
    clean_tables()
    import_nodes()
    import_links()
    print("Pre-processing completed successfully.")

# If running as a script, begin by executing main.
if __name__ == "__main__":
    access = dbaccess.test_database()
    if access == 1049:
        dbaccess.create_database()
    elif access == 1045:
        print("Database access denied. Check you username / password? (dbconfig_local.py)")
    else:
        preprocess_log()


# time python preprocess.py >/dev/null 2>/dev/null
# is about half of
# time python preprocess.py

