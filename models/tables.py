import web
import common
import filters


class Table:
    def __init__(self, db, subscription, ds):
        """
        :type db: web.DB
        :type subscription: int
        :type ds: int
        :param db: 
        :param subscription: 
        :param ds: 
        """
        self.db = db
        self.sub = subscription
        self.ds = ds
        self.table_nodes = "s{acct}_Nodes".format(acct=self.sub)
        self.table_tags = "s{acct}_Tags".format(acct=self.sub)
        self.table_links = "s{acct}_ds{id}_Links".format(acct=self.sub, id=ds)
        self.table_links_in = "s{acct}_ds{id}_LinksIn".format(acct=self.sub, id=ds)
        self.table_links_out = "s{acct}_ds{id}_LinksOut".format(acct=self.sub, id=ds)
        if self.db.dbname == 'mysql':
            self.elapsed = "COALESCE((SELECT (UNIX_TIMESTAMP(MAX(timestamp)) " \
                           "- UNIX_TIMESTAMP(MIN(timestamp)) + 300) FROM {table_links} AS l),1)"
        else:
            self.elapsed = "COALESCE((SELECT (MAX(timestamp) - MIN(timestamp) + 300) FROM {table_links} AS l),1)"
        self.elapsed.format(table_links=self.table_links)

    def get_table_info(self, clauses, page, page_size, order_by, order_dir):
        """
        
        :param clauses: list of Filter objects
        :type clauses: list[ filters.Filter ]
        :param page: int; 0-based results page number
        :param page_size: int; number of results per page. will return page_size + 1. 
                          If the +1 is returned, you know there's a next page available.
                          5 results, page size 2 = 
                            0:(1,2,3), 
                            1:(3,4,5),
                            2:(5,)
        :param order_by: Column index to order by.  list is: 
                        ['address', 'alias', 'role', 'environment', 'tags', 'bytes', 'packets', 'protocols'] 
        :param order_dir: 'asc' or 'desc' 
        :return: list of dictionaries (table rows)
        """

        where_clause = " AND ".join(clause.where(self.db) for clause in clauses if clause.where(self.db))
        if self.db.dbname == 'sqlite':
            if where_clause:
                where_clause = "WHERE (conn_out + conn_in != 0) AND " + where_clause
            else:
                where_clause = "WHERE (conn_out + conn_in != 0)"
        else:
            if where_clause:
                where_clause = "WHERE " + where_clause


        having_clause = " AND ".join(clause.having(self.db) for clause in clauses if clause.having(self.db))
        if self.db.dbname == 'mysql':
            if having_clause:
                having_clause = "HAVING (conn_out + conn_in != 0) AND " + having_clause
            else:
                having_clause = "HAVING (conn_out + conn_in != 0)"
        else:
            if having_clause:
                having_clause = "HAVING " + having_clause


        # ['address', 'alias', 'role', 'environment', 'tags', 'bytes', 'packets', 'protocols']
        cols = ['nodes.ipstart', 'nodes.alias', '(conn_in / (conn_in + conn_out))', 'env', 'CONCAT(tags, parent_tags)',
                '(bytes_in + bytes_out)', '(packets_in + packets_out)', 'CONCAT(proto_in, proto_out)']
        order_clause = ""
        order_dir = order_dir.lower()
        if 0 <= order_by < len(cols) and order_dir in ['asc', 'desc']:
            order_clause = "ORDER BY {0} {1}".format(cols[order_by], order_dir)

        # TODO: seconds has a magic number 300 added to account for DB time quantization.
        # note: group concat max length is default at 1024.
        # if any data is lost due to max length, try:
        # SET group_concat_max_len = 2048
        if self.db.dbname == 'sqlite':
            common.sqlite_udf(self.db)

        query = """
        SELECT {address} AS 'address'
            , COALESCE(nodes.alias, '') AS 'alias'
            , COALESCE((
                SELECT env
                FROM {table_nodes} nz
                WHERE nodes.ipstart >= nz.ipstart AND nodes.ipend <= nz.ipend AND env IS NOT NULL AND env != "inherit"
                ORDER BY subnet DESC
                LIMIT 1
            ), 'production') AS "computed_env"
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
            , {elapsed} AS 'seconds'
            , COALESCE((SELECT GROUP_CONCAT(DISTINCT protocols)
                FROM {table_links_in} AS l_in
                WHERE l_in.dst_start = nodes.ipstart AND l_in.dst_end = nodes.ipend
             ),"") AS 'proto_in'
            , COALESCE((SELECT GROUP_CONCAT(DISTINCT protocols)
                FROM {table_links_out} AS l_out
                WHERE l_out.src_start = nodes.ipstart AND l_out.src_end = nodes.ipend
             ),"") AS 'proto_out'
            , COALESCE((SELECT GROUP_CONCAT(DISTINCT tag)
                FROM {table_tags} AS `t`
                WHERE t.ipstart = nodes.ipstart AND t.ipend = nodes.ipend
             ),"") AS 'tags'
            , COALESCE((SELECT GROUP_CONCAT(DISTINCT tag)
                FROM {table_tags} AS `t`
                WHERE (t.ipstart <= nodes.ipstart AND t.ipend > nodes.ipend) OR (t.ipstart < nodes.ipstart AND t.ipend >= nodes.ipend)
             ),"") AS 'parent_tags'
        FROM {table_nodes} AS nodes
        {WHERE}
        {HAVING}
        {ORDER}
        LIMIT {START},{RANGE};
        """.format(
            address=common.db_concat(self.db, 'decodeIP(ipstart)', "'/'", 'subnet'),
            elapsed=self.elapsed,
            WHERE=where_clause,
            HAVING=having_clause,
            ORDER=order_clause,
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

        info = list(self.db.query(query))
        return info
