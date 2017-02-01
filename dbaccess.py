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


def print_dict(d, indent = 0):
    for k,v in d.iteritems():
        if type(v) == dict:
            print("{0}{1:>20s}: ".format(indent * 4 * " ", k))
            print_dict(v, indent + 1)
        else:
            print("{0}{1:>20s}: {2}".format(indent*4*" ", k, repr(v)))
