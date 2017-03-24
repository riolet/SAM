import constants
import db_connection
import common
import models.links
import models.datasources
from datetime import datetime

sub_id = constants.demo['id']
ds_model = models.datasources.Datasources({}, sub_id)
ds_full = 0
ds_empty = 0
for ds in ds_model.datasources.values():
    if ds['name'] == u'default':
        ds_full = int(ds['id'])
    if ds['name'] == u'short':
        ds_empty = int(ds['id'])


def test_get_protocol_list():
    l_model = models.links.Links(sub_id, ds_full)
    protocols = l_model.get_protocol_list()
    protocols.sort()
    assert protocols == [u'ICMP', u'TCP', u'UDP']

    l_model = models.links.Links(sub_id, ds_empty)
    protocols = l_model.get_protocol_list()
    protocols.sort()
    assert protocols == []


def test_get_timerange():
    l_model = models.links.Links(sub_id, ds_full)
    range = l_model.get_timerange()
    assert datetime.fromtimestamp(range['min']) == datetime(2016, 1, 17, 13, 20, 00)
    assert datetime.fromtimestamp(range['max']) == datetime(2018, 3, 19, 15, 25, 00)

    l_model = models.links.Links(sub_id, ds_empty)
    range = l_model.get_timerange()
    assert range['min'] == range['max']


def test_get_links():
    l_model = models.links.Links(sub_id, ds_full)
    timerange = None
    port = None
    protocol = None

    links = l_model.get_links([], timerange, port, protocol)
    assert links == {}

    links = l_model.get_links(['10.11.12.13'], timerange, port, protocol)
    first = links['10.11.12.13']
    assert len(first['outputs']) == 0
    assert len(first['inputs']) == 0

    links = l_model.get_links(['10.20.30.40'], timerange, port, protocol)
    first = links['10.20.30.40']
    assert len(first['outputs']) == 6
    assert sum([x['links'] for x in first['outputs']]) == 16
    assert len(first['inputs']) == 3

    links = l_model.get_links(['59.69.79.89', '50.60.70.80'], timerange, port, protocol)
    first = links['59.69.79.89']
    second = links['50.60.70.80']
    assert len(first['outputs']) == 2
    assert sum([x['links'] for x in first['outputs']]) == 3
    assert len(first['inputs']) == 0
    assert len(second['outputs']) == 0
    assert len(second['inputs']) == 1


#for o in outs:
#   print("{0} to {1}-{2} on {3} ({4})".format(t(o['src_start']), t(o['dst_start']), t(o['dst_end']), o['port'], o['protocols']))


def test_get_links_time():
    pass
    # need filter by time range
    #"59.69.79.89" @ 2017  # 1 out, 0 in
    #'10.20.30.40' @ 2017  # 5 out 1 in
    #"50.60.70.80" @ 2017  # 0 out, 0 in

def test_get_links_port():
    pass
    # need filter by port
    #'10.20.30.40' @ 80  # 8 out 2 in
    #'10.20.30.40' @ 443  # 8 out 1 in
    #"50.60.70.80" @ 80  # 0 out, 1 in
    #"50.60.70.80" @ 443  # 0 out, 0 in

def test_get_links_protocol():
    pass
    # need filter by protocol
    #'59.69.79.89' ICMP  # 3 out 0 in
    #'50.60.70.80' ICMP  # 0 out 0 in
    #'10.20.30.40' ICMP  # 0 out 3 in
    #'10.20.30.40' TCP   # 8 out 1 in
    #'10.20.30.40' UDP   # 8 out 0 in

def test_get_links_combined():
    pass
    # combo
    #'10.20.30.40' TCP 2018 80  # 2 out 0 in
    #'10.20.30.40' 2018 80  # 3 out 1 in
    #'10.20.30.40' TCP 2018  # 4 out 0 in
    #'10.20.30.40' TCP 80  # 4 out 0 in



def test_get_all_endpoints():
    l_model = models.links.Links(sub_id, ds_full)
    eps = l_model.get_all_endpoints()
    t = common.IPStringtoInt
    expected = map(common.IPStringtoInt, [
        '10.20.30.40',
        '10.20.30.41',
        '10.20.32.42',
        '10.20.32.43',
        '10.24.34.44',
        '10.24.34.45',
        '10.24.36.46',
        '10.24.36.47',
        '50.60.70.80',
        '50.60.70.81',
        '50.60.72.82',
        '50.60.72.83',
        '50.64.74.84',
        '50.64.74.85',
        '50.64.76.86',
        '50.64.76.87',
        '59.69.79.89'])
    eps.sort()
    assert eps == expected

    l_model = models.links.Links(sub_id, ds_empty)
    eps = l_model.get_all_endpoints()
    assert eps == []
