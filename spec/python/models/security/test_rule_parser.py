from datetime import datetime
import pytest
from web.utils import IterBetter
import web
from spec.python import db_connection
from sam.models.security import rule_parser, ruling_process, rule
from sam.models.links import Links
from sam.importers.import_base import BaseImporter
from sam.preprocess import Preprocessor
from sam import common

db = db_connection.db
sub_id = db_connection.default_sub
ds_full = db_connection.dsid_default
ds_temp = db_connection.dsid_short
default_timerange = None


def test_tokenize_simple():
    s1 = 'src host = 1.2.3.4'

    parser = rule_parser.RuleParser({}, 'src', s1, default_timerange)
    assert parser.where_clauses == [('CLAUSE', {'comp': '=', 'dir': 'src', 'type': 'host', 'value': '1.2.3.4'})]
    assert parser.having_clauses == []

    s2 = 'src port = 51223'
    parser = rule_parser.RuleParser({}, 'src', s2, default_timerange)
    assert parser.where_clauses == [('CLAUSE', {'comp': '=', 'dir': 'src', 'type': 'port', 'value': '51223'})]
    assert parser.having_clauses == []

    s3 = 'dst host = 1.2.3.4'
    parser = rule_parser.RuleParser({}, 'src', s3, default_timerange)
    assert parser.where_clauses == [('CLAUSE', {'comp': '=', 'dir': 'dst', 'type': 'host', 'value': '1.2.3.4'})]
    assert parser.having_clauses == []

    s4 = 'dst port = 443'
    parser = rule_parser.RuleParser({}, 'src', s4, default_timerange)
    assert parser.where_clauses == [('CLAUSE', {'comp': '=', 'dir': 'dst', 'type': 'port', 'value': '443'})]
    assert parser.having_clauses == []

    s5 = 'host = 1.2.3.4'
    parser = rule_parser.RuleParser({}, 'src', s5, default_timerange)
    assert parser.where_clauses == [('CLAUSE', {'comp': '=', 'dir': 'either', 'type': 'host', 'value': '1.2.3.4'})]
    assert parser.having_clauses == []

    s6 = 'host 1.2.3.4'
    parser = rule_parser.RuleParser({}, 'src', s6, default_timerange)
    assert parser.where_clauses == [('CLAUSE', {'comp': '=', 'dir': 'either', 'type': 'host', 'value': '1.2.3.4'})]
    assert parser.having_clauses == []

    s7 = 'src host 1.2.3.4'
    parser = rule_parser.RuleParser({}, 'src', s7, default_timerange)
    assert parser.where_clauses == [('CLAUSE', {'comp': '=', 'dir': 'src', 'type': 'host', 'value': '1.2.3.4'})]
    assert parser.having_clauses == []

    s8 = '1.2.3.4'
    parser = rule_parser.RuleParser({}, 'src', s8, default_timerange)
    assert parser.where_clauses == [('CLAUSE', {'comp': '=', 'dir': 'either', 'type': 'host', 'value': '1.2.3.4'})]
    assert parser.having_clauses == []

    s9 = 'dst 1.2.3.4'
    parser = rule_parser.RuleParser({}, 'src', s9, default_timerange)
    assert parser.where_clauses == [('CLAUSE', {'comp': '=', 'dir': 'dst', 'type': 'host', 'value': '1.2.3.4'})]
    assert parser.having_clauses == []

    s10a = 'port 443'
    parser = rule_parser.RuleParser({}, 'src', s10a, default_timerange)
    assert parser.where_clauses == [('CLAUSE', {'comp': '=', 'dir': 'either', 'type': 'port', 'value': '443'})]
    assert parser.having_clauses == []

    s10b = 'dst port 443'
    parser = rule_parser.RuleParser({}, 'src', s10b, default_timerange)
    assert parser.where_clauses == [('CLAUSE', {'comp': '=', 'dir': 'dst', 'type': 'port', 'value': '443'})]
    assert parser.having_clauses == []

    s10c = 'dst port [80, 443]'
    parser = rule_parser.RuleParser({}, 'src', s10c, default_timerange)
    assert parser.where_clauses == [('CLAUSE', {'comp': 'in', 'dir': 'dst', 'type': 'port', 'value': ['80', '443']})]
    assert parser.having_clauses == []

    s10d = 'dst port $ports'
    parser = rule_parser.RuleParser({'ports': 80}, 'src', s10d, default_timerange)
    assert parser.where_clauses == [('CLAUSE', {'comp': '=', 'dir': 'dst', 'type': 'port', 'value': '80'})]
    assert parser.having_clauses == []

    s10e = 'dst port $ports'
    parser = rule_parser.RuleParser({'ports': [80, 443]}, 'src', s10e, default_timerange)
    assert parser.where_clauses == [('CLAUSE', {'comp': 'in', 'dir': 'dst', 'type': 'port', 'value': ['80', '443']})]
    assert parser.having_clauses == []

    s12 = 'protocol tcp'
    parser = rule_parser.RuleParser({}, 'src', s12, default_timerange)
    assert parser.where_clauses == [('CLAUSE', {'comp': '=', 'dir': 'either', 'type': 'protocol', 'value': 'tcp'})]
    assert parser.having_clauses == []


