import pytest
from sam.models import rule_parser


def test_tokenize_simple():
    s1 = 'src host = 1.2.3.4'

    parser = rule_parser.RuleParser({}, s1)
    assert parser.clauses == [('CLAUSE', {'comp': '=', 'dir_': 'src', 'type': 'host', 'value': '1.2.3.4'})]

    s2 = 'src port = 51223'
    parser = rule_parser.RuleParser({}, s2)
    assert parser.clauses == [('CLAUSE', {'comp': '=', 'dir_': 'src', 'type': 'port', 'value': '51223'})]

    s3 = 'dst host = 1.2.3.4'
    parser = rule_parser.RuleParser({}, s3)
    assert parser.clauses == [('CLAUSE', {'comp': '=', 'dir_': 'dst', 'type': 'host', 'value': '1.2.3.4'})]

    s4 = 'dst port = 443'
    parser = rule_parser.RuleParser({}, s4)
    assert parser.clauses == [('CLAUSE', {'comp': '=', 'dir_': 'dst', 'type': 'port', 'value': '443'})]

    s5 = 'host = 1.2.3.4'
    parser = rule_parser.RuleParser({}, s5)
    assert parser.clauses == [('CLAUSE', {'comp': '=', 'dir_': 'either', 'type': 'host', 'value': '1.2.3.4'})]

    s6 = 'host 1.2.3.4'
    parser = rule_parser.RuleParser({}, s6)
    assert parser.clauses == [('CLAUSE', {'comp': '=', 'dir_': 'either', 'type': 'host', 'value': '1.2.3.4'})]

    s7 = 'src host 1.2.3.4'
    parser = rule_parser.RuleParser({}, s7)
    assert parser.clauses == [('CLAUSE', {'comp': '=', 'dir_': 'src', 'type': 'host', 'value': '1.2.3.4'})]

    s8 = '1.2.3.4'
    parser = rule_parser.RuleParser({}, s8)
    assert parser.clauses == [('CLAUSE', {'comp': '=', 'dir_': 'either', 'type': 'host', 'value': '1.2.3.4'})]

    s9 = 'dst 1.2.3.4'
    parser = rule_parser.RuleParser({}, s9)
    assert parser.clauses == [('CLAUSE', {'comp': '=', 'dir_': 'dst', 'type': 'host', 'value': '1.2.3.4'})]

    s10 = 'port 443'
    parser = rule_parser.RuleParser({}, s10)
    assert parser.clauses == [('CLAUSE', {'comp': '=', 'dir_': 'either', 'type': 'port', 'value': '443'})]


def test_tokenize_lists():
    s1 = 'src host in [1, 2, 3, 4]'
    parser = rule_parser.RuleParser({}, s1)
    assert parser.clauses == [('CLAUSE', {'comp': 'in', 'dir_': 'src', 'type': 'host', 'value': list('1234')})]

    s2 = 'src host in (5 ,6 ,7 , 8)'
    parser = rule_parser.RuleParser({}, s2)
    assert parser.clauses == [('CLAUSE', {'comp': 'in', 'dir_': 'src', 'type': 'host', 'value': list('5678')})]

    s3 = 'src host in (9)'
    parser = rule_parser.RuleParser({}, s3)
    assert parser.clauses == [('CLAUSE', {'comp': 'in', 'dir_': 'src', 'type': 'host', 'value': list('9')})]

    s4 = 'src host in [0]'
    parser = rule_parser.RuleParser({}, s4)
    assert parser.clauses == [('CLAUSE', {'comp': 'in', 'dir_': 'src', 'type': 'host', 'value': list('0')})]

    s5 = 'dst port in $ports'
    tr = {
        'ports': [22, 33, 44, 55]
    }
    parser = rule_parser.RuleParser(tr, s5)
    assert parser.clauses == [('CLAUSE', {'comp': 'in', 'dir_': 'dst', 'type': 'port', 'value': ['22','33','44','55']})]

    tr = {
        'ports': (22, 33, 44, 55)
    }
    parser = rule_parser.RuleParser(tr, s5)
    assert parser.clauses == [('CLAUSE', {'comp': 'in', 'dir_': 'dst', 'type': 'port', 'value': ['22','33','44','55']})]

    tr = {
        'ports': '(22, 33, 44, 55)'
    }
    parser = rule_parser.RuleParser(tr, s5)
    assert parser.clauses == [('CLAUSE', {'comp': 'in', 'dir_': 'dst', 'type': 'port', 'value': ['22','33','44','55']})]


