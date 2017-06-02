import pytest
from sam.models import rule_parser


def test_tokenize_simple():
    s1 = 'src host = 1.2.3.4'

    parser = rule_parser.RuleParser({}, 'src', s1)
    assert parser.where_clauses == [('CLAUSE', {'comp': '=', 'dir': 'src', 'type': 'host', 'value': '1.2.3.4'})]
    assert parser.having_clauses == []

    s2 = 'src port = 51223'
    parser = rule_parser.RuleParser({}, 'src', s2)
    assert parser.where_clauses == [('CLAUSE', {'comp': '=', 'dir': 'src', 'type': 'port', 'value': '51223'})]
    assert parser.having_clauses == []

    s3 = 'dst host = 1.2.3.4'
    parser = rule_parser.RuleParser({}, 'src', s3)
    assert parser.where_clauses == [('CLAUSE', {'comp': '=', 'dir': 'dst', 'type': 'host', 'value': '1.2.3.4'})]
    assert parser.having_clauses == []

    s4 = 'dst port = 443'
    parser = rule_parser.RuleParser({}, 'src', s4)
    assert parser.where_clauses == [('CLAUSE', {'comp': '=', 'dir': 'dst', 'type': 'port', 'value': '443'})]
    assert parser.having_clauses == []

    s5 = 'host = 1.2.3.4'
    parser = rule_parser.RuleParser({}, 'src', s5)
    assert parser.where_clauses == [('CLAUSE', {'comp': '=', 'dir': 'either', 'type': 'host', 'value': '1.2.3.4'})]
    assert parser.having_clauses == []

    s6 = 'host 1.2.3.4'
    parser = rule_parser.RuleParser({}, 'src', s6)
    assert parser.where_clauses == [('CLAUSE', {'comp': '=', 'dir': 'either', 'type': 'host', 'value': '1.2.3.4'})]
    assert parser.having_clauses == []

    s7 = 'src host 1.2.3.4'
    parser = rule_parser.RuleParser({}, 'src', s7)
    assert parser.where_clauses == [('CLAUSE', {'comp': '=', 'dir': 'src', 'type': 'host', 'value': '1.2.3.4'})]
    assert parser.having_clauses == []

    s8 = '1.2.3.4'
    parser = rule_parser.RuleParser({}, 'src', s8)
    assert parser.where_clauses == [('CLAUSE', {'comp': '=', 'dir': 'either', 'type': 'host', 'value': '1.2.3.4'})]
    assert parser.having_clauses == []

    s9 = 'dst 1.2.3.4'
    parser = rule_parser.RuleParser({}, 'src', s9)
    assert parser.where_clauses == [('CLAUSE', {'comp': '=', 'dir': 'dst', 'type': 'host', 'value': '1.2.3.4'})]
    assert parser.having_clauses == []

    s10 = 'port 443'
    parser = rule_parser.RuleParser({}, 'src', s10)
    assert parser.where_clauses == [('CLAUSE', {'comp': '=', 'dir': 'either', 'type': 'port', 'value': '443'})]
    assert parser.having_clauses == []


def test_tokenize_lists():
    s1 = 'src host in [1, 2, 3, 4]'
    parser = rule_parser.RuleParser({}, 'src', s1)
    assert parser.where_clauses == [('CLAUSE', {'comp': 'in', 'dir': 'src', 'type': 'host', 'value': list('1234')})]

    s2 = 'src host in (5 ,6 ,7 , 8)'
    parser = rule_parser.RuleParser({}, 'src', s2)
    assert parser.where_clauses == [('CLAUSE', {'comp': 'in', 'dir': 'src', 'type': 'host', 'value': list('5678')})]

    s3 = 'src host in (9)'
    parser = rule_parser.RuleParser({}, 'src', s3)
    assert parser.where_clauses == [('CLAUSE', {'comp': 'in', 'dir': 'src', 'type': 'host', 'value': list('9')})]

    s4 = 'src host in [0]'
    parser = rule_parser.RuleParser({}, 'src', s4)
    assert parser.where_clauses == [('CLAUSE', {'comp': 'in', 'dir': 'src', 'type': 'host', 'value': list('0')})]

    s5 = 'dst port in $ports'
    tr = {'ports': [22, 33, 44, 55]}
    parser = rule_parser.RuleParser(tr, 'src', s5)
    assert parser.where_clauses == [('CLAUSE',
                                     {'comp': 'in', 'dir': 'dst', 'type': 'port', 'value': ['22', '33', '44', '55']})]

    tr = {'ports': (22, 33, 44, 55)}
    parser = rule_parser.RuleParser(tr, 'src', s5)
    assert parser.where_clauses == [('CLAUSE',
                                     {'comp': 'in', 'dir': 'dst', 'type': 'port', 'value': ['22', '33', '44', '55']})]

    tr = {'ports': '(22, 33, 44, 55)'}
    parser = rule_parser.RuleParser(tr, 'src', s5)
    assert parser.where_clauses == [('CLAUSE',
                                     {'comp': 'in', 'dir': 'dst', 'type': 'port', 'value': ['22', '33', '44', '55']})]