def test_tokenize_lists():
    s1 = 'src host in [1, 2, 3, 4]'
    parser = rule_parser.RuleParser({}, 'src', s1, default_timerange)
    assert parser.where_clauses == [('CLAUSE', {'comp': 'in', 'dir': 'src', 'type': 'host', 'value': list('1234')})]

    s2 = 'src host in (5 ,6 ,7 , 8)'
    parser = rule_parser.RuleParser({}, 'src', s2, default_timerange)
    assert parser.where_clauses == [('CLAUSE', {'comp': 'in', 'dir': 'src', 'type': 'host', 'value': list('5678')})]

    s3 = 'src host in (9)'
    parser = rule_parser.RuleParser({}, 'src', s3, default_timerange)
    assert parser.where_clauses == [('CLAUSE', {'comp': 'in', 'dir': 'src', 'type': 'host', 'value': list('9')})]

    s4 = 'src host in [0]'
    parser = rule_parser.RuleParser({}, 'src', s4, default_timerange)
    assert parser.where_clauses == [('CLAUSE', {'comp': 'in', 'dir': 'src', 'type': 'host', 'value': list('0')})]

    s5 = 'dst port in $ports'
    tr = {'ports': [22, 33, 44, 55]}
    parser = rule_parser.RuleParser(tr, 'src', s5, default_timerange)
    assert parser.where_clauses == [('CLAUSE',
                                     {'comp': 'in', 'dir': 'dst', 'type': 'port', 'value': ['22', '33', '44', '55']})]

    tr = {'ports': (22, 33, 44, 55)}
    parser = rule_parser.RuleParser(tr, 'src', s5, default_timerange)
    assert parser.where_clauses == [('CLAUSE',
                                     {'comp': 'in', 'dir': 'dst', 'type': 'port', 'value': ['22', '33', '44', '55']})]

    tr = {'ports': '(22, 33, 44, 55)'}
    parser = rule_parser.RuleParser(tr, 'src', s5, default_timerange)
    assert parser.where_clauses == [('CLAUSE',
                                     {'comp': 'in', 'dir': 'dst', 'type': 'port', 'value': ['22', '33', '44', '55']})]


def test_tokenize_replacements():
    s1 = '$place'
    tr = {'place': 'hello'}
    parser = rule_parser.RuleParser(tr, 'src', s1, default_timerange)
    assert parser.tokens == [('LITERAL', 'hello')]

    tr = {'place': 42}
    parser = rule_parser.RuleParser(tr, 'src', s1, default_timerange)
    assert parser.tokens == [('LITERAL', '42')]

    s2 = 'host in $place'
    tr = {'place': [1, 2, 3]}
    parser = rule_parser.RuleParser(tr, 'src', s2, default_timerange)
    assert parser.tokens == [('TYPE', 'host'), ('LIST', 'in'), ('LIT_LIST', ['1', '2', '3'])]

    s2 = 'host in $place'
    tr = {'place': "(1 ,2 , 3)"}
    parser = rule_parser.RuleParser(tr, 'src', s2, default_timerange)
    assert parser.tokens == [('TYPE', 'host'), ('LIST', 'in'), ('LIT_LIST', ['1', '2', '3'])]


def test_tokenize_aggregates():
    s1 = 'src[host] > 50'
    tokens = rule_parser.RuleParser.tokenize(s1)
    expected = [
        ('AGGREGATE', 'src[host]'),
        ('COMPARATOR', '>'),
        ('LITERAL', '50')
    ]
    assert tokens == expected

    s2 = 'dst[port] 22'
    tokens = rule_parser.RuleParser.tokenize(s2)
    expected = [
        ('AGGREGATE', 'dst[port]'),
        ('LITERAL', '22')
    ]
    assert tokens == expected

    s3 = 'conn[links] > 3000'
    tokens = rule_parser.RuleParser.tokenize(s3)
    expected = [
        ('AGGREGATE', 'conn[links]'),
        ('COMPARATOR', '>'),
        ('LITERAL', '3000')
    ]
    assert tokens == expected

    # This is an expected failure.
    s4 = 'host[count] > 3000'
    tokens = rule_parser.RuleParser.tokenize(s4)
    expected = [
        ('TYPE', 'host'),
        ('LIT_LIST', '[count]'),
        ('COMPARATOR', '>'),
        ('LITERAL', '3000')
    ]
    assert tokens == expected

    s3 = 'conn[links] > 3000'
    tokens = rule_parser.RuleParser.tokenize(s3)
    expected = [
        ('AGGREGATE', ('conn', 'links')),
        ('COMPARATOR', '>'),
        ('LITERAL', '3000')
    ]
    rule_parser.RuleParser.decode_tokens({}, tokens)
    assert tokens == expected


def test_joins():
    s1 = 'src port 12345 and dst port 80'
    parser = rule_parser.RuleParser({}, 'src', s1, default_timerange)
    assert parser.where_clauses == [
        ('CLAUSE', {'dir': 'src', 'type': 'port', 'comp': '=', 'value': '12345'}),
        ('JOIN', 'and'),
        ('CLAUSE', {'dir': 'dst', 'type': 'port', 'comp': '=', 'value': '80'}),
    ]
    assert parser.having_clauses == []

    s2 = 'src port 12345 or dst port 80'
    parser = rule_parser.RuleParser({}, 'src', s2, default_timerange)
    assert parser.where_clauses == [
        ('CLAUSE', {'dir': 'src', 'type': 'port', 'comp': '=', 'value': '12345'}),
        ('JOIN', 'or'),
        ('CLAUSE', {'dir': 'dst', 'type': 'port', 'comp': '=', 'value': '80'}),
    ]
    assert parser.having_clauses == []

    s2 = 'dst port 80 or dst port 80 and dst port 80 or dst port 80 and dst port 80'
    parser = rule_parser.RuleParser({}, 'src', s2, default_timerange)
    assert parser.where_clauses == [
        ('CLAUSE', {'dir': 'dst', 'type': 'port', 'comp': '=', 'value': '80'}),
        ('JOIN', 'or'),
        ('CLAUSE', {'dir': 'dst', 'type': 'port', 'comp': '=', 'value': '80'}),
        ('JOIN', 'and'),
        ('CLAUSE', {'dir': 'dst', 'type': 'port', 'comp': '=', 'value': '80'}),
        ('JOIN', 'or'),
        ('CLAUSE', {'dir': 'dst', 'type': 'port', 'comp': '=', 'value': '80'}),
        ('JOIN', 'and'),
        ('CLAUSE', {'dir': 'dst', 'type': 'port', 'comp': '=', 'value': '80'}),
    ]
    assert parser.having_clauses == []


