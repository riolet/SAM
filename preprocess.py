"""
Preprocess the data in the database's upload table Syslog
"""

import common
import dbaccess

# method to create staging and master tables 
def create_tables():
    # calls the sql file to create staging tables
    dbaccess.exec_sql("./sql/setup_tables.sql")
    # calls the sql file to create master tables
    dbaccess.exec_sql("./sql/setup_master_tables.sql")

def import_nodes():
    # count(children) / 127.5 + 0.5) gives a number between 0.5 and 2.5
    # radius used to be:
    #    (COUNT(cluster.child) / 127.5 + 0.5) * 6000
    # instead of:
    #    6000

    # Get all /8 nodes. Load them into Nodes8
    query = """
        INSERT INTO Nodes (ipstart, ipend, subnet, x, y, radius)
        SELECT (log.ip * 16777216) AS 'ipstart'
            , ((log.ip + 1) * 16777216 - 1) AS 'ipend'
            , 8 AS 'subnet'
            , (331776 * (log.ip % 16) / 7.5 - 331776) AS 'x'
            , (331776 * (log.ip DIV 16) / 7.5 - 331776) AS 'y'
            , 20736 AS 'radius'
        FROM(
            SELECT SourceIP DIV 16777216 AS 'ip'
            FROM Syslog
            UNION
            SELECT DestinationIP DIV 16777216 AS 'ip'
            FROM Syslog
        ) AS log;
    """
    qvars = {"radius": 331776}
    common.db.query(query, vars=qvars)

    # Get all the /16 nodes. Load these into Nodes16
    query = """
        INSERT INTO Nodes (ipstart, ipend, subnet, x, y, radius)
        SELECT (log.ip * 65536) AS 'ipstart'
            , ((log.ip + 1) * 65536 - 1) AS 'ipend'
            , 16 AS 'subnet'
            , ((parent.radius * (log.ip MOD 16) / 7.5 - parent.radius) + parent.x) AS 'x'
            , ((parent.radius * (log.ip MOD 256 DIV 16) / 7.5 - parent.radius) + parent.y) AS 'y'
            , (parent.radius / 24) AS 'radius'
        FROM(
            SELECT SourceIP DIV 65536 AS 'ip'
            FROM Syslog
            UNION
            SELECT DestinationIP DIV 65536 AS 'ip'
            FROM Syslog
        ) AS log
        JOIN Nodes AS parent
            ON parent.subnet=8 && parent.ipstart = (log.ip DIV 256 * 16777216);
        """
    common.db.query(query)

    # Get all the /24 nodes. Load these into Nodes24
    query = """
        INSERT INTO Nodes (ipstart, ipend, subnet, x, y, radius)
        SELECT (log.ip * 256) AS 'ipstart'
            , ((log.ip + 1) * 256 - 1) AS 'ipend'
            , 24 AS 'subnet'
            , ((parent.radius * (log.ip MOD 16) / 7.5 - parent.radius) + parent.x) AS 'x'
            , ((parent.radius * (log.ip MOD 256 DIV 16) / 7.5 - parent.radius) + parent.y) AS 'y'
            , (parent.radius / 24) AS 'radius'
        FROM(
            SELECT SourceIP DIV 256 AS 'ip'
            FROM Syslog
            UNION
            SELECT DestinationIP DIV 256 AS 'ip'
            FROM Syslog
        ) AS log
        JOIN Nodes AS parent
            ON parent.subnet=16 && parent.ipstart = (log.ip DIV 256 * 65536);
        """
    common.db.query(query)

    # Get all the /32 nodes. Load these into Nodes32
    query = """
        INSERT INTO Nodes (ipstart, ipend, subnet, x, y, radius)
        SELECT log.ip AS 'ipstart'
            , log.ip AS 'ipend'
            , 32 AS 'subnet'
            , ((parent.radius * (log.ip MOD 16) / 7.5 - parent.radius) + parent.x) AS 'x'
            , ((parent.radius * (log.ip MOD 256 DIV 16) / 7.5 - parent.radius) + parent.y) AS 'y'
            , (parent.radius / 24) AS 'radius'
        FROM(
            SELECT SourceIP AS 'ip'
            FROM Syslog
            UNION
            SELECT DestinationIP AS 'ip'
            FROM Syslog
        ) AS log
        JOIN Nodes AS parent
            ON parent.subnet=24 && parent.ipstart = (log.ip DIV 256 * 256);
        """
    common.db.query(query)


def import_links():
    build_Links()

    # Populate Links8
    deduce_LinksIn()

    # Populate Links16
    deduce_LinksOut()


def build_Links():
    query = """
        INSERT INTO Links (src, dst, port, timestamp, links)
        SELECT SourceIP, DestinationIP, DestinationPort
            , SUBSTRING(TIMESTAMPADD(MINUTE, -(MINUTE(Timestamp) MOD 5), Timestamp), 1, 16) AS ts
            , COUNT(1) AS links
        FROM Syslog
        GROUP BY SourceIP, DestinationIP, DestinationPort, ts;
    """
    common.db.query(query)


