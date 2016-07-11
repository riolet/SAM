"""
Preprocess the data in the database's upload table Syslog
"""

import common
import dbaccess


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
    common.db.query(query);

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
    common.db.query(query);

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
    common.db.query(query);

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
    common.db.query(query);


def position_nodes():
    # position the /8 first
    # position the /16 within each node's parent
    # position the /24 within each node's parent
    # position the /32 within each node's parent


def preprocess_log():
    import_nodes()
    position_nodes()
    # do something with links...




# If running as a script, begin by executing main.
if __name__ == "__main__":
    access = dbaccess.test_database()
    if access == 1049:
        dbaccess.create_database();
    elif access == 1045:
        print("Database access denied. Check you username / password? (dbconfig_local.py)")
    else:
        preprocess_log()