def test_tokenize_replacements():
    s1 = '$place'
    tr = {'place': 'hello'}
    parser = rule_parser.RuleParser(tr, 'src', s1)
    assert parser.tokens == [('LITERAL', 'hello')]

    tr = {'place': 42}
    parser = rule_parser.RuleParser(tr, 'src', s1)
    assert parser.tokens == [('LITERAL', '42')]

    s2 = 'host in $place'
    tr = {'place': [1, 2, 3]}
    parser = rule_parser.RuleParser(tr, 'src', s2)
    assert parser.tokens == [('TYPE', 'host'), ('LIST', 'in'), ('LIT_LIST', ['1', '2', '3'])]

    s2 = 'host in $place'
    tr = {'place': "(1 ,2 , 3)"}
    parser = rule_parser.RuleParser(tr, 'src', s2)
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
    parser = rule_parser.RuleParser({}, 'src', s1)
    assert parser.where_clauses == [
        ('CLAUSE', {'dir': 'src', 'type': 'port', 'comp': '=', 'value': '12345'}),
        ('JOIN', 'and'),
        ('CLAUSE', {'dir': 'dst', 'type': 'port', 'comp': '=', 'value': '80'}),
    ]
    assert parser.having_clauses == []

    s2 = 'src port 12345 or dst port 80'
    parser = rule_parser.RuleParser({}, 'src', s2)
    assert parser.where_clauses == [
        ('CLAUSE', {'dir': 'src', 'type': 'port', 'comp': '=', 'value': '12345'}),
        ('JOIN', 'or'),
        ('CLAUSE', {'dir': 'dst', 'type': 'port', 'comp': '=', 'value': '80'}),
    ]
    assert parser.having_clauses == []

    s2 = 'dst port 80 or dst port 80 and dst port 80 or dst port 80 and dst port 80'
    parser = rule_parser.RuleParser({}, 'src', s2)
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
    parser = rule_parser.RuleParser({}, 'src', s1)
    assert parser.where_clauses == [
        ('CLAUSE', {'dir': 'dst', 'type': 'port', 'comp': 'not in', 'value': ['22', '33', '44']})
    ]
    assert parser.having_clauses == []

    s2 = 'dst port != 443'
    parser = rule_parser.RuleParser({}, 'src', s2)
    assert parser.where_clauses == [
        ('CLAUSE', {'dir': 'dst', 'type': 'port', 'comp': '!=', 'value': '443'})
    ]
    assert parser.having_clauses == []

    s3 = 'not dst port = 443'
    parser = rule_parser.RuleParser({}, 'src', s3)
    assert parser.where_clauses == [
        ('MODIFIER', 'not'),
        ('CLAUSE', {'dir': 'dst', 'type': 'port', 'comp': '=', 'value': '443'})
    ]
    assert parser.having_clauses == []

    s4 = 'not dst port not in (22, 33, 44)'
    parser = rule_parser.RuleParser({}, 'src', s4)
    assert parser.where_clauses == [
        ('MODIFIER', 'not'),
        ('CLAUSE', {'dir': 'dst', 'type': 'port', 'comp': 'not in', 'value': ['22', '33', '44']})
    ]
    assert parser.having_clauses == []


