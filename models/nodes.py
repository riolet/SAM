import web
import common
import dbaccess


class Nodes:
    default_environments = {'production', 'dev', 'inherit'}

    def __init__(self):
        self.db = common.db
        self.table = 'Nodes'
        self.tags_table = 'Tags'

    def set_alias(self, address, alias):
        r = common.determine_range_string(address)
        where = {"ipstart": r[0], "ipend": r[1]}
        self.db.update(self.table, where, alias=alias)

    def set_env(self, address, env):
        r = common.determine_range_string(address)
        where = {"ipstart": r[0], "ipend": r[1]}
        self.db.update(self.table, where, env=env)

    def set_tags(self, address, new_tags):
        """
        Assigns a new set of tags to an address overwriting any existing tag assignments.

        :param address: A string dotted-decimal IP address such as "192.168.2.100" or "21.66" or "1.2.0.0/16"
        :param new_tags: A list of tag strings. e.g. ['tag_one', 'tag_two', 'tag_three']
        :return: None
        """
        what = "ipstart, ipend, tag"
        r = common.determine_range_string(address)
        row = {"ipstart": r[0], "ipend": r[1]}
        where = "ipstart = $ipstart AND ipend = $ipend"

        existing = list(self.db.select(self.tags_table, vars=row, what=what, where=where))
        new_tags = set(new_tags)
        old_tags = {x.tag for x in existing}
        removals = old_tags - new_tags
        additions = new_tags - old_tags

        for tag in additions:
            row['tag'] = tag
            self.db.insert("Tags", **row)

        for tag in removals:
            row['tag'] = tag
            where = "ipstart = $ipstart AND ipend = $ipend AND tag = $tag"
            self.db.delete(self.tags_table, where=where, vars=row)

    def get_tags(self, address):
        """
        Gets all directly assigned tags and inherited parent tags for a given addresss
    
        :param address: A string dotted-decimal IP address such as "192.168.2.100" or "21.66" or "1.2.0.0/16"
        :return: A dict of lists of strings, with keys 'tags' and 'p_tags'
                where p_tags are inherited tags from parent nodes
        """
        ipstart, ipend = common.determine_range_string(address)
        where = 'ipstart <= $start AND ipend >= $end'
        qvars = {'start': ipstart, 'end': ipend}
        data = self.db.select(self.tags_table, vars=qvars, where=where)
        parent_tags = []
        tags = []
        for row in data:
            if row.ipend == ipend and row.ipstart == ipstart:
                tags.append(row.tag)
            else:
                parent_tags.append(row.tag)
        return {"p_tags": parent_tags, "tags": tags}
    
    def get_tag_list(self):
        return [row.tag for row in self.db.select(self.tags_table, what="DISTINCT tag") if row.tag]
    
    def get_env(self, address):
        ipstart, ipend = common.determine_range_string(address)
        where = 'ipstart <= $start AND ipend >= $end'
        qvars = {'start': ipstart, 'end': ipend}
        data = self.db.select(self.table, vars=qvars, where=where, what="ipstart, ipend, env")
        parent_env = "production"
        env = "inherit"
        nearest_distance = -1
        for row in data:
            if row.ipend == ipend and row.ipstart == ipstart:
                if row.env:
                    env = row.env
            else:
                dist = row.ipend - ipend + ipstart - row.ipstart
                if nearest_distance == -1 or dist < nearest_distance:
                    if row.env and row.env != "inherit":
                        parent_env = row.env
        return {"env": env, "p_env": parent_env}
    
    def get_env_list(self):
        envs = set(row.env for row in self.db.select(self.table, what="DISTINCT env") if row.env)
        envs |= self.default_environments
        return envs

    def delete_custom_tags(self):
        common.db.delete(self.tags_table, "1")

    def delete_custom_envs(self):
        common.db.update(self.table, "1", env=web.sqlliteral("NULL"))

    def get_root_nodes(self):
        return list(self.db.select(self.table, where="subnet=8"))

    def get_children(self, address):
        ip_start, ip_end = common.determine_range_string(address)
        diff = ip_end - ip_start
        if diff > 16777215:
            subnet = 8
        elif diff > 65536:
            subnet = 16
        elif diff > 255:
            subnet = 24
        elif diff > 0:
            subnet = 32
        else:
            return []

        where = "subnet={2} && ipstart BETWEEN {0} AND {1}".format(ip_start, ip_end, subnet)
        rows = self.db.select(self.table, where=where)
        return list(rows)

    def get_metadata(self, ds, address):
        ipstart, ipend = common.determine_range_string(address)
        dses = dbaccess.get_ds_list_cached()
        if ds not in dses:
            raise ValueError("Invalid data source specified. ({0} not in {1})".format(ds, dses))

        links_table = "ds_{0}_Links".format(ds)

        qvars = {"start": ipstart, "end": ipend}
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
                FROM {table}
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
                FROM {table}
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
        """.format(table=self.table, links_table=links_table)
        results = self.db.query(query, vars=qvars)

        if len(results) == 1:
            return results[0]
        else:
            return {}
