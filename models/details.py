import web
import common
import models.links


class Details:
    def __init__(self, subscription, ds, address, timestamp_range=None, port=None, page_size=50):
        self.db = common.db
        self.sub = subscription
        self.table_nodes = "s{acct}_Nodes".format(acct=self.sub)
        self.table_links = "s{acct}_ds{id}_Links".format(acct=self.sub, id=ds)
        self.table_links_in = "s{acct}_ds{id}_LinksIn".format(acct=self.sub, id=ds)
        self.table_links_out = "s{acct}_ds{id}_LinksOut".format(acct=self.sub, id=ds)

        self.ds = ds
        self.ip_start, self.ip_end = common.determine_range_string(address)
        self.page_size = page_size
        self.port = port
        if timestamp_range:
            self.time_range = timestamp_range
        else:
            linksModel = models.links.Links(self.sub, self.ds)
            tr = linksModel.get_timerange()
            self.time_range = (tr['min'], tr['max'])

    def get_metadata(self):
        qvars = {"start": self.ip_start, "end": self.ip_end}
        # TODO: seconds has a magic number 300 added to account for DB time quantization.

        query = """
            SELECT CONCAT(decodeIP(n.ipstart), CONCAT('/', n.subnet)) AS 'address'
                , COALESCE(n.hostname, '') AS 'hostname'
                , COALESCE(l_out.unique_out_ip, 0) AS 'unique_out_ip'
                , COALESCE(l_out.unique_out_conn, 0) AS 'unique_out_conn'
                , COALESCE(l_out.total_out, 0) AS 'total_out'
                , COALESCE(l_out.b_s, 0) AS 'out_bytes_sent'
                , COALESCE(l_out.b_r, 0) AS 'out_bytes_received'
                , COALESCE(l_out.max_bps, 0) AS 'out_max_bps'
                , COALESCE(l_out.sum_b / l_out.sum_duration, 0) AS 'out_avg_bps'
                , COALESCE(l_out.p_s, 0) AS 'out_packets_sent'
                , COALESCE(l_out.p_r, 0) AS 'out_packets_received'
                , COALESCE(l_out.sum_duration / l_out.total_out, 0) AS 'out_duration'
                , COALESCE(l_in.unique_in_ip, 0) AS 'unique_in_ip'
                , COALESCE(l_in.unique_in_conn, 0) AS 'unique_in_conn'
                , COALESCE(l_in.total_in, 0) AS 'total_in'
                , COALESCE(l_in.b_s, 0) AS 'in_bytes_sent'
                , COALESCE(l_in.b_r, 0) AS 'in_bytes_received'
                , COALESCE(l_in.max_bps, 0) AS 'in_max_bps'
                , COALESCE(l_in.sum_b / l_in.sum_duration, 0) AS 'in_avg_bps'
                , COALESCE(l_in.p_s, 0) AS 'in_packets_sent'
                , COALESCE(l_in.p_r, 0) AS 'in_packets_received'
                , COALESCE(l_in.sum_duration / l_in.total_in, 0) AS 'in_duration'
                , COALESCE(l_in.ports_used, 0) AS 'ports_used'
                , children.endpoints AS 'endpoints'
                , COALESCE(t.seconds, 0) + 300 AS 'seconds'
                , (COALESCE(l_in.sum_b, 0) + COALESCE(l_out.sum_b, 0)) / (COALESCE(t.seconds, 0) + 300) AS 'overall_bps'
                , COALESCE(l_in.protocol, "") AS 'in_protocols'
                , COALESCE(l_out.protocol, "") AS 'out_protocols'
            FROM (
                SELECT ipstart, subnet, alias AS 'hostname'
                FROM {nodes_table}
                WHERE ipstart = $start AND ipend = $end
            ) AS n
            LEFT JOIN (
                SELECT $start AS 's1'
                , COUNT(DISTINCT dst) AS 'unique_out_ip'
                , COUNT(DISTINCT src, dst, port) AS 'unique_out_conn'
                , SUM(links) AS 'total_out'
                , SUM(bytes_sent) AS 'b_s'
                , SUM(bytes_received) AS 'b_r'
                , MAX((bytes_sent + bytes_received) / duration) AS 'max_bps'
                , SUM(bytes_sent + bytes_received) AS 'sum_b'
                , SUM(packets_sent) AS 'p_s'
                , SUM(packets_received) AS 'p_r'
                , SUM(duration * links) AS 'sum_duration'
                , GROUP_CONCAT(DISTINCT protocol SEPARATOR ",") AS 'protocol'
                FROM {links_table}
                WHERE src BETWEEN $start AND $end
                GROUP BY 's1'
            ) AS l_out
                ON n.ipstart = l_out.s1
            LEFT JOIN (
                SELECT $start AS 's1'
                , COUNT(DISTINCT src) AS 'unique_in_ip'
                , COUNT(DISTINCT src, dst, port) AS 'unique_in_conn'
                , SUM(links) AS 'total_in'
                , SUM(bytes_sent) AS 'b_s'
                , SUM(bytes_received) AS 'b_r'
                , MAX((bytes_sent + bytes_received) / duration) AS 'max_bps'
                , SUM(bytes_sent + bytes_received) AS 'sum_b'
                , SUM(packets_sent) AS 'p_s'
                , SUM(packets_received) AS 'p_r'
                , SUM(duration * links) AS 'sum_duration'
                , COUNT(DISTINCT port) AS 'ports_used'
                , GROUP_CONCAT(DISTINCT protocol SEPARATOR ",") AS 'protocol'
                FROM {links_table}
                WHERE dst BETWEEN $start AND $end
                GROUP BY 's1'
            ) AS l_in
                ON n.ipstart = l_in.s1
            LEFT JOIN (
                SELECT $start AS 's1'
                , COUNT(ipstart) AS 'endpoints'
                FROM {nodes_table}
                WHERE ipstart = ipend AND ipstart BETWEEN $start AND $end
            ) AS children
                ON n.ipstart = children.s1
            LEFT JOIN (
                SELECT $start AS 's1'
                    , (MAX(TIME_TO_SEC(timestamp)) - MIN(TIME_TO_SEC(timestamp))) AS 'seconds'
                FROM {links_table}
                GROUP BY 's1'
            ) AS t
                ON n.ipstart = t.s1
            LIMIT 1;
        """.format(nodes_table=self.table_nodes, links_table=self.table_links)
        results = self.db.query(query, vars=qvars)

        if len(results) == 1:
            return results[0]
        else:
            return {}

    @staticmethod
    def build_where_clause(timestamp_range=None, port=None, protocol=None, rounding=True):
        """
        Build a WHERE SQL clause that covers basic timerange, port, and protocol filtering.
        :param timestamp_range: start and end times as unix timestamps (integers). Default is all time.
        :type timestamp_range: tuple[int, int]
        :param port: exclusively report traffic destined for this port, if specified.
        :type port: int or str
        :param protocol: exclusively report traffic using this protocol
        :type protocol: str
        :param rounding: round each time stamp to the nearest quantization mark. (db records are quantized for consiceness)
        :type rounding: bool
        :return: String SQL clause
        :rtype: str
        """
        clauses = []
        t_start = 0
        t_end = 0

        if timestamp_range:
            t_start = timestamp_range[0]
            t_end = timestamp_range[1]
            if rounding:
                # rounding to 5 minutes, for use with the Syslog table
                if t_start > 150:
                    t_start -= 150
                if t_end <= 2 ** 31 - 150:
                    t_end += 149
            clauses.append("timestamp BETWEEN FROM_UNIXTIME($tstart) AND FROM_UNIXTIME($tend)")

        if port:
            clauses.append("port = $port")

        if protocol:
            clauses.append("protocols LIKE $protocol")
            protocol = "%{0}%".format(protocol)

        qvars = {'tstart': t_start, 'tend': t_end, 'port': port, 'protocol': protocol}
        where = str(web.db.reparam("\n    && ".join(clauses), qvars))
        if where:
            where = "    && " + where
        return where

    def get_details_connections(self, inbound, page=1, order="-links", simple=False):
        sort_options = ['links', 'src', 'dst', 'port', 'sum_bytes', 'sum_packets', 'protocols', 'avg_duration']
        sort_options_simple = ['links', 'src', 'dst', 'port']

        qvars = {
            'table_links': self.table_links,
            'start': self.ip_start,
            'end': self.ip_end,
            'page': self.page_size * (page - 1),
            'page_size': self.page_size,
            'WHERE': self.build_where_clause(self.time_range, self.port)
        }
        if inbound:
            qvars['collected'] = "src"
            qvars['filtered'] = "dst"
        else:
            qvars['filtered'] = "src"
            qvars['collected'] = "dst"

        # determine the sort direction
        if order and order[0] == '-':
            sort_dir = "DESC"
        else:
            sort_dir = "ASC"
        # determine the sort column
        if simple:
            if order and order[1:] in sort_options_simple:
                sort_by = order[1:]
            else:
                sort_by = sort_options_simple[0]
        else:
            if order and order[1:] in sort_options:
                sort_by = order[1:]
            else:
                sort_by = sort_options[0]
        # add table prefix for some columns
        if sort_by in ['port', 'src', 'dst']:
            sort_by = "`links`." + sort_by

        qvars['order'] = "{0} {1}".format(sort_by, sort_dir)

        if simple:
            query = """
    SELECT decodeIP({collected}) AS '{collected}'
        , port AS 'port'
        , sum(links) AS 'links'
    FROM {table_links} AS `links`
    WHERE {filtered} BETWEEN $start AND $end
     {WHERE}
    GROUP BY `links`.{collected}, `links`.port
    ORDER BY {order}
    LIMIT {page}, {page_size}
            """.format(**qvars)
        else:
            query = """
    SELECT src, dst, port, links, protocols
        , sum_bytes
        , (sum_bytes / links) AS 'avg_bytes'
        , sum_packets
        , (sum_packets / links) AS 'avg_packets'
        , (_duration / links) AS 'avg_duration'
    FROM(
        SELECT decodeIP(src) AS 'src'
            , decodeIP(dst) AS 'dst'
            , port AS 'port'
            , sum(links) AS 'links'
            , GROUP_CONCAT(DISTINCT protocol SEPARATOR ", ") AS 'protocols'
            , SUM(bytes_sent + COALESCE(bytes_received, 0)) AS 'sum_bytes'
            , SUM(packets_sent + COALESCE(packets_received, 0)) AS 'sum_packets'
            , SUM(duration*links) AS '_duration'
        FROM {table_links} AS `links`
        WHERE {filtered} BETWEEN $start AND $end
         {WHERE}
        GROUP BY `links`.src, `links`.dst, `links`.port
        ORDER BY {order}
        LIMIT {page}, {page_size}
    ) AS precalc;
            """.format(**qvars)
        return list(self.db.query(query, vars=qvars))

    def get_details_ports(self, page=1, order="-links"):
        sort_options = ['links', 'port']
        first_result = (page - 1) * self.page_size

        qvars = {
            'links_table': self.table_links,
            'start': self.ip_start,
            'end': self.ip_end,
            'first': first_result,
            'size': self.page_size,
            'WHERE': self.build_where_clause(self.time_range, self.port),
        }

        if order and order[0] == '-':
            sort_dir = "DESC"
        else:
            sort_dir = "ASC"
        if order and order[1:] in sort_options:
            sort_by = order[1:]
        else:
            sort_by = sort_options[0]
        qvars['order'] = "{0} {1}".format(sort_by, sort_dir)

        query = """
            SELECT port AS 'port', sum(links) AS 'links'
            FROM {links_table}
            WHERE dst BETWEEN $start AND $end
             {WHERE}
            GROUP BY port
            ORDER BY {order}
            LIMIT $first, $size;
        """.format(**qvars)
        return list(common.db.query(query, vars=qvars))

    def get_details_children(self, page=1, order='+ipstart'):
        sort_options = ['ipstart', 'hostname', 'endpoints', 'ratio']

        ip_diff = self.ip_end - self.ip_start
        if ip_diff == 0:
            return []
        elif ip_diff == 255:
            quotient = 1
            child_subnet_start = 25
            child_subnet_end = 32
        elif ip_diff == 65535:
            quotient = 256
            child_subnet_start = 17
            child_subnet_end = 24
        elif ip_diff == 16777215:
            quotient = 65536
            child_subnet_start = 9
            child_subnet_end = 16
        else:
            quotient = 16777216
            child_subnet_start = 1
            child_subnet_end = 8
        first_result = (page - 1) * self.page_size
        qvars = {'ip_start': self.ip_start,
                 'ip_end': self.ip_end,
                 's_start': child_subnet_start,
                 's_end': child_subnet_end,
                 'first': first_result,
                 'size': self.page_size,
                 'quot': quotient,
                 'quot_1': quotient - 1}

        if order and order[0] == '-':
            sort_dir = "DESC"
        else:
            sort_dir = "ASC"
        if order and order[1:] in sort_options:
            sort_by = order[1:]
        else:
            sort_by = sort_options[0]
        qvars['order'] = "{0} {1}".format(sort_by, sort_dir)

        query = """
        SELECT decodeIP(`n`.ipstart) AS 'address'
          , COALESCE(`n`.alias, '') AS 'hostname'
          , `n`.subnet AS 'subnet'
          , `sn`.kids AS 'endpoints'
          , COALESCE(COALESCE(`l_in`.links,0) / (COALESCE(`l_in`.links,0) + COALESCE(`l_out`.links,0)), 0) AS 'ratio'
        FROM {nodes_table} AS `n`
        LEFT JOIN (
            SELECT dst_start DIV $quot * $quot AS 'low'
                , dst_end DIV $quot * $quot + $quot_1 AS 'high'
                , sum(links) AS 'links'
            FROM {links_in_table}
            GROUP BY low, high
            ) AS `l_in`
        ON `l_in`.low = `n`.ipstart AND `l_in`.high = `n`.ipend
        LEFT JOIN (
            SELECT src_start DIV $quot * $quot AS 'low'
                , src_end DIV $quot * $quot + $quot_1 AS 'high'
                , sum(links) AS 'links'
            FROM {links_out_table}
            GROUP BY low, high
            ) AS `l_out`
        ON `l_out`.low = `n`.ipstart AND `l_out`.high = `n`.ipend
        LEFT JOIN (
            SELECT ipstart DIV $quot * $quot AS 'low'
                , ipend DIV $quot * $quot + $quot_1 AS 'high'
                , COUNT(ipstart) AS 'kids'
            FROM {nodes_table}
            WHERE ipstart = ipend
            GROUP BY low, high
            ) AS `sn`
        ON `sn`.low = `n`.ipstart AND `sn`.high = `n`.ipend
        WHERE `n`.ipstart BETWEEN $ip_start AND $ip_end
            AND `n`.subnet BETWEEN $s_start AND $s_end
        ORDER BY {order}
        LIMIT $first, $size;
        """.format(order=qvars['order'],
                   nodes_table=self.table_nodes,
                   links_in_table=self.table_links_in,
                   links_out_table=self.table_links_out)
        return list(common.db.query(query, vars=qvars))

    def get_details_summary(self):
        where = self.build_where_clause(timestamp_range=self.time_range, port=self.port)

        # TODO: seconds has a magic number 300 added to account for DB time quantization.
        query = """
        SELECT `inputs`.ips AS 'unique_in'
            , `outputs`.ips AS 'unique_out'
            , `inputs`.ports AS 'unique_ports'
        FROM
          (SELECT COUNT(DISTINCT src) AS 'ips', COUNT(DISTINCT port) AS 'ports'
            FROM {links_table}
            WHERE dst BETWEEN $start AND $end
             {where}
        ) AS `inputs`
        JOIN (SELECT COUNT(DISTINCT dst) AS 'ips'
            FROM {links_table}
            WHERE src BETWEEN $start AND $end
             {where}
        ) AS `outputs`;""".format(where=where, links_table=self.table_links)

        qvars = {'start': self.ip_start, 'end': self.ip_end}
        rows = common.db.query(query, vars=qvars)
        return rows.first()