def test_negation():
    s1 = 'dst port not in (22, 33, 44)'
    parser = rule_parser.RuleParser({}, 'src', s1, default_timerange)
    assert parser.where_clauses == [
        ('CLAUSE', {'dir': 'dst', 'type': 'port', 'comp': 'not in', 'value': ['22', '33', '44']})
    ]
    assert parser.having_clauses == []

    s2 = 'dst port != 443'
    parser = rule_parser.RuleParser({}, 'src', s2, default_timerange)
    assert parser.where_clauses == [
        ('CLAUSE', {'dir': 'dst', 'type': 'port', 'comp': '!=', 'value': '443'})
    ]
    assert parser.having_clauses == []

    s3 = 'not dst port = 443'
    parser = rule_parser.RuleParser({}, 'src', s3, default_timerange)
    assert parser.where_clauses == [
        ('MODIFIER', 'not'),
        ('CLAUSE', {'dir': 'dst', 'type': 'port', 'comp': '=', 'value': '443'})
    ]
    assert parser.having_clauses == []

    s4 = 'not dst port not in (22, 33, 44)'
    parser = rule_parser.RuleParser({}, 'src', s4, default_timerange)
    assert parser.where_clauses == [
        ('MODIFIER', 'not'),
        ('CLAUSE', {'dir': 'dst', 'type': 'port', 'comp': 'not in', 'value': ['22', '33', '44']})
    ]
    assert parser.having_clauses == []


def test_parens():
    s = '(dst port < 500)'
    parser = rule_parser.RuleParser({}, 'src', s, default_timerange)
    assert parser.where_clauses == [
        ('MODIFIER', '('),
        ('CLAUSE', {'dir': 'dst', 'type': 'port', 'comp': '<', 'value': '500'}),
        ('MODIFIER', ')'),
    ]

    s = '((dst port < 500))'
    parser = rule_parser.RuleParser({}, 'src', s, default_timerange)
    assert parser.where_clauses == [
        ('MODIFIER', '('),
        ('MODIFIER', '('),
        ('CLAUSE', {'dir': 'dst', 'type': 'port', 'comp': '<', 'value': '500'}),
        ('MODIFIER', ')'),
        ('MODIFIER', ')'),
    ]

    s = 'dst port < 500)'
    with pytest.raises(rule_parser.RuleParseError):
        parser = rule_parser.RuleParser({}, 'src', s, default_timerange)

    s = '(dst port < 500'
    with pytest.raises(rule_parser.RuleParseError):
        parser = rule_parser.RuleParser({}, 'src', s, default_timerange)

    s = 'dst port < 500)('
    with pytest.raises(rule_parser.RuleParseError):
        parser = rule_parser.RuleParser({}, 'src', s, default_timerange)

    s = 'dst port < 500()'
    with pytest.raises(rule_parser.RuleParseError):
        parser = rule_parser.RuleParser({}, 'src', s, default_timerange)


def test_aggregates():
    s1 = 'having dst[ports] > 300'
    parser = rule_parser.RuleParser({}, 'src', s1, default_timerange)
    expected = [
        ('CONTEXT', 'having'),
        ('AGGREGATE', ('dst', 'ports')),
        ('COMPARATOR', '>'),
        ('LITERAL', '300')
    ]
    assert parser.tokens == expected
    expected = [
        ('CLAUSE', {
            'dir': 'dst',
            'agg': 'ports',
            'type': 'aggregate',
            'comp': '>',
            'value': '300'
        })
    ]
    assert parser.having_clauses == expected

    s2 = 'having conn[links] 1000 or not conn[links] 1050'
    parser = rule_parser.RuleParser({}, 'src', s2, default_timerange)
    expected = [
        ('CLAUSE', {
            'dir': 'conn',
            'agg': 'links',
            'type': 'aggregate',
            'comp': '=',
            'value': '1000'
        }),
        ('JOIN', 'or'),
        ('MODIFIER', 'not'),
        ('CLAUSE', {
            'dir': 'conn',
            'agg': 'links',
            'type': 'aggregate',
            'comp': '=',
            'value': '1050'
        }),
    ]
    assert parser.having_clauses == expected


