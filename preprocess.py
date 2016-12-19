"""
Preprocess the data in the database's upload table Syslog
"""

import common
import dbaccess
import integrity
import sys

# DB connection to use. `common.db` echos every statement to stderr, `common.db_quiet` does not.
db = common.db_quiet


def determine_datasource(argv):
    settings = dbaccess.get_settings(all=True)
    default_ds = settings['datasource']['id']
    custom_ds = 0
    if len(argv) >= 2:
        requested_ds = argv[1]
        for ds in settings['datasources']:
            if ds['name'] == requested_ds:
                custom_ds = ds['id']
                break

    if custom_ds > 0:
        return custom_ds
    else:
        return default_ds


def import_nodes():
    prefix = dbaccess.get_settings_cached()['prefix']

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
            SELECT src DIV 16777216 AS 'ip'
            FROM {prefix}Syslog
            UNION
            SELECT dst DIV 16777216 AS 'ip'
            FROM {prefix}Syslog
        ) AS log
        LEFT JOIN Nodes AS `filter`
            ON (log.ip * 16777216) = `filter`.ipstart AND ((log.ip + 1) * 16777216 - 1) = `filter`.ipend
        WHERE filter.ipstart IS NULL;
    """.format(prefix=prefix)
    qvars = {"radius": 331776}
    db.query(query, vars=qvars)

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
            SELECT src DIV 65536 AS 'ip'
            FROM {prefix}Syslog
            UNION
            SELECT dst DIV 65536 AS 'ip'
            FROM {prefix}Syslog
        ) AS log
        JOIN Nodes AS parent
            ON parent.subnet=8 && parent.ipstart = (log.ip DIV 256 * 16777216)
        LEFT JOIN Nodes AS `filter`
            ON (log.ip * 65536) = `filter`.ipstart AND ((log.ip + 1) * 65536 - 1) = `filter`.ipend
        WHERE filter.ipstart IS NULL;
        """.format(prefix=prefix)
    db.query(query)

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
            SELECT src DIV 256 AS 'ip'
            FROM {prefix}Syslog
            UNION
            SELECT dst DIV 256 AS 'ip'
            FROM {prefix}Syslog
        ) AS log
        JOIN Nodes AS parent
            ON parent.subnet=16 && parent.ipstart = (log.ip DIV 256 * 65536)
        LEFT JOIN Nodes AS `filter`
            ON (log.ip * 256) = `filter`.ipstart AND ((log.ip + 1) * 256 - 1) = `filter`.ipend
        WHERE filter.ipstart IS NULL;
        """.format(prefix=prefix)
    db.query(query)

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
            SELECT src AS 'ip'
            FROM {prefix}Syslog
            UNION
            SELECT dst AS 'ip'
            FROM {prefix}Syslog
        ) AS log
        JOIN Nodes AS parent
            ON parent.subnet=24 && parent.ipstart = (log.ip DIV 256 * 256)
        LEFT JOIN Nodes AS `filter`
            ON log.ip = `filter`.ipstart AND log.ip = `filter`.ipend
        WHERE filter.ipstart IS NULL;
        """.format(prefix=prefix)
    db.query(query)


def build_Links(prefix):
    query = """
        INSERT INTO {prefix}staging_Links (src, dst, port, protocol, timestamp,
            links, bytes_sent, bytes_received, packets_sent, packets_received, duration)
        SELECT src
            , dst
            , dstport
            , protocol
            , SUBSTRING(TIMESTAMPADD(MINUTE, -(MINUTE(Timestamp) MOD 5), Timestamp), 1, 16) AS ts
            , COUNT(1) AS links
            , SUM(bytes_sent) AS 'bytes_sent'
            , SUM(bytes_received) AS 'bytes_received'
            , SUM(packets_sent) AS 'packets_sent'
            , SUM(packets_received) AS 'packets_received'
            , AVG(duration) AS 'duration'
        FROM {prefix}Syslog
        GROUP BY src, dst, dstport, protocol, ts;
    """.format(prefix=prefix)
    db.query(query)


