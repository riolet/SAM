import web
import common
import dbaccess


class Table:
    def __init__(self, ds):
        self.db = common.db
        self.table_nodes = "Nodes"
        self.table_tags = "Tags"
        self.table_links = "ds_{0}_Links".format(ds)
        self.table_links_in = "ds_{0}_LinksIn".format(ds)
        self.table_links_out = "ds_{0}_LinksOut".format(ds)

        self.ds = ds

    def get_table_info(self, clauses, page, page_size, order_by, order_dir):

        WHERE = " && ".join(clause.where() for clause in clauses if clause.where())
        if WHERE:
            WHERE = "WHERE " + WHERE

        HAVING = " && ".join(clause.having() for clause in clauses if clause.having())
        if HAVING:
            HAVING = "HAVING (conn_out + conn_in != 0) && " + HAVING
        else:
            HAVING = "HAVING (conn_out + conn_in != 0)"

        # ['address', 'alias', 'role', 'environment', 'tags', 'bytes', 'packets', 'protocols']
        cols = ['nodes.ipstart', 'nodes.alias', '(conn_in / (conn_in + conn_out))', 'env', 'CONCAT(tags, parent_tags)',
                '(bytes_in + bytes_out)', '(packets_in + packets_out)', 'CONCAT(proto_in, proto_out)']
        ORDERBY = ""
        if 0 <= order_by < len(cols) and order_dir in ['asc', 'desc']:
            ORDERBY = "ORDER BY {0} {1}".format(cols[order_by], order_dir)

        # TODO: seconds has a magic number 300 added to account for DB time quantization.
        # note: group concat max length is default at 1024.
        # if any data is lost due to max length, try:
        # SET group_concat_max_len = 2048
        query = """
        SELECT CONCAT(decodeIP(ipstart), CONCAT('/', subnet)) AS 'address'
            , COALESCE(nodes.alias, '') AS 'alias'
            , COALESCE((
                SELECT env
                FROM {table_nodes} nz
                WHERE nodes.ipstart >= nz.ipstart AND nodes.ipend <= nz.ipend AND env IS NOT NULL AND env != "inherit"
                ORDER BY (nodes.ipstart - nz.ipstart + nz.ipend - nodes.ipend) ASC
                LIMIT 1
            ), 'production') AS "env"
            , COALESCE((SELECT SUM(links)
                FROM {table_links_out} AS l_out
                WHERE l_out.src_start = nodes.ipstart
                  AND l_out.src_end = nodes.ipend
             ),0) AS 'conn_out'
            , COALESCE((SELECT SUM(links)
                FROM {table_links_in} AS l_in
                WHERE l_in.dst_start = nodes.ipstart
                  AND l_in.dst_end = nodes.ipend
             ),0) AS 'conn_in'
            , COALESCE((SELECT SUM(bytes)
                FROM {table_links_out} AS l_out
                WHERE l_out.src_start = nodes.ipstart
                  AND l_out.src_end = nodes.ipend
             ),0) AS 'bytes_out'
            , COALESCE((SELECT SUM(bytes)
                FROM {table_links_in} AS l_in
                WHERE l_in.dst_start = nodes.ipstart
                  AND l_in.dst_end = nodes.ipend
             ),0) AS 'bytes_in'
            , COALESCE((SELECT SUM(packets)
                FROM {table_links_out} AS l_out
                WHERE l_out.src_start = nodes.ipstart
                  AND l_out.src_end = nodes.ipend
             ),0) AS 'packets_out'
            , COALESCE((SELECT SUM(packets)
                FROM {table_links_in} AS l_in
                WHERE l_in.dst_start = nodes.ipstart
                  AND l_in.dst_end = nodes.ipend
             ),0) AS 'packets_in'
            , COALESCE((SELECT (MAX(TIME_TO_SEC(timestamp)) - MIN(TIME_TO_SEC(timestamp)) + 300)
                FROM {table_links} AS l
            ),0) AS 'seconds'
            , COALESCE((SELECT GROUP_CONCAT(DISTINCT protocols SEPARATOR ',')
                FROM {table_links_in} AS l_in
                WHERE l_in.dst_start = nodes.ipstart AND l_in.dst_end = nodes.ipend
             ),"") AS 'proto_in'
            , COALESCE((SELECT GROUP_CONCAT(DISTINCT protocols SEPARATOR ',')
                FROM {table_links_out} AS l_out
                WHERE l_out.src_start = nodes.ipstart AND l_out.src_end = nodes.ipend
             ),"") AS 'proto_out'
            , COALESCE((SELECT GROUP_CONCAT(tag SEPARATOR ', ')
                FROM {table_tags} AS `t`
                WHERE t.ipstart = nodes.ipstart AND t.ipend = nodes.ipend
                GROUP BY nodes.ipstart, nodes.ipend
             ),"") AS 'tags'
            , COALESCE((SELECT GROUP_CONCAT(tag SEPARATOR ', ')
                FROM {table_tags} AS `t`
                WHERE (t.ipstart <= nodes.ipstart AND t.ipend > nodes.ipend) OR (t.ipstart < nodes.ipstart AND t.ipend >= nodes.ipend)
                GROUP BY nodes.ipstart, nodes.ipend
             ),"") AS 'parent_tags'
        FROM {table_nodes} AS nodes
        {WHERE}
        {HAVING}
        {ORDER}
        LIMIT {START},{RANGE};
        """.format(
            WHERE=WHERE,
            HAVING=HAVING,
            ORDER=ORDERBY,
            START=page * page_size,
            RANGE=page_size + 1,
            table_links=self.table_links,
            table_links_in=self.table_links_in,
            table_links_out=self.table_links_out,
            table_nodes=self.table_nodes,
            table_tags=self.table_tags)\
            .format(table_links=self.table_links,
                    table_links_in=self.table_links_in,
                    table_links_out=self.table_links_out,
                    table_nodes=self.table_nodes,
                    table_tags=self.table_tags)

        info = list(common.db.query(query))
        return info
