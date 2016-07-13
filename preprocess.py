"""
Preprocess the data in the database's upload table Syslog
"""

import common
import dbaccess
import random


def clean_tables():
    common.db.query("DELETE FROM Nodes32;")
    common.db.query("DELETE FROM Nodes24;")
    common.db.query("DELETE FROM Nodes16;")
    common.db.query("DELETE FROM Nodes8;")
    common.db.query("DELETE FROM Links32;")
    common.db.query("DELETE FROM Links24;")
    common.db.query("DELETE FROM Links16;")
    common.db.query("DELETE FROM Links8;")


def import_nodes():

    # Get all /8 nodes. Load them into Nodes8
    query = """
    INSERT INTO Nodes8 (address, connections, children, radius)
    SELECT cluster.nip AS address
        , SUM(cluster.conns) AS connections
        , COUNT(cluster.child) AS children
        , (COUNT(cluster.child) / 127.5 + 0.5) * 2000
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
    common.db.query(query)

    # Get all the /16 nodes. Load these into Nodes16
    query = """
        INSERT INTO Nodes16 (parent8, address, connections, children, radius)
        SELECT cluster.pip8 AS parent8
            , cluster.nip AS address
            , SUM(cluster.conns) AS connections
            , COUNT(cluster.child) AS children
            , (COUNT(cluster.child) / 127.5 + 0.5) * 200
        FROM
            (SELECT ip DIV 16777216 AS 'pip8'
                , (ip - (ip DIV 16777216) * 16777216) DIV 65536 AS 'nip'
                , (ip - (ip DIV 65536) * 65536) DIV 256 AS 'child'
                , COUNT(*) AS 'conns'
            FROM (
                (SELECT SourceIP AS ip
                FROM Syslog)
                UNION ALL
                (SELECT DestinationIP AS ip
                FROM Syslog)
            ) as result
            GROUP BY pip8, nip, child
        ) AS cluster
        GROUP BY parent8, address;
        """
    common.db.query(query)

    # Get all the /24 nodes. Load these into Nodes24
    query = """
        INSERT INTO Nodes24 (parent8, parent16, address, connections, children, radius)
        SELECT cluster.pip8 AS parent8
            , cluster.pip16 AS parent16
            , cluster.nip AS address
            , SUM(cluster.conns) AS connections
            , COUNT(cluster.child) AS children
            , (COUNT(cluster.child) / 127.5 + 0.5) * 20
        FROM
            (SELECT ip DIV 16777216 AS 'pip8'
                , (ip - (ip DIV 16777216) * 16777216) DIV 65536 AS 'pip16'
                , (ip - (ip DIV 65536) * 65536) DIV 256 AS 'nip'
                , (ip - (ip DIV 256) * 256) AS 'child'
                , COUNT(*) AS 'conns'
            FROM (
                (SELECT SourceIP AS ip
                FROM Syslog)
                UNION ALL
                (SELECT DestinationIP AS ip
                FROM Syslog)
            ) as result
            GROUP BY pip8, pip16, nip, child
        ) AS cluster
        GROUP BY parent8, parent16, address;
        """
    common.db.query(query)

    # Get all the /32 nodes. Load these into Nodes32
    query = """
        INSERT INTO Nodes32 (parent8, parent16, parent24, address, connections, children, radius)
        SELECT cluster.pip8 AS parent8
            , cluster.pip16 AS parent16
            , cluster.pip24 AS parent24
            , cluster.nip AS address
            , SUM(cluster.conns) AS connections
            , COUNT(cluster.child) AS children
            , (COUNT(cluster.child) / 127.5 + 0.5) * 2
        FROM
            (SELECT ip DIV 16777216 AS 'pip8'
                , (ip - (ip DIV 16777216) * 16777216) DIV 65536 AS 'pip16'
                , (ip - (ip DIV 65536) * 65536) DIV 256 AS 'pip24'
                , (ip - (ip DIV 256) * 256) AS 'nip'
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
        ) AS cluster
        GROUP BY parent8, parent16, parent24, address;
        """
    common.db.query(query)


def dist_squared(x1, y1, x2, y2):
    return (x2-x1)**2 + (y2-y1)**2


def check_collisions(node, nodelist, margin = 0):
    for n in nodelist:
        if dist_squared(node.x, node.y, n.x, n.y) < (node.radius + n.radius + margin)**2:
            return True
    return False


def position_nodes():
    # position the /8 first
    # arrangement radius is 20000
    # node radius is 2000
    rows = dbaccess.getNodes()
    placed = []
    if len(rows) > 0:
        placed.append(rows[0])
        for node in rows:
            while check_collisions(node, placed, 1000):
                node.x = random.random() * 40000 - 20000
                node.y = random.random() * 40000 - 20000
            placed.append(node)

        for node in placed:
            query = """
            UPDATE Nodes8
            SET x = $nx
              , y = $ny
            WHERE address = $nip"""
            qvars = {'nx': node.x,
                     'ny': node.y,
                     'nip': node.address}
            common.db.query(query, vars=qvars)

    # position the /16 within each node's parent
    query = """
        SELECT A.parent8, A.address, B.x AS px, B.y AS py, B.radius AS pr, A.x, A.y
        FROM
            Nodes16 A JOIN Nodes8 B
            ON A.parent8 = B.address
        ORDER BY A.parent8;
        """
    rows = common.db.query(query)
    placed = []
    if len(rows) > 0:
        parent = -1
        for node in rows:
            if node.parent8 != parent:
                parent = node.parent8
                node.x = node.px
                node.y = node.py
                placed.append(node)
            else:
                node.x = random.random() * node.pr * 2 - node.pr + node.px
                node.y = random.random() * node.pr * 2 - node.pr + node.py
                placed.append(node)
        for node in placed:
            query = """
            UPDATE Nodes16
            SET x = $nx
              , y = $ny
            WHERE parent8 = $pip8 AND address = $nip"""
            qvars = {'nx': node.x,
                     'ny': node.y,
                     'pip8': node.parent8,
                     'nip': node.address}
            common.db.query(query, vars=qvars)

    # position the /24 within each node's parent
    query = """
        SELECT A.parent8, A.parent16, A.address, B.x AS px, B.y AS py, B.radius AS pr, A.x, A.y
        FROM
            Nodes24 A JOIN Nodes16 B
            ON (A.parent16 = B.address AND A.parent8 = B.parent8)
            ORDER BY A.parent8, A.parent16;
        """
    rows = common.db.query(query)
    placed = []
    if len(rows) > 0:
        parent = -1
        for node in rows:
            # TODO: comparing parent16 by itself may backfire if sequential nodes have the same /16 and different /8
            #       such as 128.192.x.x followed by 129.192.x.x
            if node.parent16 != parent:
                parent = node.parent16
                node.x = node.px
                node.y = node.py
                placed.append(node)
            else:
                node.x = random.random() * node.pr * 2 - node.pr + node.px
                node.y = random.random() * node.pr * 2 - node.pr + node.py
                placed.append(node)
        for node in placed:
            query = """
            UPDATE Nodes24
            SET x = $nx
              , y = $ny
            WHERE parent8 = $pip8 AND parent16 = $pip16 AND address = $nip"""
            qvars = {'nx': node.x,
                     'ny': node.y,
                     'pip8': node.parent8,
                     'pip16': node.parent16,
                     'nip': node.address}
            common.db.query(query, vars=qvars)

    # position the /32 within each node's parent
    query = """
        SELECT A.parent8, A.parent16, A.parent24, A.address, B.x AS px, B.y AS py, B.radius AS pr, A.x, A.y
        FROM
            Nodes32 A JOIN Nodes24 B
            ON (A.parent24 = B.address AND A.parent16 = B.parent16 AND A.parent8 = B.parent8)
            ORDER BY A.parent8, A.parent16, A.parent24;
        """
    rows = common.db.query(query)
    placed = []
    if len(rows) > 0:
        parent = -1
        for node in rows:
            # TODO: comparing parent24 by itself may backfire if sequential nodes have the same /24 and different /16
            #       such as 192.168.16.x followed by 192.169.16.x
            if node.parent24 != parent:
                parent = node.parent24
                node.x = node.px
                node.y = node.py
                placed.append(node)
            else:
                node.x = random.random() * node.pr * 2 - node.pr + node.px
                node.y = random.random() * node.pr * 2 - node.pr + node.py
                placed.append(node)
        for node in placed:
            query = """
            UPDATE Nodes32
            SET x = $nx
              , y = $ny
            WHERE parent8 = $pip8 AND parent16 = $pip16  AND parent24 = $pip24 AND address = $nip"""
            qvars = {'nx': node.x,
                     'ny': node.y,
                     'pip8': node.parent8,
                     'pip16': node.parent16,
                     'pip24': node.parent24,
                     'nip': node.address}
            common.db.query(query, vars=qvars)


def import_links():
    # Populate Links8
    query = """
        INSERT INTO Links8 (source8, dest8, links, x1, y1, x2, y2)
        SELECT source8, dest8, conns, src.x, src.y, dst.x, dst.y
        FROM
            (SELECT SourceIP DIV 16777216 AS source8
                 , DestinationIP DIV 16777216 AS dest8
                 , COUNT(*) AS conns
            FROM Syslog
            GROUP BY source8, dest8) AS main
            JOIN
            (SELECT address, x, y FROM Nodes8) AS src
            ON (source8 = src.address)
            JOIN
            (SELECT address, x, y FROM Nodes8) AS dst
            ON (dest8 = dst.address);
        """
    common.db.query(query)

    # Populate Links16
    query = """
        INSERT INTO Links16 (source8, source16, dest8, dest16, links, x1, y1, x2, y2)
        SELECT source8, source16, dest8, dest16, conns, src.x, src.y, dst.x, dst.y
        FROM
            (SELECT SourceIP DIV 16777216 AS source8
                 , (SourceIP - (SourceIP DIV 16777216) * 16777216) DIV 65536 AS source16
                 , DestinationIP DIV 16777216 AS dest8
                 , (DestinationIP - (DestinationIP DIV 16777216) * 16777216) DIV 65536 AS dest16
                 , COUNT(*) AS conns
            FROM Syslog
            GROUP BY source8, source16, dest8, dest16) AS main
            JOIN
            (SELECT parent8, address, x, y FROM Nodes16) AS src
            ON (source8 = src.parent8 && source16 = src.address)
            JOIN
            (SELECT parent8, address, x, y FROM Nodes16) AS dst
            ON (dest8 = dst.parent8 && dest16 = dst.address);
    """
    common.db.query(query)

    # Populate Links24
    query = """
        INSERT INTO Links24 (source8, source16, source24, dest8, dest16, dest24, links, x1, y1, x2, y2)
        SELECT source8, source16, source24, dest8, dest16, dest24, conns, src.x, src.y, dst.x, dst.y
        FROM
            (SELECT SourceIP DIV 16777216 AS source8
                 , (SourceIP - (SourceIP DIV 16777216) * 16777216) DIV 65536 AS source16
                 , (SourceIP - (SourceIP DIV 65536) * 65536) DIV 256 AS source24
                 , DestinationIP DIV 16777216 AS dest8
                 , (DestinationIP - (DestinationIP DIV 16777216) * 16777216) DIV 65536 AS dest16
                 , (DestinationIP - (DestinationIP DIV 65536) * 65536) DIV 256 AS dest24
                 , COUNT(*) AS conns
            FROM Syslog
            GROUP BY source8, source16, source24, dest8, dest16, dest24) AS main
            JOIN
            (SELECT parent8, parent16, address, x, y FROM Nodes24) AS src
            ON (source8 = src.parent8 && source16 = src.parent16 && source24 = src.address)
            JOIN
            (SELECT parent8, parent16, address, x, y FROM Nodes24) AS dst
            ON (dest8 = dst.parent8 && dest16 = dst.parent16 && dest24 = dst.address);
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
            GROUP BY source8, source16, source24, source32, dest8, dest16, dest24, dest32, port) AS main
            JOIN
            (SELECT parent8, parent16, parent24, address, x, y FROM Nodes32) AS src
            ON (source8 = src.parent8 && source16 = src.parent16 && source24 = src.parent24 && source32 = src.address)
            JOIN
            (SELECT parent8, parent16, parent24, address, x, y FROM Nodes32) AS dst
            ON (dest8 = dst.parent8 && dest16 = dst.parent16 && dest24 = dst.parent24 && dest32 = dst.address);
    """
    common.db.query(query)


def preprocess_log():
    clean_tables()
    import_nodes()
    import_links()
    position_nodes()
    # do something with links...


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
# is 28 seconds
# time python preprocess.py
# is 51 seconds