def test_where_sql():
    s1 = 'src host = 1.2.3.4'
    parser = rule_parser.RuleParser({}, 'src', s1, default_timerange)
    sql = parser.sql
    assert sql.where == 'src = 16909060'

    s2 = 'src host in [1.2.3.4, 10.20.30.40, 100.200.50.150]'
    parser = rule_parser.RuleParser({}, 'src', s2, default_timerange)
    sql = parser.sql
    assert sql.where == 'src in (16909060, 169090600, 1690841750)'

    s3 = 'dst port in [22, 33, 44]'
    parser = rule_parser.RuleParser({}, 'src', s3, default_timerange)
    sql = parser.sql
    assert sql.where == "port in ('22', '33', '44')"

    s4 = 'dst port = 5'
    parser = rule_parser.RuleParser({}, 'src', s4, default_timerange)
    sql = parser.sql
    assert sql.where == "port = '5'"

    s5 = '(src host = 1.2.3.4 or dst host = 5.6.7.8) and port = 80'
    parser = rule_parser.RuleParser({}, 'src', s5, default_timerange)
    sql = parser.sql
    assert sql.where == "( src = 16909060 or dst = 84281096 ) and port = '80'"

    s6 = 'host 10.20.30.40 and not (10.24.34.44 or 10.24.34.45)'
    parser = rule_parser.RuleParser({}, 'src', s6, default_timerange)
    sql = parser.sql
    assert sql.where == '(dst = 169090600 or src = 169090600) and not ' \
                        '( (dst = 169353772 or src = 169353772) or (dst = 169353773 or src = 169353773) )'

    s7 = 'protocol UDP or protocol tcp'
    parser = rule_parser.RuleParser({}, 'src', s7, default_timerange)
    sql = parser.sql
    assert sql.where == "protocol = 'UDP' or protocol = 'TCP'"


def test_having_sql():
    s1 = 'having conn[links] > 1000'
    parser = rule_parser.RuleParser({}, 'dst', s1, default_timerange)
    sql = parser.sql

    print(" WHERE ".center(80, '='))
    print(sql.where)
    print(" HAVING ".center(80, '='))
    print(sql.having)
    print(" GROUPBY ".center(80, '='))
    print(sql.groupby)
    print(" WHAT ".center(80, '='))
    print(sql.what)
    print(" -- ".center(80, '='))

    assert sql.where == ''
    assert sql.having == "`conn[links]` > '1000'"
    assert sql.groupby == 'timestamp, dst'

    s2 = 'protocol udp having conn[ports] > 3000'
    parser = rule_parser.RuleParser({}, 'src', s2, default_timerange)
    sql = parser.sql
    assert sql.where == "protocol = 'UDP'"
    assert sql.having == "`conn[ports]` > '3000'"
    assert sql.groupby == 'timestamp, protocol, src'

    s3 = '(port > 16384 and port < 32768) or protocol TCP having dst[hosts] > $threshold'
    parser = rule_parser.RuleParser({'threshold': 100}, 'src', s3, default_timerange)
    sql = parser.sql
    assert sql.where == "( port > '16384' and port < '32768' ) or protocol = 'TCP'"
    assert sql.having == "`dst[hosts]` > '100'"
    assert sql.groupby == 'timestamp, protocol, port, src'


def simple_query(select, from_, where='', groupby='', having='', orderby='', limit=''):
    query = "SELECT {}\nFROM {}".format(select, from_)
    if where:
        query = "{}\nWHERE {}".format(query, where)
    if groupby:
        query = "{}\nGROUP BY {}".format(query, groupby)
    if having:
        query = "{}\nHAVING {}".format(query, having)
    if orderby:
        query = "{}\nORDER BY {}".format(query, orderby)
    if limit:
        query = "{}\nLIMIT {}".format(query, limit)
    return query


def test_timerange():
    s1 = 'having conn[links] > 1000'
    parser = rule_parser.RuleParser({}, 'dst', s1, default_timerange)
    sql = parser.sql
    t_start = datetime(2014, 1, 1)
    t_stop = datetime(2014, 1, 2)
    t_stop_sql = datetime(2014, 1, 1, 23, 59, 59)
    assert sql.get_where() == ""
    sql.set_timerange(t_start, t_stop)
    assert sql.get_where() == "WHERE timestamp BETWEEN {} AND {}".format(web.sqlquote(t_start), web.sqlquote(t_stop_sql))

    s2 = 'protocol UDP'
    parser = rule_parser.RuleParser({}, 'dst', s2, default_timerange)
    sql = parser.sql
    t_start = datetime(2014, 1, 3)
    t_stop = datetime(2014, 1, 4)
    t_stop_sql = datetime(2014, 1, 3, 23, 59, 59)
    assert sql.get_where() == "WHERE protocol = 'UDP'"
    sql.set_timerange(t_start, t_stop)
    assert sql.get_where() == "WHERE timestamp BETWEEN {} AND {} AND (protocol = 'UDP')".format(web.sqlquote(t_start), web.sqlquote(t_stop_sql))

    s3 = 'protocol UDP having conn[links] >1000'
    parser = rule_parser.RuleParser({}, 'dst', s3, default_timerange)
    sql = parser.sql
    t_start = datetime(2014, 1, 5)
    t_stop = datetime(2014, 1, 6)
    t_stop_sql = datetime(2014, 1, 5, 23, 59, 59)
    assert sql.get_where() == "WHERE protocol = 'UDP'"
    sql.set_timerange(t_start, t_stop)
    assert sql.get_where() == "WHERE timestamp BETWEEN {} AND {} AND (protocol = 'UDP')".format(web.sqlquote(t_start), web.sqlquote(t_stop_sql))