def test_tokenize_replacements():
    s1 = '$place'
    tr = {'place': 'hello'}
    parser = rule_parser.RuleParser(tr, s1)
    assert parser.tokens == [('LITERAL', 'hello')]

    tr = {'place': 42}
    parser = rule_parser.RuleParser(tr, s1)
    assert parser.tokens == [('LITERAL', '42')]

    s2 = 'host in $place'
    tr = {'place': [1, 2, 3]}
    parser = rule_parser.RuleParser(tr, s2)
    assert parser.tokens == [('TYPE', 'host'), ('LIST', 'in'), ('LIT_LIST', ['1', '2', '3'])]

    s2 = 'host in $place'
    tr = {'place': "(1 ,2 , 3)"}
    parser = rule_parser.RuleParser(tr, s2)
    assert parser.tokens == [('TYPE', 'host'), ('LIST', 'in'), ('LIT_LIST', ['1', '2', '3'])]


def test_joins():
    s1 = 'src port 12345 and dst port 80'
    parser = rule_parser.RuleParser({}, s1)
    assert parser.clauses == [
        ('CLAUSE', {'dir_': 'src', 'type': 'port', 'comp': '=', 'value': '12345'}),
        ('JOIN', 'and'),
        ('CLAUSE', {'dir_': 'dst', 'type': 'port', 'comp': '=', 'value': '80'}),
    ]

    s2 = 'src port 12345 or dst port 80'
    parser = rule_parser.RuleParser({}, s2)
    assert parser.clauses == [
        ('CLAUSE', {'dir_': 'src', 'type': 'port', 'comp': '=', 'value': '12345'}),
        ('JOIN', 'or'),
        ('CLAUSE', {'dir_': 'dst', 'type': 'port', 'comp': '=', 'value': '80'}),
    ]

    s2 = 'dst port 80 or dst port 80 and dst port 80 or dst port 80 and dst port 80'
    parser = rule_parser.RuleParser({}, s2)
    assert parser.clauses == [
        ('CLAUSE', {'dir_': 'dst', 'type': 'port', 'comp': '=', 'value': '80'}),
        ('JOIN', 'or'),
        ('CLAUSE', {'dir_': 'dst', 'type': 'port', 'comp': '=', 'value': '80'}),
        ('JOIN', 'and'),
        ('CLAUSE', {'dir_': 'dst', 'type': 'port', 'comp': '=', 'value': '80'}),
        ('JOIN', 'or'),
        ('CLAUSE', {'dir_': 'dst', 'type': 'port', 'comp': '=', 'value': '80'}),
        ('JOIN', 'and'),
        ('CLAUSE', {'dir_': 'dst', 'type': 'port', 'comp': '=', 'value': '80'}),
    ]


def test_negation():
    s1 = 'dst port not in (22, 33, 44)'
    parser = rule_parser.RuleParser({}, s1)
    assert parser.clauses == [
        ('CLAUSE', {'dir_': 'dst', 'type': 'port', 'comp': 'not in', 'value': ['22', '33', '44']})
    ]

    s2 = 'dst port != 443'
    parser = rule_parser.RuleParser({}, s2)
    assert parser.clauses == [
        ('CLAUSE', {'dir_': 'dst', 'type': 'port', 'comp': '!=', 'value': '443'})
    ]

    s3 = 'not dst port = 443'
    parser = rule_parser.RuleParser({}, s3)
    assert parser.clauses == [
        ('MODIFIER', 'not'),
        ('CLAUSE', {'dir_': 'dst', 'type': 'port', 'comp': '=', 'value': '443'})
    ]

    s4 = 'not dst port not in (22, 33, 44)'
    parser = rule_parser.RuleParser({}, s4)
    assert parser.clauses == [
        ('MODIFIER', 'not'),
        ('CLAUSE', {'dir_': 'dst', 'type': 'port', 'comp': 'not in', 'value': ['22', '33', '44']})
    ]