def build_link_aggregates(prefix):
    rows = db.select("{0}staging_Links".format(prefix), what="MIN(timestamp) AS 'start', MAX(timestamp) AS 'end'")
    timerange = rows[0]

    db.delete("{0}LinksIn".format(prefix), where="timestamp BETWEEN $start AND $end", vars=timerange)
    db.delete("{0}LinksOut".format(prefix), where="timestamp BETWEEN $start AND $end", vars=timerange)
    deduce_LinksIn(prefix, timerange.start, timerange.end)
    deduce_LinksOut(prefix, timerange.start, timerange.end)


def deduce_LinksIn(prefix, timestart, timestop):
    time_vars = {
        "start": timestart,
        "stop": timestop
    }

    # /8 links
    query = """
        INSERT INTO {prefix}LinksIn (src_start, src_end, dst_start, dst_end, protocols, port, timestamp, links, bytes, packets)
        SELECT src DIV 16777216 * 16777216 AS 'src_start'
            , src DIV 16777216 * 16777216 + 16777215 AS 'src_end'
            , dst DIV 16777216 * 16777216 AS 'dst_start'
            , dst DIV 16777216 * 16777216 + 16777215 AS 'dst_end'
            , GROUP_CONCAT(DISTINCT protocol SEPARATOR ",")
            , port
            , timestamp
            , SUM(links)
            , SUM(bytes_sent + COALESCE(bytes_received, 0))
            , SUM(packets_sent + COALESCE(packets_received, 0))
        FROM {prefix}Links
        WHERE timestamp BETWEEN $start AND $stop
        GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp;
    """.format(prefix=prefix)
    db.query(query, vars=time_vars)

    # /16 links
    query = """
        INSERT INTO {prefix}LinksIn (src_start, src_end, dst_start, dst_end, protocols, port, timestamp, links, bytes, packets)
        SELECT src DIV 65536 * 65536 AS 'src_start'
            , src DIV 65536 * 65536 + 65535 AS 'src_end'
            , dst DIV 65536 * 65536 AS 'dst_start'
            , dst DIV 65536 * 65536 + 65535 AS 'dst_end'
            , GROUP_CONCAT(DISTINCT protocol SEPARATOR ",")
            , port
            , timestamp
            , SUM(links)
            , SUM(bytes_sent + COALESCE(bytes_received, 0))
            , SUM(packets_sent + COALESCE(packets_received, 0))
        FROM {prefix}Links
        WHERE (src DIV 16777216) = (dst DIV 16777216)
          AND timestamp BETWEEN $start AND $stop
        GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp
        UNION
        SELECT src DIV 16777216 * 16777216 AS 'src_start'
            , src DIV 16777216 * 16777216 + 16777215 AS 'src_end'
            , dst DIV 65536 * 65536 AS 'dst_start'
            , dst DIV 65536 * 65536 + 65535 AS 'dst_end'
            , GROUP_CONCAT(DISTINCT protocol SEPARATOR ",")
            , port
            , timestamp
            , SUM(links)
            , SUM(bytes_sent + COALESCE(bytes_received, 0))
            , SUM(packets_sent + COALESCE(packets_received, 0))
        FROM {prefix}Links
        WHERE (src DIV 16777216) != (dst DIV 16777216)
          AND timestamp BETWEEN $start AND $stop
        GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp;
    """.format(prefix=prefix)
    db.query(query, vars=time_vars)

    # /24 links
    query = """
        INSERT INTO {prefix}LinksIn (src_start, src_end, dst_start, dst_end, protocols, port, timestamp, links, bytes, packets)
        SELECT src DIV 256 * 256 AS 'src_start'
            , src DIV 256 * 256 + 255 AS 'src_end'
            , dst DIV 256 * 256 AS 'dst_start'
            , dst DIV 256 * 256 + 255 AS 'dst_end'
            , GROUP_CONCAT(DISTINCT protocol SEPARATOR ",")
            , port
            , timestamp
            , SUM(links)
            , SUM(bytes_sent + COALESCE(bytes_received, 0))
            , SUM(packets_sent + COALESCE(packets_received, 0))
        FROM {prefix}Links
        WHERE (src DIV 65536) = (dst DIV 65536)
          AND timestamp BETWEEN $start AND $stop
        GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp
        UNION
        SELECT src DIV 65536 * 65536 AS 'src_start'
            , src DIV 65536 * 65536 + 65535 AS 'src_end'
            , dst DIV 256 * 256 AS 'dst_start'
            , dst DIV 256 * 256 + 255 AS 'dst_end'
            , GROUP_CONCAT(DISTINCT protocol SEPARATOR ",")
            , port
            , timestamp
            , SUM(links)
            , SUM(bytes_sent + COALESCE(bytes_received, 0))
            , SUM(packets_sent + COALESCE(packets_received, 0))
        FROM {prefix}Links
        WHERE (src DIV 16777216) = (dst DIV 16777216)
          AND (src DIV 65536) != (dst DIV 65536)
          AND timestamp BETWEEN $start AND $stop
        GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp
        UNION
        SELECT src DIV 16777216 * 16777216 AS 'src_start'
            , src DIV 16777216 * 16777216 + 16777215 AS 'src_end'
            , dst DIV 256 * 256 AS 'dst_start'
            , dst DIV 256 * 256 + 255 AS 'dst_end'
            , GROUP_CONCAT(DISTINCT protocol SEPARATOR ",")
            , port
            , timestamp
            , SUM(links)
            , SUM(bytes_sent + COALESCE(bytes_received, 0))
            , SUM(packets_sent + COALESCE(packets_received, 0))
        FROM {prefix}Links
        WHERE (src DIV 16777216) != (dst DIV 16777216)
          AND timestamp BETWEEN $start AND $stop
        GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp;
    """.format(prefix=prefix)
    db.query(query, vars=time_vars)

    # /32 links
    query = """
        INSERT INTO {prefix}LinksIn (src_start, src_end, dst_start, dst_end, protocols, port, timestamp, links, bytes, packets)
        SELECT src AS 'src_start'
            , src AS 'src_end'
            , dst AS 'dst_start'
            , dst AS 'dst_end'
            , GROUP_CONCAT(DISTINCT protocol SEPARATOR ",")
            , port
            , timestamp
            , SUM(links)
            , SUM(bytes_sent + COALESCE(bytes_received, 0))
            , SUM(packets_sent + COALESCE(packets_received, 0))
        FROM {prefix}Links
        WHERE (src DIV 256) = (dst DIV 256)
          AND timestamp BETWEEN $start AND $stop
        GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp
        UNION
        SELECT src DIV 256 * 256 AS 'src_start'
            , src DIV 256 * 256 + 255 AS 'src_end'
            , dst AS 'dst_start'
            , dst AS 'dst_end'
            , GROUP_CONCAT(DISTINCT protocol SEPARATOR ",")
            , port
            , timestamp
            , SUM(links)
            , SUM(bytes_sent + COALESCE(bytes_received, 0))
            , SUM(packets_sent + COALESCE(packets_received, 0))
        FROM {prefix}Links
        WHERE (src DIV 65536) = (dst DIV 65536)
          AND (src DIV 256) != (dst DIV 256)
          AND timestamp BETWEEN $start AND $stop
        GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp
        UNION
        SELECT src DIV 65536 * 65536 AS 'src_start'
            , src DIV 65536 * 65536 + 65535 AS 'src_end'
            , dst AS 'dst_start'
            , dst AS 'dst_end'
            , GROUP_CONCAT(DISTINCT protocol SEPARATOR ",")
            , port
            , timestamp
            , SUM(links)
            , SUM(bytes_sent + COALESCE(bytes_received, 0))
            , SUM(packets_sent + COALESCE(packets_received, 0))
        FROM {prefix}Links
        WHERE (src DIV 16777216) = (dst DIV 16777216)
          AND (src DIV 65536) != (dst DIV 65536)
          AND timestamp BETWEEN $start AND $stop
        GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp
        UNION
        SELECT src DIV 16777216 * 16777216 AS 'src_start'
            , src DIV 16777216 * 16777216 + 16777215 AS 'src_end'
            , dst AS 'dst_start'
            , dst AS 'dst_end'
            , GROUP_CONCAT(DISTINCT protocol SEPARATOR ",")
            , port
            , timestamp
            , SUM(links)
            , SUM(bytes_sent + COALESCE(bytes_received, 0))
            , SUM(packets_sent + COALESCE(packets_received, 0))
        FROM {prefix}Links
        WHERE (src DIV 16777216) != (dst DIV 16777216)
          AND timestamp BETWEEN $start AND $stop
        GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp;
    """.format(prefix=prefix)
    db.query(query, vars=time_vars)