def test_valid_sql():
    table = 's{}_ds{}_Links'.format(sub_id, ds_full)
    s1 = 'dst port in [22, 33, 44]'
    s2 = 'protocol udp having conn[ports] > 3000'
    s3 = 'having conn[links] > 1000'
    s4 = '(src host = 1.2.3.4 or dst host = 5.6.7.8) and port = 80'
    s5 = 'host 10.20.30.40 and not (10.24.34.44 or 10.24.34.45)'
    s6 = '(port > 16384 and port < 32768) or protocol TCP having dst[hosts] > $threshold'

    parser = rule_parser.RuleParser({}, 'src', s1, default_timerange)
    sql = parser.sql
    rows = db.query(sql.get_query(table, limit=1))
    assert isinstance(rows, IterBetter)
    t_start = datetime(2014, 1, 5)
    t_stop = datetime(2014, 1, 6)
    sql.set_timerange(t_start, t_stop)
    rows = db.query(sql.get_query(table, limit=1))
    assert isinstance(rows, IterBetter)

    parser = rule_parser.RuleParser({}, 'src', s2, default_timerange)
    sql = parser.sql
    rows = db.query(sql.get_query(table, limit=1))
    assert isinstance(rows, IterBetter)

    parser = rule_parser.RuleParser({}, 'src', s3, default_timerange)
    sql = parser.sql
    rows = db.query(sql.get_query(table, limit=1))
    assert isinstance(rows, IterBetter)

    parser = rule_parser.RuleParser({}, 'src', s4, default_timerange)
    sql = parser.sql
    rows = db.query(sql.get_query(table, limit=1))
    assert isinstance(rows, IterBetter)

    parser = rule_parser.RuleParser({}, 'src', s5, default_timerange)
    sql = parser.sql
    rows = db.query(sql.get_query(table, limit=1))
    assert isinstance(rows, IterBetter)

    parser = rule_parser.RuleParser({'threshold': 100}, 'src', s6, default_timerange)
    sql = parser.sql
    rows = db.query(sql.get_query(table, limit=1))
    assert isinstance(rows, IterBetter)


def test_tcpdump_examples():
    s = 'host sundown'
    parser = rule_parser.RuleParser({}, 'src', s, default_timerange)
    assert parser.where_clauses == [
        ('CLAUSE', {'dir': 'either', 'type': 'host', 'comp': '=', 'value': 'sundown'})
    ]

    s = 'host helios and ( hot or ace )'
    parser = rule_parser.RuleParser({}, 'src', s, default_timerange)
    assert parser.where_clauses == [
        ('CLAUSE', {'dir': 'either', 'type': 'host', 'comp': '=', 'value': 'helios'}),
        ('JOIN', 'and'),
        ('MODIFIER', '('),
        ('CLAUSE', {'dir': 'either', 'type': 'host', 'comp': '=', 'value': 'hot'}),
        ('JOIN', 'or'),
        ('CLAUSE', {'dir': 'either', 'type': 'host', 'comp': '=', 'value': 'ace'}),
        ('MODIFIER', ')'),
    ]

    s = 'ip host ace and not helios'  # all traffic available is IP traffic
    s = 'host ace and not helios'
    parser = rule_parser.RuleParser({}, 'src', s, default_timerange)
    assert parser.where_clauses == [
        ('CLAUSE', {'dir': 'either', 'type': 'host', 'comp': '=', 'value': 'ace'}),
        ('JOIN', 'and'),
        ('MODIFIER', 'not'),
        ('CLAUSE', {'dir': 'either', 'type': 'host', 'comp': '=', 'value': 'helios'}),
    ]

    s = 'net ucb-ether'  # 'net' is not supported in SAM
    s = 'gateway snup and (port ftp or ftp-data)'  # 'gateway' is not supported in SAM
    s = 'ip and not net localnet'  # 'localnet' is not supported in SAM
    s = 'tcp[tcpflags] & (tcp-syn|tcp-fin) != 0 and not src and dst net localnet'  # tcp flags haven't been retained by SAM
    s = 'tcp port 80 and (((ip[2:2] - ((ip[0]&0xf)<<2)) - ((tcp[12]&0xf0)>>2)) != 0)'  # no packet data has been retained by SAM
    s = 'gateway snup and ip[2:2] > 576'  # 'gateway' is not supported in SAM
    s = 'ether[0] & 1 = 0 and ip[16] >= 224'  # distinguising networks is not supported
    s = 'icmp[icmptype] != icmp-echo and icmp[icmptype] != icmp-echoreply'  # icmp details are not stored by SAM


