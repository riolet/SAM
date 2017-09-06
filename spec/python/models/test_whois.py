from spec.python import db_connection
from sam.models import whois
import pytest

db = db_connection.db
sub_id = db_connection.default_sub
ds_id = db_connection.dsid_default

ip_arin1 = '104.31.70.170'
ip_arin1_name = 'Cloudflare, Inc.'
ip_arin1_net = ('CLOUDFLARENET', 1745879040, 1746927615, 12)
ip_arin2 = '199.59.148.85'
ip_arin2_name = 'Twitter Inc.'
ip_arin2_net = ('TWITTER-NETWORK', 3342570496, 3342571519, 22)

ip_ripe1 = '31.13.76.68'
ip_ripe1_name = 'Facebook'
ip_ripe1_net = ('SEA1', 520965120, 520965375, 24)
ip_ripe2 = '91.189.92.150'
ip_ripe2_name = 'Canonical Ltd'
ip_ripe2_net = ('CANONICAL-CORE', 1539135488, 1539137535, 21)


ip_apnic1 = '203.119.101.24'
ip_apnic1_name = 'Asia Pacific Network Information Centre'
ip_apnic1_net = ('APNIC-SERVICES-AU', 3413598208, 3413602303, 20)
ip_apnic2 = '164.100.78.177'
ip_apnic2_name = 'NICNET, INDIA'
ip_apnic2_net = ('NICNET', 2758017024, 2758082559, 16)


def test_ip_itos():
    assert whois.ip_itos(int(1e0)) == "0.0.0.1"
    assert whois.ip_itos(int(1e1)) == "0.0.0.10"
    assert whois.ip_itos(int(1e2)) == "0.0.0.100"
    assert whois.ip_itos(int(1e3)) == "0.0.3.232"
    assert whois.ip_itos(int(1e4)) == "0.0.39.16"
    assert whois.ip_itos(int(1e5)) == "0.1.134.160"
    assert whois.ip_itos(int(1e6)) == "0.15.66.64"
    assert whois.ip_itos(int(1e7)) == "0.152.150.128"
    assert whois.ip_itos(int(1e8)) == "5.245.225.0"
    assert whois.ip_itos(int(1e9)) == "59.154.202.0"


def test_ip_stoi():
    assert whois.ip_stoi("0.0.0.1") == 1e0
    assert whois.ip_stoi("0.0.0.10") == 1e1
    assert whois.ip_stoi("0.0.0.100") == 1e2
    assert whois.ip_stoi("0.0.3.232") == 1e3
    assert whois.ip_stoi("0.0.39.16") == 1e4
    assert whois.ip_stoi("0.1.134.160") == 1e5
    assert whois.ip_stoi("0.15.66.64") == 1e6
    assert whois.ip_stoi("0.152.150.128") == 1e7
    assert whois.ip_stoi("5.245.225.0") == 1e8
    assert whois.ip_stoi("59.154.202.0") == 1e9
    assert whois.ip_stoi("1.2.3.4") == 16909060
    assert whois.ip_stoi("1.2.3.4/32") == 16909060
    assert whois.ip_stoi("1.2.3.4/24") == 16909056
    assert whois.ip_stoi("1.2.3.4/16") == 16908288
    assert whois.ip_stoi("1.2.3.4/8") == 16777216
    assert whois.ip_stoi("10/8") == 167772160
    assert whois.ip_stoi("10/16") == 167772160
    assert whois.ip_stoi("10/24") == 167772160
    assert whois.ip_stoi("10/32") == 167772160
    assert whois.ip_stoi("10") == 167772160
    assert whois.ip_stoi("10.20") == 169082880
    assert whois.ip_stoi("10.20.30") == 169090560
    assert whois.ip_stoi("10.20.30.40") == 169090600