def deduce_LinksIn():
    # /8 links
    query = """
        INSERT INTO LinksIn (src_start, src_end, dst_start, dst_end, port, timestamp, links)
        SELECT src DIV 16777216 * 16777216 AS 'src_start'
            , src DIV 16777216 * 16777216 + 16777215 AS 'src_end'
            , dst DIV 16777216 * 16777216 AS 'dst_start'
            , dst DIV 16777216 * 16777216 + 16777215 AS 'dst_end'
            , port
            , timestamp
            , SUM(links)
        FROM Links
        GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp;
    """
    common.db.query(query)

    # /16 links
    query = """
        INSERT INTO LinksIn (src_start, src_end, dst_start, dst_end, port, timestamp, links)
        SELECT src DIV 65536 * 65536 AS 'src_start'
            , src DIV 65536 * 65536 + 65535 AS 'src_end'
            , dst DIV 65536 * 65536 AS 'dst_start'
            , dst DIV 65536 * 65536 + 65535 AS 'dst_end'
            , port
            , timestamp
            , SUM(links)
        FROM Links
        WHERE (src DIV 16777216) = (dst DIV 16777216)
        GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp
        UNION
        SELECT src DIV 16777216 * 16777216 AS 'src_start'
            , src DIV 16777216 * 16777216 + 16777215 AS 'src_end'
            , dst DIV 65536 * 65536 AS 'dst_start'
            , dst DIV 65536 * 65536 + 65535 AS 'dst_end'
            , port
            , timestamp
            , SUM(links)
        FROM Links
        WHERE (src DIV 16777216) != (dst DIV 16777216)
        GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp;
    """
    common.db.query(query)

    # /24 links
    query = """
        INSERT INTO LinksIn (src_start, src_end, dst_start, dst_end, port, timestamp, links)
        SELECT src DIV 256 * 256 AS 'src_start'
            , src DIV 256 * 256 + 255 AS 'src_end'
            , dst DIV 256 * 256 AS 'dst_start'
            , dst DIV 256 * 256 + 255 AS 'dst_end'
            , port
            , timestamp
            , SUM(links)
        FROM Links
        WHERE (src DIV 65536) = (dst DIV 65536)
        GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp
        UNION
        SELECT src DIV 65536 * 65536 AS 'src_start'
            , src DIV 65536 * 65536 + 65535 AS 'src_end'
            , dst DIV 256 * 256 AS 'dst_start'
            , dst DIV 256 * 256 + 255 AS 'dst_end'
            , port
            , timestamp
            , SUM(links)
        FROM Links
        WHERE (src DIV 16777216) = (dst DIV 16777216)
          AND (src DIV 65536) != (dst DIV 65536)
        GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp
        UNION
        SELECT src DIV 16777216 * 16777216 AS 'src_start'
            , src DIV 16777216 * 16777216 + 16777215 AS 'src_end'
            , dst DIV 256 * 256 AS 'dst_start'
            , dst DIV 256 * 256 + 255 AS 'dst_end'
            , port
            , timestamp
            , SUM(links)
        FROM Links
        WHERE (src DIV 16777216) != (dst DIV 16777216)
        GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp;
    """
    common.db.query(query)

    # /32 links
    query = """
        INSERT INTO LinksIn (src_start, src_end, dst_start, dst_end, port, timestamp, links)
        SELECT src AS 'src_start'
            , src AS 'src_end'
            , dst AS 'dst_start'
            , dst AS 'dst_end'
            , port
            , timestamp
            , SUM(links)
        FROM Links
        WHERE (src DIV 256) = (dst DIV 256)
        GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp
        UNION
        SELECT src DIV 256 * 256 AS 'src_start'
            , src DIV 256 * 256 + 255 AS 'src_end'
            , dst AS 'dst_start'
            , dst AS 'dst_end'
            , port
            , timestamp
            , SUM(links)
        FROM Links
        WHERE (src DIV 65536) = (dst DIV 65536)
          AND (src DIV 256) != (dst DIV 256)
        GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp
        UNION
        SELECT src DIV 65536 * 65536 AS 'src_start'
            , src DIV 65536 * 65536 + 65535 AS 'src_end'
            , dst AS 'dst_start'
            , dst AS 'dst_end'
            , port
            , timestamp
            , SUM(links)
        FROM Links
        WHERE (src DIV 16777216) = (dst DIV 16777216)
          AND (src DIV 65536) != (dst DIV 65536)
        GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp
        UNION
        SELECT src DIV 16777216 * 16777216 AS 'src_start'
            , src DIV 16777216 * 16777216 + 16777215 AS 'src_end'
            , dst AS 'dst_start'
            , dst AS 'dst_end'
            , port
            , timestamp
            , SUM(links)
        FROM Links
        WHERE (src DIV 16777216) != (dst DIV 16777216)
        GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp;
    """
    common.db.query(query)