def deduce_LinksOut(prefix, timestart, timestop):
    time_vars = {
        "start": timestart,
        "stop": timestop
    }
    # /8 links
    query = """
        INSERT INTO {prefix}LinksOut (src_start, src_end, dst_start, dst_end, protocols, port, timestamp, links, bytes, packets)
        SELECT src DIV 16777216 * 16777216 AS 'src_start'
            , src DIV 16777216 * 16777216 + 16777215 AS 'src_end'
            , dst DIV 16777216 * 16777216 AS 'dst_start'
            , dst DIV 16777216 * 16777216 + 16777215 AS 'dst_end'
            , GROUP_CONCAT(DISTINCT protocol SEPARATOR ",")
            , port
            , timestamp
            , SUM(links)
            , SUM(bytes_sent + COALESCE(bytes_received, 0))
            , SUM(packets_sent + COALESCE(packets_received, 0))
        FROM {prefix}Links
        WHERE timestamp BETWEEN $start AND $stop
        GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp;
    """.format(prefix=prefix)
    db.query(query, vars=time_vars)

    # /16 links
    query = """
        INSERT INTO {prefix}LinksOut (src_start, src_end, dst_start, dst_end, protocols, port, timestamp, links, bytes, packets)
        SELECT src DIV 65536 * 65536 AS 'src_start'
            , src DIV 65536 * 65536 + 65535 AS 'src_end'
            , dst DIV 65536 * 65536 AS 'dst_start'
            , dst DIV 65536 * 65536 + 65535 AS 'dst_end'
            , GROUP_CONCAT(DISTINCT protocol SEPARATOR ",")
            , port
            , timestamp
            , SUM(links)
            , SUM(bytes_sent + COALESCE(bytes_received, 0))
            , SUM(packets_sent + COALESCE(packets_received, 0))
        FROM {prefix}Links
        WHERE (src DIV 16777216) = (dst DIV 16777216)
          AND timestamp BETWEEN $start AND $stop
        GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp
        UNION
        SELECT src DIV 65536 * 65536 AS 'src_start'
            , src DIV 65536 * 65536 + 65535 AS 'src_end'
            , dst DIV 16777216 * 16777216 AS 'dst_start'
            , dst DIV 16777216 * 16777216 + 16777215 AS 'dst_end'
            , GROUP_CONCAT(DISTINCT protocol SEPARATOR ",")
            , port
            , timestamp
            , SUM(links)
            , SUM(bytes_sent + COALESCE(bytes_received, 0))
            , SUM(packets_sent + COALESCE(packets_received, 0))
        FROM {prefix}Links
        WHERE (src DIV 16777216) != (dst DIV 16777216)
          AND timestamp BETWEEN $start AND $stop
        GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp;
    """.format(prefix=prefix)
    db.query(query, vars=time_vars)

    # /24 links
    query = """
        INSERT INTO {prefix}LinksOut (src_start, src_end, dst_start, dst_end, protocols, port, timestamp, links, bytes, packets)
        SELECT src DIV 256 * 256 AS 'src_start'
            , src DIV 256 * 256 + 255 AS 'src_end'
            , dst DIV 256 * 256 AS 'dst_start'
            , dst DIV 256 * 256 + 255 AS 'dst_end'
            , GROUP_CONCAT(DISTINCT protocol SEPARATOR ",")
            , port
            , timestamp
            , SUM(links)
            , SUM(bytes_sent + COALESCE(bytes_received, 0))
            , SUM(packets_sent + COALESCE(packets_received, 0))
        FROM {prefix}Links
        WHERE (src DIV 65536) = (dst DIV 65536)
          AND timestamp BETWEEN $start AND $stop
        GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp
        UNION
        SELECT src DIV 256 * 256 AS 'src_start'
            , src DIV 256 * 256 + 255 AS 'src_end'
            , dst DIV 65536 * 65536 AS 'dst_start'
            , dst DIV 65536 * 65536 + 65535 AS 'dst_end'
            , GROUP_CONCAT(DISTINCT protocol SEPARATOR ",")
            , port
            , timestamp
            , SUM(links)
            , SUM(bytes_sent + COALESCE(bytes_received, 0))
            , SUM(packets_sent + COALESCE(packets_received, 0))
        FROM {prefix}Links
        WHERE (src DIV 16777216) = (dst DIV 16777216)
          AND (src DIV 65536) != (dst DIV 65536)
          AND timestamp BETWEEN $start AND $stop
        GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp
        UNION
        SELECT src DIV 256 * 256 AS 'src_start'
            , src DIV 256 * 256 + 255 AS 'src_end'
            , dst DIV 16777216 * 16777216 AS 'dst_start'
            , dst DIV 16777216 * 16777216 + 16777215 AS 'dst_end'
            , GROUP_CONCAT(DISTINCT protocol SEPARATOR ",")
            , port
            , timestamp
            , SUM(links)
            , SUM(bytes_sent + COALESCE(bytes_received, 0))
            , SUM(packets_sent + COALESCE(packets_received, 0))
        FROM {prefix}Links
        WHERE (src DIV 16777216) != (dst DIV 16777216)
          AND timestamp BETWEEN $start AND $stop
        GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp;
    """.format(prefix=prefix)
    db.query(query, vars=time_vars)

    # /32 links
    query = """
        INSERT INTO {prefix}LinksOut (src_start, src_end, dst_start, dst_end, protocols, port, timestamp, links, bytes, packets)
        SELECT src AS 'src_start'
            , src AS 'src_end'
            , dst AS 'dst_start'
            , dst AS 'dst_end'
            , GROUP_CONCAT(DISTINCT protocol SEPARATOR ",")
            , port
            , timestamp
            , SUM(links)
            , SUM(bytes_sent + COALESCE(bytes_received, 0))
            , SUM(packets_sent + COALESCE(packets_received, 0))
        FROM {prefix}Links
        WHERE (src DIV 256) = (dst DIV 256)
          AND timestamp BETWEEN $start AND $stop
        GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp
        UNION
        SELECT src AS 'src_start'
            , src AS 'src_end'
            , dst DIV 256 * 256 AS 'dst_start'
            , dst DIV 256 * 256 + 255 AS 'dst_end'
            , GROUP_CONCAT(DISTINCT protocol SEPARATOR ",")
            , port
            , timestamp
            , SUM(links)
            , SUM(bytes_sent + COALESCE(bytes_received, 0))
            , SUM(packets_sent + COALESCE(packets_received, 0))
        FROM {prefix}Links
        WHERE (src DIV 65536) = (dst DIV 65536)
          AND (src DIV 256) != (dst DIV 256)
          AND timestamp BETWEEN $start AND $stop
        GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp
        UNION
        SELECT src AS 'src_start'
            , src AS 'src_end'
            , dst DIV 65536 * 65536 AS 'dst_start'
            , dst DIV 65536 * 65536 + 65535 AS 'dst_end'
            , GROUP_CONCAT(DISTINCT protocol SEPARATOR ",")
            , port
            , timestamp
            , SUM(links)
            , SUM(bytes_sent + COALESCE(bytes_received, 0))
            , SUM(packets_sent + COALESCE(packets_received, 0))
        FROM {prefix}Links
        WHERE (src DIV 16777216) = (dst DIV 16777216)
          AND (src DIV 65536) != (dst DIV 65536)
          AND timestamp BETWEEN $start AND $stop
        GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp
        UNION
        SELECT src AS 'src_start'
            , src AS 'src_end'
            , dst DIV 16777216 * 16777216 AS 'dst_start'
            , dst DIV 16777216 * 16777216 + 16777215 AS 'dst_end'
            , GROUP_CONCAT(DISTINCT protocol SEPARATOR ",")
            , port
            , timestamp
            , SUM(links)
            , SUM(bytes_sent + COALESCE(bytes_received, 0))
            , SUM(packets_sent + COALESCE(packets_received, 0))
        FROM {prefix}Links
        WHERE (src DIV 16777216) != (dst DIV 16777216)
          AND timestamp BETWEEN $start AND $stop
        GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp;
    """.format(prefix=prefix)
    db.query(query, vars=time_vars)


