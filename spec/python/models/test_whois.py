import models.whois

ip_arin1 = '104.31.70.170'
ip_arin1_name = 'Cloudflare, Inc.'
ip_arin2 = '199.59.148.85'
ip_arin2_name = 'Twitter Inc.'

ip_ripe1 = '31.13.76.68'
ip_ripe1_name = 'Facebook'
ip_ripe2 = '91.189.92.150'
ip_ripe2_name = 'Canonical Ltd'


ip_apnic1 = '203.119.101.24'
ip_apnic1_name = 'Asia Pacific Network Information Centre'
ip_apnic2 = '164.100.78.177'
ip_apnic2_name = 'NICNET, INDIA'


def test_arin():
    w = models.whois.Whois(ip_arin1)
    assert w.query_ARIN() == ip_arin1_name

    w = models.whois.Whois(ip_arin2)
    assert w.query_ARIN() == ip_arin2_name

    w = models.whois.Whois(ip_ripe1)
    assert w.query_ARIN() == 'RIPE'

    w = models.whois.Whois(ip_ripe2)
    assert w.query_ARIN() == 'RIPE'

    w = models.whois.Whois(ip_apnic1)
    assert w.query_ARIN() == 'APNIC'

    w = models.whois.Whois(ip_apnic2)
    assert w.query_ARIN() == 'APNIC'


def test_ripe():
    w = models.whois.Whois(ip_ripe1)
    assert w.query_RIPE() == ip_ripe1_name

    w = models.whois.Whois(ip_ripe2)
    assert w.query_RIPE() == ip_ripe2_name


def test_apnic():
    w = models.whois.Whois(ip_apnic1)
    assert w.query_APNIC() == ip_apnic1_name

    w = models.whois.Whois(ip_apnic2)
    assert w.query_APNIC() == ip_apnic2_name


def test_overall():
    w = models.whois.Whois(ip_arin1)
    assert w.ip_to_org() == ip_arin1_name

    w = models.whois.Whois(ip_ripe1)
    assert w.ip_to_org() == ip_ripe1_name

    w = models.whois.Whois(ip_apnic1)
    assert w.ip_to_org() == ip_apnic1_name
