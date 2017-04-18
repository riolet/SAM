"""
Preprocess the data in the database's upload table Syslog
"""
import os
import sys
from sam import constants
from sam import common
from sam import integrity
from sam.models.datasources import Datasources


class InvalidDatasource(ValueError):
    pass


def determine_datasource(db, sub, argv):
    ds_model = Datasources(db, {}, sub)
    ds_id = None
    if len(argv) >= 2:
        requested_ds = argv[1]
        for datasource in ds_model.datasources.values():
            if datasource['name'] == requested_ds:
                ds_id = datasource['id']
                break
            if str(datasource['id']) == requested_ds:
                ds_id = datasource['id']
                break

    if ds_id is not None:
        return ds_id
    else:
        raise InvalidDatasource


class Preprocessor:
    def __init__(self, database, subscription, datasource):
        self.db = database
        self.sub_id = subscription
        self.ds_id = datasource
        self.whois_thread = None
        if self.db.dbname == 'mysql':
            self.divop = 'DIV'
            self.timeround = 'SUBSTRING(TIMESTAMPADD(MINUTE, -(MINUTE(Timestamp) % 5), Timestamp), 1, 16)'
        else:
            self.divop = '/'
            self.timeround = "(strftime('%s', timestamp, 'utc') - (strftime('%s', timestamp, 'utc') % 300))"

        self.tables = {
            'table_nodes': 's{acct}_Nodes'.format(acct=self.sub_id),
            'table_syslog': 's{acct}_ds{id}_Syslog'.format(acct=self.sub_id, id=self.ds_id),
            'table_staging_links': 's{acct}_ds{id}_StagingLinks'.format(acct=self.sub_id, id=self.ds_id),
            'table_links': 's{acct}_ds{id}_Links'.format(acct=self.sub_id, id=self.ds_id),
            'table_links_in': 's{acct}_ds{id}_LinksIn'.format(acct=self.sub_id, id=self.ds_id),
            'table_links_out': 's{acct}_ds{id}_LinksOut'.format(acct=self.sub_id, id=self.ds_id)
        } 

    def count_syslog(self):
        rows = self.db.select(self.tables['table_syslog'], what="COUNT(1) AS 'cnt'")
        row = rows.first()
        return row.cnt

    def syslog_to_nodes(self):
        # Get all /8 nodes. Load them into Nodes8
        query = """
                INSERT INTO {table_nodes} (ipstart, ipend, subnet, x, y, radius)
                SELECT (log.ip * 16777216) AS 'ipstart'
                    , ((log.ip + 1) * 16777216 - 1) AS 'ipend'
                    , 8 AS 'subnet'
                    , (331776 * (log.ip % 16) / 7.5 - 331776) AS 'x'
                    , (331776 * (log.ip {div} 16) / 7.5 - 331776) AS 'y'
                    , 20736 AS 'radius'
                FROM(
                    SELECT src {div} 16777216 AS 'ip'
                    FROM {table_syslog}
                    UNION
                    SELECT dst {div} 16777216 AS 'ip'
                    FROM {table_syslog}
                ) AS log
                LEFT JOIN {table_nodes} AS `filter`
                    ON (log.ip * 16777216) = `filter`.ipstart AND ((log.ip + 1) * 16777216 - 1) = `filter`.ipend
                WHERE filter.ipstart IS NULL;
            """.format(div=self.divop, **self.tables)
        qvars = {"radius": 331776}
        self.db.query(query, vars=qvars)

        # Get all the /16 nodes. Load these into Nodes16
        query = """
                INSERT INTO {table_nodes} (ipstart, ipend, subnet, x, y, radius)
                SELECT (log.ip * 65536) AS 'ipstart'
                    , ((log.ip + 1) * 65536 - 1) AS 'ipend'
                    , 16 AS 'subnet'
                    , ((parent.radius * (log.ip % 16) / 7.5 - parent.radius) + parent.x) AS 'x'
                    , ((parent.radius * (log.ip % 256 {div} 16) / 7.5 - parent.radius) + parent.y) AS 'y'
                    , (parent.radius / 24) AS 'radius'
                FROM(
                    SELECT src {div} 65536 AS 'ip'
                    FROM {table_syslog}
                    UNION
                    SELECT dst {div} 65536 AS 'ip'
                    FROM {table_syslog}
                ) AS log
                JOIN {table_nodes} AS parent
                    ON parent.subnet=8 AND parent.ipstart = (log.ip {div} 256 * 16777216)
                LEFT JOIN {table_nodes} AS `filter`
                    ON (log.ip * 65536) = `filter`.ipstart AND ((log.ip + 1) * 65536 - 1) = `filter`.ipend
                WHERE filter.ipstart IS NULL;
                """.format(div=self.divop, **self.tables)
        self.db.query(query)

        # Get all the /24 nodes. Load these into Nodes24
        query = """
                INSERT INTO {table_nodes} (ipstart, ipend, subnet, x, y, radius)
                SELECT (log.ip * 256) AS 'ipstart'
                    , ((log.ip + 1) * 256 - 1) AS 'ipend'
                    , 24 AS 'subnet'
                    , ((parent.radius * (log.ip % 16) / 7.5 - parent.radius) + parent.x) AS 'x'
                    , ((parent.radius * (log.ip % 256 {div} 16) / 7.5 - parent.radius) + parent.y) AS 'y'
                    , (parent.radius {div} 24) AS 'radius'
                FROM(
                    SELECT src {div} 256 AS 'ip'
                    FROM {table_syslog}
                    UNION
                    SELECT dst {div} 256 AS 'ip'
                    FROM {table_syslog}
                ) AS log
                JOIN {table_nodes} AS parent
                    ON parent.subnet=16 AND parent.ipstart = (log.ip {div} 256 * 65536)
                LEFT JOIN {table_nodes} AS `filter`
                    ON (log.ip * 256) = `filter`.ipstart AND ((log.ip + 1) * 256 - 1) = `filter`.ipend
                WHERE filter.ipstart IS NULL;
                """.format(div=self.divop, **self.tables)
        self.db.query(query)

        # Get all the /32 nodes. Load these into Nodes32
        query = """
                INSERT INTO {table_nodes} (ipstart, ipend, subnet, x, y, radius)
                SELECT log.ip AS 'ipstart'
                    , log.ip AS 'ipend'
                    , 32 AS 'subnet'
                    , ((parent.radius * (log.ip % 16) / 7.5 - parent.radius) + parent.x) AS 'x'
                    , ((parent.radius * (log.ip % 256 {div} 16) / 7.5 - parent.radius) + parent.y) AS 'y'
                    , (parent.radius / 24) AS 'radius'
                FROM(
                    SELECT src AS 'ip'
                    FROM {table_syslog}
                    UNION
                    SELECT dst AS 'ip'
                    FROM {table_syslog}
                ) AS log
                JOIN {table_nodes} AS parent
                    ON parent.subnet=24 AND parent.ipstart = (log.ip {div} 256 * 256)
                LEFT JOIN {table_nodes} AS `filter`
                    ON log.ip = `filter`.ipstart AND log.ip = `filter`.ipend
                WHERE filter.ipstart IS NULL;
                """.format(div=self.divop, **self.tables)
        self.db.query(query)

    def syslog_to_staging_links(self):
        query = """
            INSERT INTO {table_staging_links} (src, dst, port, protocol, timestamp,
                links, bytes_sent, bytes_received, packets_sent, packets_received, duration)
            SELECT src
                , dst
                , dstport
                , protocol
                , {timeround} AS ts
                , COUNT(1) AS links
                , SUM(bytes_sent) AS 'bytes_sent'
                , SUM(bytes_received) AS 'bytes_received'
                , SUM(packets_sent) AS 'packets_sent'
                , SUM(packets_received) AS 'packets_received'
                , AVG(duration) AS 'duration'
            FROM {table_syslog}
            GROUP BY src, dst, dstport, protocol, ts;
        """.format(div=self.divop, timeround=self.timeround, **self.tables)
        self.db.query(query)

    def staging_links_to_links(self):
        query = """
        REPLACE INTO {table_links} (src, dst, port, protocol, timestamp, links, bytes_sent, bytes_received, packets_sent, packets_received, duration)
        SELECT `SL`.src, `SL`.dst, `SL`.port, `SL`.protocol, `SL`.timestamp
            , `SL`.links + COALESCE(`L`.links, 0) AS 'links'
            , `SL`.bytes_sent + COALESCE(`L`.bytes_sent, 0) AS 'bytesIn'
            , `SL`.bytes_received + COALESCE(`L`.bytes_received, 0) AS 'bytesOut'
            , `SL`.packets_sent + COALESCE(`L`.packets_sent, 0) AS 'packetsIn'
            , `SL`.packets_received + COALESCE(`L`.packets_received, 0) AS 'packetsOut'
            , (`SL`.duration * `SL`.links + COALESCE(`L`.duration * `L`.links, 0)) / (COALESCE(`L`.links, 0) + `SL`.links) AS 'durationAvg'
        FROM {table_staging_links} AS `SL`
        LEFT JOIN {table_links} AS `L`
        ON `L`.src = `SL`.src
         AND `L`.dst = `SL`.dst
         AND `L`.port = `SL`.port
         AND `L`.protocol = `SL`.protocol
         AND `L`.timestamp = `SL`.timestamp;
        """.format(**self.tables)
        self.db.query(query)

    def links_to_links_in_out(self):
        rows = self.db.select(self.tables['table_staging_links'], what="MIN(timestamp) AS 'start', MAX(timestamp) AS 'end'")
        timerange = rows[0]

        self.db.delete(self.tables['table_links_in'], where="timestamp BETWEEN $start AND $end", vars=timerange)
        self.db.delete(self.tables['table_links_out'], where="timestamp BETWEEN $start AND $end", vars=timerange)
        self.links_to_links_in(timerange.start, timerange.end)
        self.links_to_links_out(timerange.start, timerange.end)

    def links_to_links_in(self, timestart, timestop):
        time_vars = {
            "start": timestart,
            "stop": timestop
        }

        # /8 links
        query = """
            INSERT INTO {table_links_in} (src_start, src_end, dst_start, dst_end, protocols, port, timestamp, links, bytes, packets)
            SELECT src {div} 16777216 * 16777216 AS 'src_start'
                , src {div} 16777216 * 16777216 + 16777215 AS 'src_end'
                , dst {div} 16777216 * 16777216 AS 'dst_start'
                , dst {div} 16777216 * 16777216 + 16777215 AS 'dst_end'
                , GROUP_CONCAT(DISTINCT protocol)
                , port
                , timestamp
                , SUM(links)
                , SUM(bytes_sent + COALESCE(bytes_received, 0))
                , SUM(packets_sent + COALESCE(packets_received, 0))
            FROM {table_links}
            WHERE timestamp BETWEEN $start AND $stop
            GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp;
        """.format(div=self.divop, **self.tables)
        self.db.query(query, vars=time_vars)

        # /16 links
        query = """
            INSERT INTO {table_links_in} (src_start, src_end, dst_start, dst_end, protocols, port, timestamp, links, bytes, packets)
            SELECT src {div} 65536 * 65536 AS 'src_start'
                , src {div} 65536 * 65536 + 65535 AS 'src_end'
                , dst {div} 65536 * 65536 AS 'dst_start'
                , dst {div} 65536 * 65536 + 65535 AS 'dst_end'
                , GROUP_CONCAT(DISTINCT protocol)
                , port
                , timestamp
                , SUM(links)
                , SUM(bytes_sent + COALESCE(bytes_received, 0))
                , SUM(packets_sent + COALESCE(packets_received, 0))
            FROM {table_links}
            WHERE (src {div} 16777216) = (dst {div} 16777216)
              AND timestamp BETWEEN $start AND $stop
            GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp
            UNION
            SELECT src {div} 16777216 * 16777216 AS 'src_start'
                , src {div} 16777216 * 16777216 + 16777215 AS 'src_end'
                , dst {div} 65536 * 65536 AS 'dst_start'
                , dst {div} 65536 * 65536 + 65535 AS 'dst_end'
                , GROUP_CONCAT(DISTINCT protocol)
                , port
                , timestamp
                , SUM(links)
                , SUM(bytes_sent + COALESCE(bytes_received, 0))
                , SUM(packets_sent + COALESCE(packets_received, 0))
            FROM {table_links}
            WHERE (src {div} 16777216) != (dst {div} 16777216)
              AND timestamp BETWEEN $start AND $stop
            GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp;
        """.format(div=self.divop, **self.tables)
        self.db.query(query, vars=time_vars)

        # /24 links
        query = """
            INSERT INTO {table_links_in} (src_start, src_end, dst_start, dst_end, protocols, port, timestamp, links, bytes, packets)
            SELECT src {div} 256 * 256 AS 'src_start'
                , src {div} 256 * 256 + 255 AS 'src_end'
                , dst {div} 256 * 256 AS 'dst_start'
                , dst {div} 256 * 256 + 255 AS 'dst_end'
                , GROUP_CONCAT(DISTINCT protocol)
                , port
                , timestamp
                , SUM(links)
                , SUM(bytes_sent + COALESCE(bytes_received, 0))
                , SUM(packets_sent + COALESCE(packets_received, 0))
            FROM {table_links}
            WHERE (src {div} 65536) = (dst {div} 65536)
              AND timestamp BETWEEN $start AND $stop
            GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp
            UNION
            SELECT src {div} 65536 * 65536 AS 'src_start'
                , src {div} 65536 * 65536 + 65535 AS 'src_end'
                , dst {div} 256 * 256 AS 'dst_start'
                , dst {div} 256 * 256 + 255 AS 'dst_end'
                , GROUP_CONCAT(DISTINCT protocol)
                , port
                , timestamp
                , SUM(links)
                , SUM(bytes_sent + COALESCE(bytes_received, 0))
                , SUM(packets_sent + COALESCE(packets_received, 0))
            FROM {table_links}
            WHERE (src {div} 16777216) = (dst {div} 16777216)
              AND (src {div} 65536) != (dst {div} 65536)
              AND timestamp BETWEEN $start AND $stop
            GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp
            UNION
            SELECT src {div} 16777216 * 16777216 AS 'src_start'
                , src {div} 16777216 * 16777216 + 16777215 AS 'src_end'
                , dst {div} 256 * 256 AS 'dst_start'
                , dst {div} 256 * 256 + 255 AS 'dst_end'
                , GROUP_CONCAT(DISTINCT protocol)
                , port
                , timestamp
                , SUM(links)
                , SUM(bytes_sent + COALESCE(bytes_received, 0))
                , SUM(packets_sent + COALESCE(packets_received, 0))
            FROM {table_links}
            WHERE (src {div} 16777216) != (dst {div} 16777216)
              AND timestamp BETWEEN $start AND $stop
            GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp;
        """.format(div=self.divop, **self.tables)
        self.db.query(query, vars=time_vars)

        # /32 links
        query = """
            INSERT INTO {table_links_in} (src_start, src_end, dst_start, dst_end, protocols, port, timestamp, links, bytes, packets)
            SELECT src AS 'src_start'
                , src AS 'src_end'
                , dst AS 'dst_start'
                , dst AS 'dst_end'
                , GROUP_CONCAT(DISTINCT protocol)
                , port
                , timestamp
                , SUM(links)
                , SUM(bytes_sent + COALESCE(bytes_received, 0))
                , SUM(packets_sent + COALESCE(packets_received, 0))
            FROM {table_links}
            WHERE (src {div} 256) = (dst {div} 256)
              AND timestamp BETWEEN $start AND $stop
            GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp
            UNION
            SELECT src {div} 256 * 256 AS 'src_start'
                , src {div} 256 * 256 + 255 AS 'src_end'
                , dst AS 'dst_start'
                , dst AS 'dst_end'
                , GROUP_CONCAT(DISTINCT protocol)
                , port
                , timestamp
                , SUM(links)
                , SUM(bytes_sent + COALESCE(bytes_received, 0))
                , SUM(packets_sent + COALESCE(packets_received, 0))
            FROM {table_links}
            WHERE (src {div} 65536) = (dst {div} 65536)
              AND (src {div} 256) != (dst {div} 256)
              AND timestamp BETWEEN $start AND $stop
            GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp
            UNION
            SELECT src {div} 65536 * 65536 AS 'src_start'
                , src {div} 65536 * 65536 + 65535 AS 'src_end'
                , dst AS 'dst_start'
                , dst AS 'dst_end'
                , GROUP_CONCAT(DISTINCT protocol)
                , port
                , timestamp
                , SUM(links)
                , SUM(bytes_sent + COALESCE(bytes_received, 0))
                , SUM(packets_sent + COALESCE(packets_received, 0))
            FROM {table_links}
            WHERE (src {div} 16777216) = (dst {div} 16777216)
              AND (src {div} 65536) != (dst {div} 65536)
              AND timestamp BETWEEN $start AND $stop
            GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp
            UNION
            SELECT src {div} 16777216 * 16777216 AS 'src_start'
                , src {div} 16777216 * 16777216 + 16777215 AS 'src_end'
                , dst AS 'dst_start'
                , dst AS 'dst_end'
                , GROUP_CONCAT(DISTINCT protocol)
                , port
                , timestamp
                , SUM(links)
                , SUM(bytes_sent + COALESCE(bytes_received, 0))
                , SUM(packets_sent + COALESCE(packets_received, 0))
            FROM {table_links}
            WHERE (src {div} 16777216) != (dst {div} 16777216)
              AND timestamp BETWEEN $start AND $stop
            GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp;
        """.format(div=self.divop, **self.tables)
        self.db.query(query, vars=time_vars)

    def links_to_links_out(self, timestart, timestop):
        time_vars = {
            "start": timestart,
            "stop": timestop
        }
        # /8 links
        query = """
            INSERT INTO {table_links_out} (src_start, src_end, dst_start, dst_end, protocols, port, timestamp, links, bytes, packets)
            SELECT src {div} 16777216 * 16777216 AS 'src_start'
                , src {div} 16777216 * 16777216 + 16777215 AS 'src_end'
                , dst {div} 16777216 * 16777216 AS 'dst_start'
                , dst {div} 16777216 * 16777216 + 16777215 AS 'dst_end'
                , GROUP_CONCAT(DISTINCT protocol)
                , port
                , timestamp
                , SUM(links)
                , SUM(bytes_sent + COALESCE(bytes_received, 0))
                , SUM(packets_sent + COALESCE(packets_received, 0))
            FROM {table_links}
            WHERE timestamp BETWEEN $start AND $stop
            GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp;
        """.format(div=self.divop, **self.tables)
        self.db.query(query, vars=time_vars)

        # /16 links
        query = """
            INSERT INTO {table_links_out} (src_start, src_end, dst_start, dst_end, protocols, port, timestamp, links, bytes, packets)
            SELECT src {div} 65536 * 65536 AS 'src_start'
                , src {div} 65536 * 65536 + 65535 AS 'src_end'
                , dst {div} 65536 * 65536 AS 'dst_start'
                , dst {div} 65536 * 65536 + 65535 AS 'dst_end'
                , GROUP_CONCAT(DISTINCT protocol)
                , port
                , timestamp
                , SUM(links)
                , SUM(bytes_sent + COALESCE(bytes_received, 0))
                , SUM(packets_sent + COALESCE(packets_received, 0))
            FROM {table_links}
            WHERE (src {div} 16777216) = (dst {div} 16777216)
              AND timestamp BETWEEN $start AND $stop
            GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp
            UNION
            SELECT src {div} 65536 * 65536 AS 'src_start'
                , src {div} 65536 * 65536 + 65535 AS 'src_end'
                , dst {div} 16777216 * 16777216 AS 'dst_start'
                , dst {div} 16777216 * 16777216 + 16777215 AS 'dst_end'
                , GROUP_CONCAT(DISTINCT protocol)
                , port
                , timestamp
                , SUM(links)
                , SUM(bytes_sent + COALESCE(bytes_received, 0))
                , SUM(packets_sent + COALESCE(packets_received, 0))
            FROM {table_links}
            WHERE (src {div} 16777216) != (dst {div} 16777216)
              AND timestamp BETWEEN $start AND $stop
            GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp;
        """.format(div=self.divop, **self.tables)
        self.db.query(query, vars=time_vars)

        # /24 links
        query = """
            INSERT INTO {table_links_out} (src_start, src_end, dst_start, dst_end, protocols, port, timestamp, links, bytes, packets)
            SELECT src {div} 256 * 256 AS 'src_start'
                , src {div} 256 * 256 + 255 AS 'src_end'
                , dst {div} 256 * 256 AS 'dst_start'
                , dst {div} 256 * 256 + 255 AS 'dst_end'
                , GROUP_CONCAT(DISTINCT protocol)
                , port
                , timestamp
                , SUM(links)
                , SUM(bytes_sent + COALESCE(bytes_received, 0))
                , SUM(packets_sent + COALESCE(packets_received, 0))
            FROM {table_links}
            WHERE (src {div} 65536) = (dst {div} 65536)
              AND timestamp BETWEEN $start AND $stop
            GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp
            UNION
            SELECT src {div} 256 * 256 AS 'src_start'
                , src {div} 256 * 256 + 255 AS 'src_end'
                , dst {div} 65536 * 65536 AS 'dst_start'
                , dst {div} 65536 * 65536 + 65535 AS 'dst_end'
                , GROUP_CONCAT(DISTINCT protocol)
                , port
                , timestamp
                , SUM(links)
                , SUM(bytes_sent + COALESCE(bytes_received, 0))
                , SUM(packets_sent + COALESCE(packets_received, 0))
            FROM {table_links}
            WHERE (src {div} 16777216) = (dst {div} 16777216)
              AND (src {div} 65536) != (dst {div} 65536)
              AND timestamp BETWEEN $start AND $stop
            GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp
            UNION
            SELECT src {div} 256 * 256 AS 'src_start'
                , src {div} 256 * 256 + 255 AS 'src_end'
                , dst {div} 16777216 * 16777216 AS 'dst_start'
                , dst {div} 16777216 * 16777216 + 16777215 AS 'dst_end'
                , GROUP_CONCAT(DISTINCT protocol)
                , port
                , timestamp
                , SUM(links)
                , SUM(bytes_sent + COALESCE(bytes_received, 0))
                , SUM(packets_sent + COALESCE(packets_received, 0))
            FROM {table_links}
            WHERE (src {div} 16777216) != (dst {div} 16777216)
              AND timestamp BETWEEN $start AND $stop
            GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp;
        """.format(div=self.divop, **self.tables)
        self.db.query(query, vars=time_vars)

        # /32 links
        query = """
            INSERT INTO {table_links_out} (src_start, src_end, dst_start, dst_end, protocols, port, timestamp, links, bytes, packets)
            SELECT src AS 'src_start'
                , src AS 'src_end'
                , dst AS 'dst_start'
                , dst AS 'dst_end'
                , GROUP_CONCAT(DISTINCT protocol)
                , port
                , timestamp
                , SUM(links)
                , SUM(bytes_sent + COALESCE(bytes_received, 0))
                , SUM(packets_sent + COALESCE(packets_received, 0))
            FROM {table_links}
            WHERE (src {div} 256) = (dst {div} 256)
              AND timestamp BETWEEN $start AND $stop
            GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp
            UNION
            SELECT src AS 'src_start'
                , src AS 'src_end'
                , dst {div} 256 * 256 AS 'dst_start'
                , dst {div} 256 * 256 + 255 AS 'dst_end'
                , GROUP_CONCAT(DISTINCT protocol)
                , port
                , timestamp
                , SUM(links)
                , SUM(bytes_sent + COALESCE(bytes_received, 0))
                , SUM(packets_sent + COALESCE(packets_received, 0))
            FROM {table_links}
            WHERE (src {div} 65536) = (dst {div} 65536)
              AND (src {div} 256) != (dst {div} 256)
              AND timestamp BETWEEN $start AND $stop
            GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp
            UNION
            SELECT src AS 'src_start'
                , src AS 'src_end'
                , dst {div} 65536 * 65536 AS 'dst_start'
                , dst {div} 65536 * 65536 + 65535 AS 'dst_end'
                , GROUP_CONCAT(DISTINCT protocol)
                , port
                , timestamp
                , SUM(links)
                , SUM(bytes_sent + COALESCE(bytes_received, 0))
                , SUM(packets_sent + COALESCE(packets_received, 0))
            FROM {table_links}
            WHERE (src {div} 16777216) = (dst {div} 16777216)
              AND (src {div} 65536) != (dst {div} 65536)
              AND timestamp BETWEEN $start AND $stop
            GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp
            UNION
            SELECT src AS 'src_start'
                , src AS 'src_end'
                , dst {div} 16777216 * 16777216 AS 'dst_start'
                , dst {div} 16777216 * 16777216 + 16777215 AS 'dst_end'
                , GROUP_CONCAT(DISTINCT protocol)
                , port
                , timestamp
                , SUM(links)
                , SUM(bytes_sent + COALESCE(bytes_received, 0))
                , SUM(packets_sent + COALESCE(packets_received, 0))
            FROM {table_links}
            WHERE (src {div} 16777216) != (dst {div} 16777216)
              AND timestamp BETWEEN $start AND $stop
            GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp;
        """.format(div=self.divop, **self.tables)
        self.db.query(query, vars=time_vars)

    def staging_to_null(self):
        replacements = {
            'acct': self.sub_id,
            'id': self.ds_id
        }
        common.exec_sql(self.db, os.path.join(constants.base_path, "sql", "delete_staging_data.sql"), replacements)

    def run_all(self):
        print("PREPROCESSOR: beginning preprocessing...")
        db_transaction = self.db.transaction()
        try:
            print("PREPROCESSOR: importing nodes...")
            self.syslog_to_nodes()  # import all nodes into the shared Nodes table
            print("PREPROCESSOR: importing links...")
            self.syslog_to_staging_links()  # import all link info into staging tables
            print("PREPROCESSOR: copying from staging to master...")
            self.staging_links_to_links()  # copy data from staging to master tables
            print("PREPROCESSOR: precomputing aggregates...")
            self.links_to_links_in_out()  # merge new data into the existing aggregates
            print("PREPROCESSOR: deleting from staging...")
            self.staging_to_null()  # delete all data from staging tables
        except:
            db_transaction.rollback()
            print("PREPROCESSOR: Pre-processing rolled back.")
            raise
        else:
            db_transaction.commit()
            print("PREPROCESSOR: Pre-processing completed successfully.")

# If running as a script
if __name__ == "__main__":
    error_number = integrity.check_and_fix_db_access(constants.dbconfig)
    if error_number == 0:
        sub_id = constants.demo['id']
        try:
            ds = determine_datasource(common.db_quiet, sub_id, sys.argv)
            processor = Preprocessor(common.db_quiet, sub_id, ds)
            processor.run_all()
        except InvalidDatasource:
            print("PREPROCESSOR: Data source missing or invalid. Aborting.")
            print("PREPROCESSOR: please run as \n\t`python {0} <datasource>`".format(sys.argv[0]))
    else:
        print("PREPROCESSOR: Preprocess aborted. Database check failed.")