def test_rate_ports():
    l_model = Links(db, sub_id, ds_temp)
    l_model.delete_connections()
    assert len(l_model.get_all_endpoints()) == 0

    #insert some link data into ds_temp
    loader = BaseImporter()
    loader.set_subscription(sub_id)
    loader.set_datasource_id(ds_temp)
    processor = Preprocessor(db, sub_id, ds_temp, security_rules=False)
    A = common.IPStringtoInt('110.20.30.40')
    D = common.IPStringtoInt('110.20.32.43')
    log_lines = [
        [A, 12345, D, 120, datetime(2017, 1, 2, 5, 30,  0), 'UDP', 1000, 500, 4, 4, 3],
        [A, 12345, D, 121, datetime(2017, 1, 2, 5, 30, 30), 'UDP', 1000, 500, 4, 4, 3],
        [A, 12345, D, 122, datetime(2017, 1, 2, 5, 31,  0), 'UDP', 1000, 500, 4, 4, 3],
        [A, 12345, D, 123, datetime(2017, 1, 2, 5, 31, 30), 'UDP', 1000, 500, 4, 4, 3],
        [A, 12345, D, 124, datetime(2017, 1, 2, 5, 32,  0), 'UDP', 1000, 500, 4, 4, 3],

        [A, 12345, D, 125, datetime(2017, 1, 2, 5, 35, 0), 'UDP', 1000, 500, 4, 4, 3],
        [A, 12345, D, 126, datetime(2017, 1, 2, 5, 35, 30), 'UDP', 1000, 500, 4, 4, 3],
        [A, 12345, D, 127, datetime(2017, 1, 2, 5, 36, 0), 'UDP', 1000, 500, 4, 4, 3],
        [A, 12345, D, 123, datetime(2017, 1, 2, 5, 36, 30), 'UDP', 1000, 500, 4, 4, 3],
        [A, 12345, D, 124, datetime(2017, 1, 2, 5, 37,  0), 'UDP', 1000, 500, 4, 4, 3],
        [A, 12345, D, 125, datetime(2017, 1, 2, 5, 37, 30), 'UDP', 1000, 500, 4, 4, 3],
        [A, 12345, D, 126, datetime(2017, 1, 2, 5, 38,  0), 'UDP', 1000, 500, 4, 4, 3],
        [A, 12345, D, 127, datetime(2017, 1, 2, 5, 38, 30), 'UDP', 1000, 500, 4, 4, 3],
        [A, 12345, D, 123, datetime(2017, 1, 2, 5, 39,  0), 'UDP', 1000, 500, 4, 4, 3],
        [A, 12345, D, 122, datetime(2017, 1, 2, 5, 39, 30), 'UDP', 1000, 500, 4, 4, 3],
    ]
    rows = [dict(zip(loader.keys, entry)) for entry in log_lines]
    count = len(rows)
    loader.insert_data(rows, count)
    processor.run_all()
    assert len(l_model.get_all_endpoints()) == 2

    # rule and job to test
    # A connects to 5 distinct ports between 5:30 and 5:35
    # A connects to 6 distinct ports between 5:35 and 5:40
    # A connects to 8 distinct ports between 5:30 and 5:40 (but period rules apply to 5-min segments)
    t30 = datetime(2017,1,2,5,30,0)
    t35 = datetime(2017,1,2,5,35,0)
    t40 = datetime(2017,1,2,5,40,0)
    rp = ruling_process.RulesProcessor(db)
    rule1 = rule.Rule(3, True, 'test_rule3', 'test_rule3_desc', 'portscan.yml')
    rule1.set_exposed_params({'threshold': '4'})
    job1 = ruling_process.RuleJob(sub_id, ds_temp, t30, t35, [rule1])
    alerts = rp.evaluate_periodic_rule(job1, rule1)
    assert len(alerts) == 1
    rule1.set_exposed_params({'threshold': '4'})
    job1 = ruling_process.RuleJob(sub_id, ds_temp, t35, t40, [rule1])
    alerts = rp.evaluate_periodic_rule(job1, rule1)
    assert len(alerts) == 1
    rule1.set_exposed_params({'threshold': '4'})
    job1 = ruling_process.RuleJob(sub_id, ds_temp, t30, t40, [rule1])
    alerts = rp.evaluate_periodic_rule(job1, rule1)
    assert len(alerts) == 2

    rule1.set_exposed_params({'threshold': '5'})
    job1 = ruling_process.RuleJob(sub_id, ds_temp, t30, t35, [rule1])
    alerts = rp.evaluate_periodic_rule(job1, rule1)
    assert len(alerts) == 0
    rule1.set_exposed_params({'threshold': '5'})
    job1 = ruling_process.RuleJob(sub_id, ds_temp, t35, t40, [rule1])
    alerts = rp.evaluate_periodic_rule(job1, rule1)
    assert len(alerts) == 1
    rule1.set_exposed_params({'threshold': '5'})
    job1 = ruling_process.RuleJob(sub_id, ds_temp, t30, t40, [rule1])
    alerts = rp.evaluate_periodic_rule(job1, rule1)
    assert len(alerts) == 1

    rule1.set_exposed_params({'threshold': '6'})
    job1 = ruling_process.RuleJob(sub_id, ds_temp, t30, t35, [rule1])
    alerts = rp.evaluate_periodic_rule(job1, rule1)
    assert len(alerts) == 0
    rule1.set_exposed_params({'threshold': '6'})
    job1 = ruling_process.RuleJob(sub_id, ds_temp, t35, t40, [rule1])
    alerts = rp.evaluate_periodic_rule(job1, rule1)
    assert len(alerts) == 0
    rule1.set_exposed_params({'threshold': '6'})
    job1 = ruling_process.RuleJob(sub_id, ds_temp, t30, t40, [rule1])
    alerts = rp.evaluate_periodic_rule(job1, rule1)
    assert len(alerts) == 0

    #remove temp data
    l_model.delete_connections()
    assert len(l_model.get_all_endpoints()) == 0


