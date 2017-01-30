import web
import common
import dbaccess


class Links:
    def __init__(self):
        self.db = common.db
        self.table_name = "ds_{}_Links"
        self.table_name_in = "ds_{}_LinksIn"
        self.table_name_out = "ds_{}_LinksOut"

    def get_links(self, ds, addresses, timerange, port, protocol):
        seconds = timerange[1] - timerange[0]
        minutes = seconds // 60

        result = {}
        for address in addresses:
            ip_start, ip_end = common.determine_range_string(address)
            result[address] = {}
            result[address]['inputs'] = self.get_links_in(ds, ip_start, ip_end, timerange, port, protocol)
            result[address]['outputs'] = self.get_links_out(ds, ip_start, ip_end, timerange, port, protocol)

            # remove duplicate protocol names, normalize values over time
            for row in result[address]['inputs']:
                row['protocols'] = ",".join(set(row['protocols'].split(',')))
                row['links'] /= minutes
                row['bytes'] /= seconds
                row['packets'] /= seconds

            for row in result[address]['outputs']:
                row['protocols'] = ",".join(set(row['protocols'].split(',')))
                row['links'] /= minutes
                row['bytes'] /= seconds
                row['packets'] /= seconds
        return result

    def get_links_in(self, ds, ip_start, ip_end, timerange, port, protocol):
        return self._get_links(ds, ip_start, ip_end, True, timerange, port, protocol)

    def get_links_out(self, ds, ip_start, ip_end, timerange, port, protocol):
        return self._get_links(ds, ip_start, ip_end, False, timerange, port, protocol)

    def build_where_clause(self, timestamp_range=None, port=None, protocol=None, rounding=True):
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

    def _get_links(self, ds, ip_start, ip_end, inbound, timerange, port, protocol):
        """
        This function returns a list of the connections coming in to a given node from the rest of the graph.

        * The connections are aggregated into groups based on the first diverging ancestor.
            that means that connections to destination 1.2.3.4
            that come from source 1.9.*.* will be grouped together as a single connection.

        * for /8, /16, and /24, `IP to IP` is a unique connection.
        * for /32, `IP to IP on Port` make a unique connection.

        * If filter is provided, only connections over the given port are considered.

        * If timerange is provided, only connections that occur within the given time range are considered.

        :param ds: integer indicating which datasource to use
        :param ip_start:  integer indicating the low end of the IP address range constraint
        :param ip_end:  integer indicating the high end of the IP address range constraint
        :param inbound:  boolean, the direction of links to consider:
            If True, only consider links that terminate in the ip_range specified.
            If False, only consider links that originate in the ip_range specified,
        :param port:  Only consider connections using this destination port.
        :param timerange:  Tuple of (start, end) timestamps. Only connections happening
        during this time period are considered.
        :return: A list of db results formated as web.storage objects (used like dictionaries)
        """
        ports = (ip_start == ip_end)  # include ports in the results?
        where = self.build_where_clause(timerange, port, protocol)
        dses = dbaccess.get_ds_list_cached()
        if ds not in dses:
            raise ValueError("Invalid data source specified. ({0} not in {1})".format(ds, dses))

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
            """.format(where=where, select=select, group_by=group_by, table=self.table_name_in.format(ds))
        else:
            query = """
            SELECT {select}
            FROM {table}
            WHERE src_start = $start && src_end = $end
             {where}
            {group_by}
            """.format(where=where, select=select, group_by=group_by, table=self.table_name_out.format(ds))

        qvars = {"start": ip_start, "end": ip_end}
        rows = list(self.db.query(query, vars=qvars))
        return rows
        