def test_arin():
    w = whois.Whois(ip_arin1)
    network = w.query_ARIN()
    assert 'orgRef' in network
    assert 'handle' in network
    assert 'name' in network

    w.info = network
    w.downloaded = True
    w.decode_ARIN()
    assert w.get_name() == ip_arin1_name
    assert w.get_network() == ip_arin1_net

    w = whois.Whois(ip_arin2)
    network = w.query_ARIN()
    assert 'orgRef' in network
    assert 'handle' in network
    assert 'name' in network

    w.info = network
    w.downloaded = True
    w.decode_ARIN()
    assert w.get_name() == ip_arin2_name
    print(w.get_network())
    assert w.get_network() == ip_arin2_net

    w = whois.Whois(ip_ripe1)
    with pytest.raises(whois.WrongAuthorityError):
        w.query_ARIN()

    w = whois.Whois(ip_ripe2)
    with pytest.raises(whois.WrongAuthorityError):
        w.query_ARIN()

    w = whois.Whois(ip_apnic1)
    with pytest.raises(whois.WrongAuthorityError):
        w.query_ARIN()

    w = whois.Whois(ip_apnic2)
    with pytest.raises(whois.WrongAuthorityError):
        w.query_ARIN()


def test_ripe():
    w = whois.Whois(ip_ripe1)
    network = w.query_RIPE()
    assert {n['type'] for n in network} == {'role', 'inetnum'}

    w.info = network
    w.downloaded = True
    w.decode_RIPE()
    assert w.get_name() == ip_ripe1_name
    assert w.get_network() == ip_ripe1_net

    w = whois.Whois(ip_ripe2)
    network = w.query_RIPE()
    assert {n['type'] for n in network} == {'route', 'organisation', 'role', 'inetnum'}

    w.info = network
    w.downloaded = True
    w.decode_RIPE()
    assert w.get_name() == ip_ripe2_name
    assert w.get_network() == ip_ripe2_net


def test_apnic():
    w = whois.Whois(ip_apnic1)
    network = w.query_APNIC()
    objs = {n['objectType'] for n in network if n['type'] == 'object'}
    assert objs == {'role', 'route', 'irt', 'inetnum'}

    w.info = network
    w.downloaded = True
    w.decode_APNIC()
    assert w.get_name() == ip_apnic1_name
    assert w.get_network() == ip_apnic1_net

    w = whois.Whois(ip_apnic2)
    network = w.query_APNIC()
    objs = {n['objectType'] for n in network if n['type'] == 'object'}
    print objs
    assert objs == {'person', 'role', 'route', 'irt', 'inetnum'}

    w.info = network
    w.downloaded = True
    w.decode_APNIC()
    print(w.get_name())
    print(w.get_network())
    assert w.get_name() == ip_apnic2_name
    assert w.get_network() == ip_apnic2_net


def test_overall():
    w = whois.Whois(ip_arin1)
    assert w.get_name() == ip_arin1_name
    w = whois.Whois(ip_arin2)
    assert w.get_network() == ip_arin2_net

    w = whois.Whois(ip_ripe1)
    assert w.get_name() == ip_ripe1_name
    w = whois.Whois(ip_ripe2)
    assert w.get_network() == ip_ripe2_net

    w = whois.Whois(ip_apnic1)
    assert w.get_name() == ip_apnic1_name
    w = whois.Whois(ip_apnic2)
    assert w.get_network() == ip_apnic2_net


def test_get_missing():
    ws = whois.WhoisService(db, sub_id)
    actual = set(ws.get_missing())
    assert '10.20.30.40' in actual
    assert '10.20.30.41' in actual

    db.query("UPDATE s{}_Nodes SET alias='temp' WHERE ipstart=169090600 and ipend=169090600".format(sub_id))


    actual = set(ws.get_missing())
    assert '10.20.30.40' not in actual
    assert '10.20.30.41' in actual

    db.query("UPDATE s{}_Nodes SET alias=NULL WHERE ipstart=169090600 and ipend=169090600".format(sub_id))