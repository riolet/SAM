from sam.models.whois import Whois, WrongAuthorityError
import pytest

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


def test_arin():
    w = Whois(ip_arin1)
    network = w.query_ARIN()
    assert 'orgRef' in network
    assert 'handle' in network
    assert 'name' in network

    w.info = network
    w.downloaded = True
    w.decode_ARIN()
    assert w.get_name() == ip_arin1_name
    assert w.get_network() == ip_arin1_net

    w = Whois(ip_arin2)
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

    w = Whois(ip_ripe1)
    with pytest.raises(WrongAuthorityError, 'RIPE'):
        w.query_ARIN()

    w = Whois(ip_ripe2)
    with pytest.raises(WrongAuthorityError, 'RIPE'):
        w.query_ARIN()

    w = Whois(ip_apnic1)
    with pytest.raises(WrongAuthorityError, 'APNIC'):
        w.query_ARIN()

    w = Whois(ip_apnic2)
    with pytest.raises(WrongAuthorityError, 'APNIC'):
        w.query_ARIN()


def test_ripe():
    w = Whois(ip_ripe1)
    network = w.query_RIPE()
    assert {n['type'] for n in network} == {'role', 'inetnum'}

    w.info = network
    w.downloaded = True
    w.decode_RIPE()
    assert w.get_name() == ip_ripe1_name
    assert w.get_network() == ip_ripe1_net

    w = Whois(ip_ripe2)
    network = w.query_RIPE()
    assert {n['type'] for n in network} == {'route', 'organisation', 'role', 'inetnum'}

    w.info = network
    w.downloaded = True
    w.decode_RIPE()
    assert w.get_name() == ip_ripe2_name
    assert w.get_network() == ip_ripe2_net


def test_apnic():
    w = Whois(ip_apnic1)
    network = w.query_APNIC()
    objs = {n['objectType'] for n in network if n['type'] == 'object'}
    assert objs == {'role', 'route', 'irt', 'inetnum'}

    w.info = network
    w.downloaded = True
    w.decode_APNIC()
    assert w.get_name() == ip_apnic1_name
    assert w.get_network() == ip_apnic1_net

    w = Whois(ip_apnic2)
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
    w = Whois(ip_arin1)
    assert w.get_name() == ip_arin1_name
    w = Whois(ip_arin2)
    assert w.get_network() == ip_arin2_net

    w = Whois(ip_ripe1)
    assert w.get_name() == ip_ripe1_name
    w = Whois(ip_ripe2)
    assert w.get_network() == ip_ripe2_net

    w = Whois(ip_apnic1)
    assert w.get_name() == ip_apnic1_name
    w = Whois(ip_apnic2)
    assert w.get_network() == ip_apnic2_net