def copy_links_to_master(prefix):
    query = """
INSERT INTO {prefix}Links SELECT * FROM {prefix}staging_Links
  ON DUPLICATE KEY UPDATE
    `{prefix}Links`.duration=(`{prefix}Links`.duration*`{prefix}Links`.links+VALUES(links)*VALUES(duration)) / GREATEST(1, `{prefix}Links`.duration + VALUES(duration))
  , `{prefix}Links`.timestamp=VALUES(timestamp)
  , `{prefix}Links`.links=`{prefix}Links`.links+VALUES(links)
  , `{prefix}Links`.bytes_sent=`{prefix}Links`.bytes_sent+VALUES(bytes_sent)
  , `{prefix}Links`.bytes_received=`{prefix}Links`.bytes_received+VALUES(bytes_received)
  , `{prefix}Links`.packets_sent=`{prefix}Links`.packets_sent+VALUES(packets_sent)
  , `{prefix}Links`.packets_received=`{prefix}Links`.packets_received+VALUES(packets_received);
    """.format(prefix=prefix)
    db.query(query)


def delete_staging_data(prefix):
    dbaccess.exec_sql(db, "./sql/delete_staging_data.sql", {'prefix': prefix})


def preprocess_log(ds=None):
    print("Beginning preprocessing...")
    t = db.transaction()
    try:
        prefix = "ds_{0}_".format(ds)
        print("importing nodes...")
        import_nodes() # import all nodes into the shared Nodes table
        print("importing links...")
        build_Links(prefix) # import all link info into staging tables
        print("copying from staging to master...")
        copy_links_to_master(prefix) # copy data from staging to master tables
        print("precomputing aggregates...")
        build_link_aggregates(prefix)
        print("deleting from staging...")
        delete_staging_data(prefix) # delete all data from staging tables
    except:
        t.rollback()
        print("Pre-processing rolled back.")
        raise
    else:
        t.commit()
        print("Pre-processing completed successfully.")


# If running as a script
if __name__ == "__main__":
    test = integrity.check_and_fix_db_access()
    if test == 0:
        ds = determine_datasource(sys.argv)
        preprocess_log(ds=ds)
    else:
        print("Preprocess aborted. Database check failed.")