def test_parens():
    s = '(dst port < 500)'
    parser = rule_parser.RuleParser({}, 'src', s)
    assert parser.where_clauses == [
        ('MODIFIER', '('),
        ('CLAUSE', {'dir': 'dst', 'type': 'port', 'comp': '<', 'value': '500'}),
        ('MODIFIER', ')'),
    ]

    s = '((dst port < 500))'
    parser = rule_parser.RuleParser({}, 'src', s)
    assert parser.where_clauses == [
        ('MODIFIER', '('),
        ('MODIFIER', '('),
        ('CLAUSE', {'dir': 'dst', 'type': 'port', 'comp': '<', 'value': '500'}),
        ('MODIFIER', ')'),
        ('MODIFIER', ')'),
    ]

    s = 'dst port < 500)'
    with pytest.raises(rule_parser.RuleParseError):
        parser = rule_parser.RuleParser({}, 'src', s)

    s = '(dst port < 500'
    with pytest.raises(rule_parser.RuleParseError):
        parser = rule_parser.RuleParser({}, 'src', s)

    s = 'dst port < 500)('
    with pytest.raises(rule_parser.RuleParseError):
        parser = rule_parser.RuleParser({}, 'src', s)

    s = 'dst port < 500()'
    with pytest.raises(rule_parser.RuleParseError):
        parser = rule_parser.RuleParser({}, 'src', s)


def test_aggregates():
    s1 = 'having dst[ports] > 300'
    parser = rule_parser.RuleParser({}, 'src', s1)
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
    parser = rule_parser.RuleParser({}, 'src', s2)
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


def test_sql():
    s1 = 'src host = 1.2.3.4'
    parser = rule_parser.RuleParser({}, 'src', s1)
    sql = parser.sql
    assert sql.where == 'src = 16909060'

    s2 = 'src host in [1.2.3.4, 10.20.30.40, 100.200.50.150]'
    parser = rule_parser.RuleParser({}, 'src', s2)
    sql = parser.sql
    assert sql.where == 'src in (16909060,169090600,1690841750)'

    s3 = 'dst port in [22, 33, 44]'
    parser = rule_parser.RuleParser({}, 'src', s3)
    sql = parser.sql
    assert sql.where == 'port in (22,33,44)'

    s4 = 'dst port = 5'
    parser = rule_parser.RuleParser({}, 'src', s4)
    sql = parser.sql
    assert sql.where == 'port = 5'

    s5 = '(src host = 1.2.3.4 or dst host = 5.6.7.8) and port = 80'
    parser = rule_parser.RuleParser({}, 'src', s5)
    sql = parser.sql
    assert sql.where == '( src = 16909060 or dst = 84281096 ) and port = 80'

    s6 = 'host 10.20.30.40 and not (10.24.34.44 or 10.24.34.45)'
    parser = rule_parser.RuleParser({}, 'src', s6)
    sql = parser.sql
    assert sql.where == '(dst = 169090600 or src = 169090600) and not ' \
                        '( (dst = 169353772 or src = 169353772) or (dst = 169353773 or src = 169353773) )'


def test_tcpdump_examples():
    s = 'host sundown'
    parser = rule_parser.RuleParser({}, 'src', s)
    assert parser.where_clauses == [
        ('CLAUSE', {'dir': 'either', 'type': 'host', 'comp': '=', 'value': 'sundown'})
    ]

    s = 'host helios and ( hot or ace )'
    parser = rule_parser.RuleParser({}, 'src', s)
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
    parser = rule_parser.RuleParser({}, 'src', s)
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
    s = 'tcp port 80 and (((ip[2:2] - ((ip[0]&0xf)<<2)) - ((tcp[12]&0xf0)>>2)) != 0)'  # no data has been retained by SAM
    s = 'gateway snup and ip[2:2] > 576'  # 'gateway' is not supported in SAM
    s = 'ether[0] & 1 = 0 and ip[16] >= 224'  #
    s = 'icmp[icmptype] != icmp-echo and icmp[icmptype] != icmp-echoreply'  # icmp details are not stored by SAM