def deduce_LinksOut():
    # /8 links
    query = """
        INSERT INTO LinksOut (src_start, src_end, dst_start, dst_end, port, timestamp, links)
        SELECT src DIV 16777216 * 16777216 AS 'src_start'
            , src DIV 16777216 * 16777216 + 16777215 AS 'src_end'
            , dst DIV 16777216 * 16777216 AS 'dst_start'
            , dst DIV 16777216 * 16777216 + 16777215 AS 'dst_end'
            , port
            , timestamp
            , SUM(links)
        FROM Links
        GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp;
    """
    common.db.query(query)

    # /16 links
    query = """
        INSERT INTO LinksOut (src_start, src_end, dst_start, dst_end, port, timestamp, links)
        SELECT src DIV 65536 * 65536 AS 'src_start'
            , src DIV 65536 * 65536 + 65535 AS 'src_end'
            , dst DIV 65536 * 65536 AS 'dst_start'
            , dst DIV 65536 * 65536 + 65535 AS 'dst_end'
            , port
            , timestamp
            , SUM(links)
        FROM Links
        WHERE (src DIV 16777216) = (dst DIV 16777216)
        GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp
        UNION
        SELECT src DIV 65536 * 65536 AS 'src_start'
            , src DIV 65536 * 65536 + 65535 AS 'src_end'
            , dst DIV 16777216 * 16777216 AS 'dst_start'
            , dst DIV 16777216 * 16777216 + 16777215 AS 'dst_end'
            , port
            , timestamp
            , SUM(links)
        FROM Links
        WHERE (src DIV 16777216) != (dst DIV 16777216)
        GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp;
    """
    common.db.query(query)

    # /24 links
    query = """
        INSERT INTO LinksOut (src_start, src_end, dst_start, dst_end, port, timestamp, links)
        SELECT src DIV 256 * 256 AS 'src_start'
            , src DIV 256 * 256 + 255 AS 'src_end'
            , dst DIV 256 * 256 AS 'dst_start'
            , dst DIV 256 * 256 + 255 AS 'dst_end'
            , port
            , timestamp
            , SUM(links)
        FROM Links
        WHERE (src DIV 65536) = (dst DIV 65536)
        GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp
        UNION
        SELECT src DIV 256 * 256 AS 'src_start'
            , src DIV 256 * 256 + 255 AS 'src_end'
            , dst DIV 65536 * 65536 AS 'dst_start'
            , dst DIV 65536 * 65536 + 65535 AS 'dst_end'
            , port
            , timestamp
            , SUM(links)
        FROM Links
        WHERE (src DIV 16777216) = (dst DIV 16777216)
          AND (src DIV 65536) != (dst DIV 65536)
        GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp
        UNION
        SELECT src DIV 256 * 256 AS 'src_start'
            , src DIV 256 * 256 + 255 AS 'src_end'
            , dst DIV 16777216 * 16777216 AS 'dst_start'
            , dst DIV 16777216 * 16777216 + 16777215 AS 'dst_end'
            , port
            , timestamp
            , SUM(links)
        FROM Links
        WHERE (src DIV 16777216) != (dst DIV 16777216)
        GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp;
    """
    common.db.query(query)

    # /32 links
    query = """
        INSERT INTO LinksOut (src_start, src_end, dst_start, dst_end, port, timestamp, links)
        SELECT src AS 'src_start'
            , src AS 'src_end'
            , dst AS 'dst_start'
            , dst AS 'dst_end'
            , port
            , timestamp
            , SUM(links)
        FROM Links
        WHERE (src DIV 256) = (dst DIV 256)
        GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp
        UNION
        SELECT src AS 'src_start'
            , src AS 'src_end'
            , dst DIV 256 * 256 AS 'dst_start'
            , dst DIV 256 * 256 + 255 AS 'dst_end'
            , port
            , timestamp
            , SUM(links)
        FROM Links
        WHERE (src DIV 65536) = (dst DIV 65536)
          AND (src DIV 256) != (dst DIV 256)
        GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp
        UNION
        SELECT src AS 'src_start'
            , src AS 'src_end'
            , dst DIV 65536 * 65536 AS 'dst_start'
            , dst DIV 65536 * 65536 + 65535 AS 'dst_end'
            , port
            , timestamp
            , SUM(links)
        FROM Links
        WHERE (src DIV 16777216) = (dst DIV 16777216)
          AND (src DIV 65536) != (dst DIV 65536)
        GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp
        UNION
        SELECT src AS 'src_start'
            , src AS 'src_end'
            , dst DIV 16777216 * 16777216 AS 'dst_start'
            , dst DIV 16777216 * 16777216 + 16777215 AS 'dst_end'
            , port
            , timestamp
            , SUM(links)
        FROM Links
        WHERE (src DIV 16777216) != (dst DIV 16777216)
        GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp;
    """
    common.db.query(query)

# method to copy all data from staging tables to master tables
def copy_to_master():
    dbaccess.exec_sql("./sql/copy_to_master_tables.sql")
    
# method to delete all data from staging tables
def delete_staging_data():
    dbaccess.exec_sql("./sql/delete_staging_data.sql")


def preprocess_log():

    create_tables() # create staging tables and master tables if they don't exist
    import_nodes() # import all node info into staging tables
    import_links() # import all link info into staging tables
    copy_to_master() # copy data from staging to master tables
    delete_staging_data() # delete all data from staging tables

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