def test_rate_nets():
    l_model = Links(db, sub_id, ds_temp)
    l_model.delete_connections()
    assert len(l_model.get_all_endpoints()) == 0

    #insert some link data into ds_temp
    loader = BaseImporter()
    loader.set_subscription(sub_id)
    loader.set_datasource_id(ds_temp)
    processor = Preprocessor(db, sub_id, ds_temp, security_rules=False)
    A = common.IPStringtoInt('110.20.30.40')
    B = common.IPStringtoInt('110.20.30.41')
    C = common.IPStringtoInt('110.20.32.42')
    D = common.IPStringtoInt('110.20.32.43')
    E = common.IPStringtoInt('110.24.34.44')
    F = common.IPStringtoInt('110.24.34.45')
    log_lines = [
        [A, 12345, B, 80, datetime(2017, 1, 2, 5, 30, 0), 'TCP', 1000, 500, 4, 4, 3],
        [A, 12345, C, 80, datetime(2017, 1, 2, 5, 31, 0), 'TCP', 1000, 500, 4, 4, 3],
        [A, 12345, D, 80, datetime(2017, 1, 2, 5, 32, 0), 'TCP', 1000, 500, 4, 4, 3],
        [A, 12345, E, 80, datetime(2017, 1, 2, 5, 33, 0), 'TCP', 1000, 500, 4, 4, 3],
        [A, 12345, F, 80, datetime(2017, 1, 2, 5, 34, 0), 'TCP', 1000, 500, 4, 4, 3],

        [A, 12345, B, 80, datetime(2017, 1, 2, 5, 35, 0), 'TCP', 1000, 500, 4, 4, 3],
        [A, 12345, C, 80, datetime(2017, 1, 2, 5, 36, 0), 'TCP', 1000, 500, 4, 4, 3],
        [A, 12345, D, 80, datetime(2017, 1, 2, 5, 37, 0), 'TCP', 1000, 500, 4, 4, 3],
        [A, 12345, E, 80, datetime(2017, 1, 2, 5, 38, 0), 'TCP', 1000, 500, 4, 4, 3],

        [A, 12345, B, 80, datetime(2017, 1, 2, 5, 40, 0), 'TCP', 1000, 500, 4, 4, 3],
        [A, 12345, C, 80, datetime(2017, 1, 2, 5, 42, 0), 'TCP', 1000, 500, 4, 4, 3],
        [A, 12345, D, 80, datetime(2017, 1, 2, 5, 44, 0), 'TCP', 1000, 500, 4, 4, 3],

        [A, 12345, B, 80, datetime(2017, 1, 2, 5, 45, 0), 'TCP', 1000, 500, 4, 4, 3],
        [A, 12345, C, 80, datetime(2017, 1, 2, 5, 48, 0), 'TCP', 1000, 500, 4, 4, 3],

        [A, 12345, B, 80, datetime(2017, 1, 2, 5, 50, 0), 'TCP', 1000, 500, 4, 4, 3],
    ]
    rows = [dict(zip(loader.keys, entry)) for entry in log_lines]
    count = len(rows)
    loader.insert_data(rows, count)
    processor.run_all()
    assert len(l_model.get_all_endpoints()) == 6

    # rule and job to test
    # A connects to 5 distinct ports between 5:30 and 5:35
    # A connects to 6 distinct ports between 5:35 and 5:40
    # A connects to 8 distinct ports between 5:30 and 5:40 (but period rules apply to 5-min segments)
    t30 = datetime(2017,1,2,5,30,0)
    t35 = datetime(2017,1,2,5,35,0)
    t40 = datetime(2017,1,2,5,40,0)
    t45 = datetime(2017,1,2,5,45,0)
    t50 = datetime(2017,1,2,5,50,0)
    t55 = datetime(2017,1,2,5,50,0)
    t60 = datetime(2017,1,2,6,00,0)
    rp = ruling_process.RulesProcessor(db)
    rule1 = rule.Rule(3, True, 'test_rule3', 'test_rule3_desc', 'netscan.yml')
    rule1.set_exposed_params({'threshold': '3'})
    job1 = ruling_process.RuleJob(sub_id, ds_temp, t30, t35, [rule1])
    alerts = rp.evaluate_periodic_rule(job1, rule1)
    assert len(alerts) == 1
    rule1.set_exposed_params({'threshold': '3'})
    job1 = ruling_process.RuleJob(sub_id, ds_temp, t40, t45, [rule1])
    alerts = rp.evaluate_periodic_rule(job1, rule1)
    assert len(alerts) == 0
    rule1.set_exposed_params({'threshold': '3'})
    job1 = ruling_process.RuleJob(sub_id, ds_temp, t30, t55, [rule1])
    alerts = rp.evaluate_periodic_rule(job1, rule1)
    assert len(alerts) == 2

    rule1.set_exposed_params({'threshold': '1'})
    job1 = ruling_process.RuleJob(sub_id, ds_temp, t30, t45, [rule1])
    alerts = rp.evaluate_periodic_rule(job1, rule1)
    assert len(alerts) == 3
    rule1.set_exposed_params({'threshold': '1'})
    job1 = ruling_process.RuleJob(sub_id, ds_temp, t45, t55, [rule1])
    alerts = rp.evaluate_periodic_rule(job1, rule1)
    assert len(alerts) == 1
    rule1.set_exposed_params({'threshold': '1'})
    job1 = ruling_process.RuleJob(sub_id, ds_temp, t50, t60, [rule1])
    alerts = rp.evaluate_periodic_rule(job1, rule1)
    assert len(alerts) == 0
    rule1.set_exposed_params({'threshold': '1'})
    job1 = ruling_process.RuleJob(sub_id, ds_temp, t30, t60, [rule1])
    alerts = rp.evaluate_periodic_rule(job1, rule1)
    assert len(alerts) == 4

    #remove temp data
    l_model.delete_connections()
    assert len(l_model.get_all_endpoints()) == 0

