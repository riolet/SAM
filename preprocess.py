"""
Preprocess the data in the database's upload table Syslog
"""

import common
import dbaccess
import random


def import_nodes():

    # Get all /8 nodes. Load them into Nodes8
    query = """
    INSERT INTO Nodes8 (IPAddress, connections)
    SELECT ip DIV 16777216 AS 'address', COUNT(*) AS 'count'
    FROM (
        (SELECT SourceIP AS ip
        FROM Syslog)
        UNION ALL
        (SELECT DestinationIP AS ip
        FROM Syslog)
    ) as result
    GROUP BY address;
    """
    common.db.query(query)

    # Get all the /16 nodes. Load these into Nodes16
    query = """
        INSERT INTO Nodes16 (parent8, IPAddress, connections)
        SELECT ip DIV 16777216 AS 'parent8'
            , (ip - (ip DIV 16777216) * 16777216) DIV 65536 AS 'address'
            , COUNT(*) AS 'count'
        FROM (
            (SELECT SourceIP AS ip
            FROM Syslog)
            UNION ALL
            (SELECT DestinationIP AS ip
            FROM Syslog)
        ) as result
        GROUP BY parent8, address;
        """
    common.db.query(query)

    # Get all the /24 nodes. Load these into Nodes24
    query = """
        INSERT INTO Nodes24 (parent8, parent16, IPAddress, connections)
        SELECT ip DIV 16777216 AS 'parent8'
            , (ip - (ip DIV 16777216) * 16777216) DIV 65536 AS 'parent16'
            , (ip - (ip DIV 65536) * 65536) DIV 256 AS 'address'
            , COUNT(*) AS 'count'
        FROM (
            (SELECT SourceIP AS ip
            FROM Syslog)
            UNION ALL
            (SELECT DestinationIP AS ip
            FROM Syslog)
        ) as result
        GROUP BY parent8, parent16, address;
        """
    common.db.query(query)

    # Get all the /32 nodes. Load these into Nodes32
    query = """
        INSERT INTO Nodes32 (parent8, parent16, parent24, IPAddress, connections)
        SELECT ip DIV 16777216 AS 'parent8'
            , (ip - (ip DIV 16777216) * 16777216) DIV 65536 AS 'parent16'
            , (ip - (ip DIV 65536) * 65536) DIV 256 AS 'parent24'
            , (ip - (ip DIV 256) * 256) AS 'address'
            , COUNT(*) AS 'count'
        FROM (
            (SELECT SourceIP AS ip
            FROM Syslog)
            UNION ALL
            (SELECT DestinationIP AS ip
            FROM Syslog)
        ) as result
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
    placed8 = []
    for node in rows:
        node.radius = 2000
        while checkCollisions(node, placed8, 1000):
            node.x = random.random() * 40000 - 20000
            node.y = random.random() * 40000 - 20000
        placed8.append(node)

    for node in placed8:
        query = """
        UPDATE Nodes8
        SET x = $nx
          , y = $ny
          , radius = $nr
        WHERE IPAddress = $nIP"""
        qvars = {'nx':node.x, 'ny':node.y, 'nr':node.radius, 'nIP':node.IPAddress}
        common.db.query(query, vars=qvars)

    # position the /16 within each node's parent
    query = """
        SELECT A.parent8, A.IPAddress, B.x AS px, B.y AS py, A.x, A.y
        FROM
            Nodes16 A JOIN Nodes8 B
            ON A.parent8 = B.IPAddress;
        """
    rows = common.db.query(query)
    placed16 = []
    for node in rows:
        node.radius = 200
        safetyCounter = 0
        #while checkCollisions(node, placed16, 100):
        node.x = random.random() * 4000 - 2000 + node.px
        node.y = random.random() * 4000 - 2000 + node.py
        #    safetyCounter += 1
        #    if safetyCounter > 100:
        #        break
        placed16.append(node)
    for node in placed16:
        query = """
        UPDATE Nodes16
        SET x = $nx
          , y = $ny
          , radius = $nr
        WHERE parent8 = $pip8 AND IPAddress = $nip"""
        qvars = {'nx': node.x, 'ny': node.y, 'nr': node.radius, 'pip8': node.parent8, 'nip': node.IPAddress}
        common.db.query(query, vars=qvars)

    # position the /24 within each node's parent
query = """
    SELECT A.parent8, A.parent16, A.IPAddress, B.x AS px, B.y AS py, A.x, A.y
    FROM
        Nodes24 A JOIN Nodes16 B
        ON (A.parent16 = B.IPAddress AND A.parent8 = B.parent8);
    """
rows = common.db.query(query)
placed24 = []
for node in rows:
    node.radius = 20
    safetyCounter = 0
    # while checkCollisions(node, placed24, 10):
    node.x = random.random() * 400 - 200 + node.px
    node.y = random.random() * 400 - 200 + node.py
    #    safetyCounter += 1
    #    if safetyCounter > 100:
    #        break
    placed24.append(node)
for node in placed24:
    query = """
    UPDATE Nodes24
    SET x = $nx
      , y = $ny
      , radius = $nr
    WHERE parent8 = $pip8 AND parent16 = $pip16 AND IPAddress = $nip"""
    qvars = {'nx': node.x, 'ny': node.y, 'nr': node.radius, 'pip8': node.parent8, 'pip16': node.parent16, 'nip': node.IPAddress}
    common.db.query(query, vars=qvars)

    # position the /32 within each node's parent
    query = """
        SELECT A.parent8, A.parent16, A.parent24, A.IPAddress, B.x AS px, B.y AS py, A.x, A.y
        FROM
            Nodes32 A JOIN Nodes24 B
            ON (A.parent24 = B.IPAddress AND A.parent16 = B.parent16 AND A.parent8 = B.parent8);
        """
    rows = common.db.query(query)
    placed32 = []
    for node in rows:
        node.radius = 2
        safetyCounter = 0
        # while checkCollisions(node, placed24, 10):
        node.x = random.random() * 40 - 20 + node.px
        node.y = random.random() * 40 - 20 + node.py
        #    safetyCounter += 1
        #    if safetyCounter > 100:
        #        break
        placed32.append(node)
    for node in placed32:
        query = """
        UPDATE Nodes32
        SET x = $nx
          , y = $ny
          , radius = $nr
        WHERE parent8 = $pip8 AND parent16 = $pip16  AND parent24 = $pip24 AND IPAddress = $nip"""
        qvars = {'nx': node.x, 'ny': node.y, 'nr': node.radius, 'pip8': node.parent8, 'pip16': node.parent16, 'pip24': node.parent24, 'nip': node.IPAddress}
        common.db.query(query, vars=qvars)


def import_links():
    pass


def preprocess_log():
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
