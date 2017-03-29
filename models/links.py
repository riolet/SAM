import time
from datetime import datetime
import web
import common


class Links:
    def __init__(self, subscription, ds):
        self.db = common.db
        self.sub = subscription
        self.ds = ds
        self.table_links = "s{acct}_ds{id}_Links".format(acct=self.sub, id=self.ds)
        self.table_links_in = "s{acct}_ds{id}_LinksIn".format(acct=self.sub, id=self.ds)
        self.table_links_out = "s{acct}_ds{id}_LinksOut".format(acct=self.sub, id=self.ds)

    def delete_connections(self):
        self.db.delete(self.table_links, "1")
        self.db.delete(self.table_links_in, "1")
        self.db.delete(self.table_links_out, "1")

    def get_protocol_list(self):
        rows = common.db.select(self.table_links, what="DISTINCT protocol")
        return [row.protocol for row in rows if row.protocol]

    def get_timerange(self):
        rows = common.db.query("SELECT MIN(timestamp) AS 'min', MAX(timestamp) AS 'max' "
                               "FROM {table_links};".format(table_links=self.table_links))
        row = rows[0]
        if row['min'] is None or row['max'] is None:
            now = time.mktime(datetime.now().timetuple())
            return {'min': now, 'max': now}
        return {'min': int(time.mktime(row['min'].timetuple())), 'max': int(time.mktime(row['max'].timetuple()))}

    def get_links(self, addresses, timerange, port, protocol):
        result = {}
        for address in addresses:
            ip_start, ip_end = common.determine_range_string(address)
            result[address] = {}
            result[address]['inputs'] = self.get_links_in(ip_start, ip_end, timerange, port, protocol)
            result[address]['outputs'] = self.get_links_out(ip_start, ip_end, timerange, port, protocol)
        return result

    def get_links_in(self, ip_start, ip_end, timerange, port, protocol):
        return self._get_links(ip_start, ip_end, True, timerange, port, protocol)

    def get_links_out(self, ip_start, ip_end, timerange, port, protocol):
        return self._get_links(ip_start, ip_end, False, timerange, port, protocol)

    @staticmethod
    def build_where_clause(timestamp_range=None, port=None, protocol=None, rounding=True):
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

    def _get_links(self, ip_start, ip_end, inbound, timerange, port, protocol):
        """
        This function returns a list of the connections coming in to a given node from the rest of the graph.

        * The connections are aggregated into groups based on the first diverging ancestor.
            that means that connections to destination 1.2.3.4
            that come from source 1.9.*.* will be grouped together as a single connection.

        * for /8, /16, and /24, `IP to IP` is a unique connection.
        * for /32, `IP to IP on Port` make a unique connection.

        * If filter is provided, only connections over the given port are considered.

        * If timerange is provided, only connections that occur within the given time range are considered.

        :param ip_start:  integer indicating the low end of the IP address range constraint
        :param ip_end:  integer indicating the high end of the IP address range constraint
        :param inbound:  boolean, the direction of links to consider:
            If True, only consider links that terminate in the ip_range specified.
            If False, only consider links that originate in the ip_range specified,
        :param port:  int or None; Only consider connections using this destination port.
        :param timerange:  Tuple of (start, end) unix timestamps. Only connections happening
        during this time period are considered.
        :param protocol: String or None; filter to only connections using this protocol.
        :return: A list of db results formated as web.storage objects (used like dictionaries)
        """
        ports = (ip_start == ip_end)  # include ports in the results?
        where = self.build_where_clause(timerange, port, protocol)

        if ports:
            select = "src_start, src_end, dst_start, dst_end, port, SUM(links) AS 'links', SUM(bytes) AS 'bytes', SUM(packets) AS 'packets', GROUP_CONCAT(DISTINCT protocols SEPARATOR ',') AS 'protocols'"
            group_by = "GROUP BY src_start, src_end, dst_start, dst_end, port"
        else:
            select = "src_start, src_end, dst_start, dst_end, SUM(links) AS 'links', SUM(bytes) AS 'bytes', SUM(packets) AS 'packets', GROUP_CONCAT(DISTINCT protocols SEPARATOR ',') AS 'protocols'"
            group_by = "GROUP BY src_start, src_end, dst_start, dst_end"

        if inbound:
            query = """
            SELECT {select}
            FROM {table}
            WHERE dst_start = $start && dst_end = $end
             {where}
            {group_by}
            """.format(where=where, select=select, group_by=group_by, table=self.table_links_in)
        else:
            query = """
            SELECT {select}
            FROM {table}
            WHERE src_start = $start && src_end = $end
             {where}
            {group_by}
            """.format(where=where, select=select, group_by=group_by, table=self.table_links_out)

        qvars = {"start": ip_start, "end": ip_end}
        rows = list(self.db.query(query, vars=qvars))
        return rows

    def get_all_endpoints(self):
        query = """SELECT src AS 'ip' from {table_links}
UNION
SELECT dst AS 'ip' from {table_links};""".format(table_links=self.table_links)
        rows = self.db.query(query)
        return [row['ip'] for row in rows]
