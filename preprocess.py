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


def import_nodes():

    # Get all /8 nodes. Load them into Nodes8
    query = """
    INSERT INTO Nodes8 (IPAddress, connections, children, radius)
    SELECT cluster.address AS ipa
        , SUM(cluster.conns) AS connections
        , COUNT(cluster.child) AS children
        , (COUNT(cluster.child) / 127.5 + 0.5) * 2000
    FROM
        (SELECT ip DIV 16777216 AS 'address'
            , (ip - (ip DIV 16777216) * 16777216) DIV 65536 AS 'child'
            , COUNT(*) AS 'conns'
        FROM (
            (SELECT SourceIP AS ip
            FROM Syslog)
            UNION ALL
            (SELECT DestinationIP AS ip
            FROM Syslog)
        ) AS result
        GROUP BY address, child
    ) AS cluster
    GROUP BY ipa;
    """
    common.db.query(query)

    # Get all the /16 nodes. Load these into Nodes16
    query = """
        INSERT INTO Nodes16 (parent8, IPAddress, connections, children, radius)
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
        INSERT INTO Nodes24 (parent8, parent16, IPAddress, connections, children, radius)
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
        INSERT INTO Nodes32 (parent8, parent16, parent24, IPAddress, connections, children, radius)
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


def distSquared(x1, y1, x2, y2):
    return (x2-x1)**2 + (y2-y1)**2


def checkCollisions(node, nodelist, margin = 0):
    for n in nodelist:
        if distSquared(node.x, node.y, n.x, n.y) < (node.radius + n.radius + margin)**2:
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
            while checkCollisions(node, placed, 1000):
                node.x = random.random() * 40000 - 20000
                node.y = random.random() * 40000 - 20000
            placed.append(node)

        for node in placed:
            query = """
            UPDATE Nodes8
            SET x = $nx
              , y = $ny
            WHERE IPAddress = $nip"""
            qvars = {'nx':node.x, 'ny':node.y, 'nip':node.IPAddress}
            common.db.query(query, vars=qvars)


    # position the /16 within each node's parent
    query = """
        SELECT A.parent8, A.IPAddress, B.x AS px, B.y AS py, B.radius AS pr, A.x, A.y
        FROM
            Nodes16 A JOIN Nodes8 B
            ON A.parent8 = B.IPAddress
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
            WHERE parent8 = $pip8 AND IPAddress = $nip"""
            qvars = {'nx': node.x, 'ny': node.y, 'pip8': node.parent8, 'nip': node.IPAddress}
            common.db.query(query, vars=qvars)


    # position the /24 within each node's parent
    query = """
        SELECT A.parent8, A.parent16, A.IPAddress, B.x AS px, B.y AS py, B.radius AS pr, A.x, A.y
        FROM
            Nodes24 A JOIN Nodes16 B
            ON (A.parent16 = B.IPAddress AND A.parent8 = B.parent8)
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
            WHERE parent8 = $pip8 AND parent16 = $pip16 AND IPAddress = $nip"""
            qvars = {'nx': node.x, 'ny': node.y, 'pip8': node.parent8, 'pip16': node.parent16, 'nip': node.IPAddress}
            common.db.query(query, vars=qvars)


    # position the /32 within each node's parent
    query = """
        SELECT A.parent8, A.parent16, A.parent24, A.IPAddress, B.x AS px, B.y AS py, B.radius AS pr, A.x, A.y
        FROM
            Nodes32 A JOIN Nodes24 B
            ON (A.parent24 = B.IPAddress AND A.parent16 = B.parent16 AND A.parent8 = B.parent8)
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
            WHERE parent8 = $pip8 AND parent16 = $pip16  AND parent24 = $pip24 AND IPAddress = $nip"""
            qvars = {'nx': node.x, 'ny': node.y, 'pip8': node.parent8, 'pip16': node.parent16, 'pip24': node.parent24, 'nip': node.IPAddress}
            common.db.query(query, vars=qvars)


def import_links():
    pass


def preprocess_log():
    clean_tables()
    import_nodes()
    position_nodes()
    import_links()
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
