import web
import common
from datetime import datetime
import time
import models.datasources

def parse_sql_file(path, replacements):
    with open(path, 'r') as f:
        lines = f.readlines()
    # remove comment lines
    lines = [i for i in lines if not i.startswith("--")]
    # join into one long string
    script = " ".join(lines)
    # do any necessary string replacements
    if replacements:
        script = script.format(**replacements)
    # split string into a list of commands
    commands = script.split(";")
    # ignore empty statements (like trailing newlines)
    commands = filter(lambda x: bool(x.strip()), commands)
    return commands


def exec_sql(connection, path, replacements=None):
    if not replacements:
        commands = parse_sql_file(path, {})
    else:
        commands = parse_sql_file(path, replacements)
    for command in commands:
        connection.query(command)


def get_syslog_size(datasource, buffer, _test=False):
    return common.db.select("ds_{0}_Syslog{1}".format(datasource, buffer),
                            what="COUNT(1) AS 'rows'",
                            _test=_test)[0].rows


def get_timerange(ds):
    datasources = models.datasources.Datasources()
    if ds not in datasources.dses:
        raise ValueError("Invalid data source specified. ({0} not in {1})".format(ds, datasources.dses))
    prefix = "ds_{0}_".format(ds)

    rows = common.db.query("SELECT MIN(timestamp) AS 'min', MAX(timestamp) AS 'max' "
                           "FROM {prefix}Links;".format(prefix=prefix))
    row = rows[0]
    if row['min'] is None or row['max'] is None:
        now = time.mktime(datetime.now().timetuple())
        return {'min': now, 'max': now}
    return {'min': time.mktime(row['min'].timetuple()), 'max': time.mktime(row['max'].timetuple())}


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
    WHERE = str(web.db.reparam("\n    && ".join(clauses), qvars))
    if WHERE:
        WHERE = "    && " + WHERE
    return WHERE


def get_protocol_list(ds):
    dses = get_ds_list_cached()
    if ds not in dses:
        raise ValueError("Invalid data source specified. ({0} not in {1})".format(ds, dses))
    prefix = "ds_{0}_".format(ds)
    table = "{0}Links".format(prefix)
    return [row.protocol for row in common.db.select(table, what="DISTINCT protocol") if row.protocol]


def get_table_info(ds, clauses, page, page_size, order_by, order_dir):
    dses = get_ds_list_cached()
    if ds not in dses:
        raise ValueError("Invalid data source specified. ({0} not in {1})".format(ds, dses))
    prefix = "ds_{0}_".format(ds)

    WHERE = " && ".join(clause.where() for clause in clauses if clause.where())
    if WHERE:
        WHERE = "WHERE " + WHERE

    HAVING = " && ".join(clause.having() for clause in clauses if clause.having())
    if HAVING:
        HAVING = "HAVING (conn_out + conn_in != 0) && " + HAVING
    else:
        HAVING = "HAVING (conn_out + conn_in != 0)"

    #      ['address', 'alias', 'role', 'environment', 'tags', 'bytes', 'packets', 'protocols']
    cols = ['nodes.ipstart', 'nodes.alias', '(conn_in / (conn_in + conn_out))', 'env', 'CONCAT(tags, parent_tags)', '(bytes_in + bytes_out)', '(packets_in + packets_out)', 'CONCAT(proto_in, proto_out)']
    ORDERBY = ""
    if 0 <= order_by < len(cols) and order_dir in ['asc', 'desc']:
        ORDERBY = "ORDER BY {0} {1}".format(cols[order_by], order_dir)

    #TODO: seconds has a magic number 300 added to account for DB time quantization.
    # note: group concat max length is default at 1024.
    # if any data is lost due to max length, try:
    # SET group_concat_max_len = 2048
    query = """
    SELECT CONCAT(decodeIP(ipstart), CONCAT('/', subnet)) AS 'address'
        , COALESCE(nodes.alias, '') AS 'alias'
        , COALESCE((
            SELECT env
            FROM Nodes nz
            WHERE nodes.ipstart >= nz.ipstart AND nodes.ipend <= nz.ipend AND env IS NOT NULL AND env != "inherit"
            ORDER BY (nodes.ipstart - nz.ipstart + nz.ipend - nodes.ipend) ASC
            LIMIT 1
        ), 'production') AS "env"
        , COALESCE((SELECT SUM(links)
            FROM {prefix}LinksOut AS l_out
            WHERE l_out.src_start = nodes.ipstart
              AND l_out.src_end = nodes.ipend
         ),0) AS 'conn_out'
        , COALESCE((SELECT SUM(links)
            FROM {prefix}LinksIn AS l_in
            WHERE l_in.dst_start = nodes.ipstart
              AND l_in.dst_end = nodes.ipend
         ),0) AS 'conn_in'
        , COALESCE((SELECT SUM(bytes)
            FROM {prefix}LinksOut AS l_out
            WHERE l_out.src_start = nodes.ipstart
              AND l_out.src_end = nodes.ipend
         ),0) AS 'bytes_out'
        , COALESCE((SELECT SUM(bytes)
            FROM {prefix}LinksIn AS l_in
            WHERE l_in.dst_start = nodes.ipstart
              AND l_in.dst_end = nodes.ipend
         ),0) AS 'bytes_in'
        , COALESCE((SELECT SUM(packets)
            FROM {prefix}LinksOut AS l_out
            WHERE l_out.src_start = nodes.ipstart
              AND l_out.src_end = nodes.ipend
         ),0) AS 'packets_out'
        , COALESCE((SELECT SUM(packets)
            FROM {prefix}LinksIn AS l_in
            WHERE l_in.dst_start = nodes.ipstart
              AND l_in.dst_end = nodes.ipend
         ),0) AS 'packets_in'
        , COALESCE((SELECT (MAX(TIME_TO_SEC(timestamp)) - MIN(TIME_TO_SEC(timestamp)) + 300)
            FROM {prefix}Links AS l
        ),0) AS 'seconds'
        , COALESCE((SELECT GROUP_CONCAT(DISTINCT protocols SEPARATOR ',')
            FROM {prefix}LinksIn AS l_in
            WHERE l_in.dst_start = nodes.ipstart AND l_in.dst_end = nodes.ipend
         ),"") AS 'proto_in'
        , COALESCE((SELECT GROUP_CONCAT(DISTINCT protocols SEPARATOR ',')
            FROM {prefix}LinksOut AS l_out
            WHERE l_out.src_start = nodes.ipstart AND l_out.src_end = nodes.ipend
         ),"") AS 'proto_out'
        , COALESCE((SELECT GROUP_CONCAT(tag SEPARATOR ', ')
            FROM Tags
            WHERE Tags.ipstart = nodes.ipstart AND Tags.ipend = nodes.ipend
            GROUP BY ipstart, ipend
         ),"") AS 'tags'
        , COALESCE((SELECT GROUP_CONCAT(tag SEPARATOR ', ')
            FROM Tags
            WHERE (Tags.ipstart <= nodes.ipstart AND Tags.ipend > nodes.ipend) OR (Tags.ipstart < nodes.ipstart AND Tags.ipend >= nodes.ipend)
            GROUP BY nodes.ipstart, nodes.ipend
         ),"") AS 'parent_tags'
    FROM Nodes AS nodes
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
        prefix=prefix)

    info = list(common.db.query(query))
    return info


def print_dict(d, indent = 0):
    for k,v in d.iteritems():
        if type(v) == dict:
            print("{0}{1:>20s}: ".format(indent * 4 * " ", k))
            print_dict(v, indent + 1)
        else:
            print("{0}{1:>20s}: {2}".format(indent*4*" ", k, repr(v)))