def test_parens():
    s = '(dst port < 500)'
    parser = rule_parser.RuleParser({}, s)
    assert parser.clauses == [
        ('MODIFIER', '('),
        ('CLAUSE', {'dir_': 'dst', 'type': 'port', 'comp': '<', 'value': '500'}),
        ('MODIFIER', ')'),
    ]

    s = '((dst port < 500))'
    parser = rule_parser.RuleParser({}, s)
    assert parser.clauses == [
        ('MODIFIER', '('),
        ('MODIFIER', '('),
        ('CLAUSE', {'dir_': 'dst', 'type': 'port', 'comp': '<', 'value': '500'}),
        ('MODIFIER', ')'),
        ('MODIFIER', ')'),
    ]

    s = 'dst port < 500)'
    with pytest.raises(rule_parser.RuleParseError):
        parser = rule_parser.RuleParser({}, s)

    s = '(dst port < 500'
    with pytest.raises(rule_parser.RuleParseError):
        parser = rule_parser.RuleParser({}, s)

    s = 'dst port < 500)('
    with pytest.raises(rule_parser.RuleParseError):
        parser = rule_parser.RuleParser({}, s)

    s = 'dst port < 500()'
    parser = rule_parser.RuleParser({}, s)
    assert parser.clauses == [
        ('CLAUSE', {'dir_': 'dst', 'type': 'port', 'comp': '<', 'value': '500'}),
        ('MODIFIER', '('),
        ('MODIFIER', ')'),
    ]


def test_sql():
    s1 = 'src host = 1.2.3.4'
    parser = rule_parser.RuleParser({}, s1)
    sql = parser.sql
    assert sql == 'src = 16909060'

    s2 = 'src host in [1.2.3.4, 10.20.30.40, 100.200.50.150]'
    parser = rule_parser.RuleParser({}, s2)
    sql = parser.sql
    assert sql == 'src in (16909060,169090600,1690841750)'

    s3 = 'dst port in [22, 33, 44]'
    parser = rule_parser.RuleParser({}, s3)
    sql = parser.sql
    assert sql == 'port in (22,33,44)'

    s4 = 'dst port = 5'
    parser = rule_parser.RuleParser({}, s4)
    sql = parser.sql
    assert sql == 'port = 5'

    s5 = '(src host = 1.2.3.4 or dst host = 5.6.7.8) and port = 80'
    parser = rule_parser.RuleParser({}, s5)
    sql = parser.sql
    assert sql == ' ( src = 16909060 or dst = 84281096 )  and port = 80'


def test_tcpdump_examples():
    s = 'host sundown'
    parser = rule_parser.RuleParser({}, s)
    assert parser.clauses == [
        ('CLAUSE', {'dir_': 'either', 'type': 'host', 'comp': '=', 'value': 'sundown'})
    ]

    s = 'host helios and ( hot or ace )'
    parser = rule_parser.RuleParser({}, s)
    assert parser.clauses == [
        ('CLAUSE', {'dir_': 'either', 'type': 'host', 'comp': '=', 'value': 'helios'}),
        ('JOIN', 'and'),
        ('MODIFIER', '('),
        ('CLAUSE', {'dir_': 'either', 'type': 'host', 'comp': '=', 'value': 'hot'}),
        ('JOIN', 'or'),
        ('CLAUSE', {'dir_': 'either', 'type': 'host', 'comp': '=', 'value': 'ace'}),
        ('MODIFIER', ')'),
    ]

    s = 'ip host ace and not helios'  # all traffic available is IP traffic
    s = 'host ace and not helios'
    parser = rule_parser.RuleParser({}, s)
    assert parser.clauses == [
        ('CLAUSE', {'dir_': 'either', 'type': 'host', 'comp': '=', 'value': 'ace'}),
        ('JOIN', 'and'),
        ('MODIFIER', 'not'),
        ('CLAUSE', {'dir_': 'either', 'type': 'host', 'comp': '=', 'value': 'helios'}),
    ]

    s = 'net ucb-ether'  # 'net' is not supported in SAM
    s = 'gateway snup and (port ftp or ftp-data)'  # 'gateway' is not supported in SAM
    s = 'ip and not net localnet'  # 'localnet' is not supported in SAM
    s = 'tcp[tcpflags] & (tcp-syn|tcp-fin) != 0 and not src and dst net localnet'  # tcp flags haven't been retained by SAM
    s = 'tcp port 80 and (((ip[2:2] - ((ip[0]&0xf)<<2)) - ((tcp[12]&0xf0)>>2)) != 0)'  # no data has been retained by SAM
    s = 'gateway snup and ip[2:2] > 576'  # 'gateway' is not supported in SAM
    s = 'ether[0] & 1 = 0 and ip[16] >= 224'  #
    s = 'icmp[icmptype] != icmp-echo and icmp[icmptype] != icmp-echoreply'