def test_rate_ddos():
    l_model = Links(db, sub_id, ds_temp)
    l_model.delete_connections()
    assert len(l_model.get_all_endpoints()) == 0

    #insert some link data into ds_temp
    loader = BaseImporter()
    loader.set_subscription(sub_id)
    loader.set_datasource_id(ds_temp)
    processor = Preprocessor(db, sub_id, ds_temp, security_rules=False)
    A = common.IPStringtoInt('110.20.30.40')
    B = common.IPStringtoInt('110.24.34.45')
    log_lines = [
        [A, 12345, B, 80, datetime(2017, 1, 2, 5, 30, 0), 'TCP', 1000, 500, 4, 4, 3],
        [A, 12345, B, 80, datetime(2017, 1, 2, 5, 31, 0), 'TCP', 1000, 500, 4, 4, 3],
        [A, 12345, B, 80, datetime(2017, 1, 2, 5, 32, 0), 'TCP', 1000, 500, 4, 4, 3],
        [A, 12345, B, 80, datetime(2017, 1, 2, 5, 33, 0), 'TCP', 1000, 500, 4, 4, 3],
        [A, 12345, B, 80, datetime(2017, 1, 2, 5, 34, 0), 'TCP', 1000, 500, 4, 4, 3],

        [A, 12345, B, 80, datetime(2017, 1, 2, 5, 35, 0), 'TCP', 1000, 500, 4, 4, 3],
        [A, 12345, B, 80, datetime(2017, 1, 2, 5, 36, 0), 'TCP', 1000, 500, 4, 4, 3],
        [A, 12345, B, 80, datetime(2017, 1, 2, 5, 37, 0), 'TCP', 1000, 500, 4, 4, 3],
        [A, 12345, B, 80, datetime(2017, 1, 2, 5, 38, 0), 'TCP', 1000, 500, 4, 4, 3],

        [A, 12345, B, 80, datetime(2017, 1, 2, 5, 40, 0), 'TCP', 1000, 500, 4, 4, 3],
        [A, 12345, B, 80, datetime(2017, 1, 2, 5, 42, 0), 'TCP', 1000, 500, 4, 4, 3],
        [A, 12345, B, 80, datetime(2017, 1, 2, 5, 44, 0), 'TCP', 1000, 500, 4, 4, 3],

        [A, 12345, B, 80, datetime(2017, 1, 2, 5, 45, 0), 'TCP', 1000, 500, 4, 4, 3],
        [A, 12345, B, 80, datetime(2017, 1, 2, 5, 48, 0), 'TCP', 1000, 500, 4, 4, 3],

        [A, 12345, B, 80, datetime(2017, 1, 2, 5, 50, 0), 'TCP', 1000, 500, 4, 4, 3],
    ]
    rows = [dict(zip(loader.keys, entry)) for entry in log_lines]
    count = len(rows)
    loader.insert_data(rows, count)
    processor.run_all()
    assert len(l_model.get_all_endpoints()) == 2

    # rule and job to test
    # A connects to 5 distinct ports between 5:30 and 5:35
    # A connects to 6 distinct ports between 5:35 and 5:40
    # A connects to 8 distinct ports between 5:30 and 5:40 (but period rules apply to 5-min segments)
    t30 = datetime(2017,1,2,5,30,0)
    t35 = datetime(2017,1,2,5,35,0)
    t40 = datetime(2017,1,2,5,40,0)
    t45 = datetime(2017,1,2,5,45,0)
    t50 = datetime(2017,1,2,5,50,0)
    t55 = datetime(2017,1,2,5,50,0)
    t60 = datetime(2017,1,2,6,00,0)
    rp = ruling_process.RulesProcessor(db)
    rule1 = rule.Rule(3, True, 'test_rule3', 'test_rule3_desc', 'dos.yml')
    rule1.set_exposed_params({'threshold': '3'})
    job1 = ruling_process.RuleJob(sub_id, ds_temp, t30, t35, [rule1])
    alerts = rp.evaluate_periodic_rule(job1, rule1)
    assert len(alerts) == 1
    rule1.set_exposed_params({'threshold': '3'})
    job1 = ruling_process.RuleJob(sub_id, ds_temp, t40, t45, [rule1])
    alerts = rp.evaluate_periodic_rule(job1, rule1)
    assert len(alerts) == 0
    rule1.set_exposed_params({'threshold': '3'})
    job1 = ruling_process.RuleJob(sub_id, ds_temp, t30, t55, [rule1])
    alerts = rp.evaluate_periodic_rule(job1, rule1)
    assert len(alerts) == 2

    rule1.set_exposed_params({'threshold': '1'})
    job1 = ruling_process.RuleJob(sub_id, ds_temp, t30, t45, [rule1])
    alerts = rp.evaluate_periodic_rule(job1, rule1)
    assert len(alerts) == 3
    rule1.set_exposed_params({'threshold': '1'})
    job1 = ruling_process.RuleJob(sub_id, ds_temp, t45, t55, [rule1])
    alerts = rp.evaluate_periodic_rule(job1, rule1)
    assert len(alerts) == 1
    rule1.set_exposed_params({'threshold': '1'})
    job1 = ruling_process.RuleJob(sub_id, ds_temp, t50, t60, [rule1])
    alerts = rp.evaluate_periodic_rule(job1, rule1)
    assert len(alerts) == 0
    rule1.set_exposed_params({'threshold': '1'})
    job1 = ruling_process.RuleJob(sub_id, ds_temp, t30, t60, [rule1])
    alerts = rp.evaluate_periodic_rule(job1, rule1)
    assert len(alerts) == 4

    #remove temp data
    l_model.delete_connections()
    assert len(l_model.get_all_endpoints()) == 0