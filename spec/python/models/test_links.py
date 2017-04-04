import time
from datetime import datetime

from spec.python import db_connection
import common
import models.links

db = db_connection.db
sub_id = db_connection.default_sub
ds_full = db_connection.dsid_default
ds_empty = db_connection.dsid_short


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

    links = l_model.get_links(['110.11.12.13'], timerange, port, protocol)
    first = links['110.11.12.13']
    assert len(first['outputs']) == 0
    assert len(first['inputs']) == 0

    links = l_model.get_links(['110.20.30.40'], timerange, port, protocol)
    first = links['110.20.30.40']
    assert len(first['outputs']) == 6
    assert sum([x['links'] for x in first['outputs']]) == 16
    assert len(first['inputs']) == 3

    links = l_model.get_links(['159.69.79.89', '150.60.70.80'], timerange, port, protocol)
    first = links['159.69.79.89']
    second = links['150.60.70.80']
    assert len(first['outputs']) == 2
    assert sum([x['links'] for x in first['outputs']]) == 3
    assert len(first['inputs']) == 0
    assert len(second['outputs']) == 0
    assert len(second['inputs']) == 1


def test_get_links_time():
    l_model = models.links.Links(sub_id, ds_full)
    timerange = (time.mktime(datetime(2017, 1, 1).timetuple()), time.mktime(datetime(2018, 1, 1).timetuple()))
    port = None
    protocol = None

    # need filter by time range
    links = l_model.get_links(['110.20.30.40', '150.60.70.80', '159.69.79.89'], timerange, port, protocol)
    first = links['110.20.30.40']
    second = links['150.60.70.80']
    third = links['159.69.79.89']

    # '110.20.30.40' @ 2017  # 5 out 1 in
    assert len(first['outputs']) == 4
    assert sum([x['links'] for x in first['outputs']]) == 5
    assert len(first['inputs']) == 1

    # '150.60.70.80' @ 2017  # 0 out, 0 in
    assert len(second['outputs']) == 0
    assert len(second['inputs']) == 0

    # '159.69.79.89' @ 2017  # 1 out, 0 in
    assert len(third['outputs']) == 1
    assert len(third['inputs']) == 0


def test_get_links_port():
    l_model = models.links.Links(sub_id, ds_full)
    timerange = None
    port = 180
    protocol = None
    # need filter by port
    # '110.20.30.40' @ 180  # 8 out 2 in
    # "150.60.70.80" @ 180  # 0 out, 1 in
    links = l_model.get_links(['110.20.30.40', '150.60.70.80'], timerange, port, protocol)
    first = links['110.20.30.40']
    second = links['150.60.70.80']
    assert len(first['outputs']) == 4
    assert sum([x['links'] for x in first['outputs']]) == 8
    assert len(first['inputs']) == 2
    assert sum([x['links'] for x in first['inputs']]) == 3
    assert len(second['outputs']) == 0
    assert len(second['inputs']) == 1

    # '110.20.30.40' @ 1443  # 8 out 1 in
    # "150.60.70.80" @ 1443  # 0 out, 0 in
    port = 1443
    links = l_model.get_links(['110.20.30.40', '150.60.70.80'], timerange, port, protocol)
    first = links['110.20.30.40']
    second = links['150.60.70.80']
    assert len(first['outputs']) == 2
    assert sum([x['links'] for x in first['outputs']]) == 8
    assert len(first['inputs']) == 1
    assert len(second['outputs']) == 0
    assert len(second['inputs']) == 0


def test_get_links_protocol():
    l_model = models.links.Links(sub_id, ds_full)
    timerange = None
    port = None
    protocol = 'ICMP'

    # need filter by protocol
    # '110.20.30.40' ICMP  # 0 out 3 in
    # '150.60.70.80' ICMP  # 0 out 0 in
    # '159.69.79.89' ICMP  # 3 out 0 in
    links = l_model.get_links(['110.20.30.40', '150.60.70.80', '159.69.79.89'], timerange, port, protocol)
    first = links['110.20.30.40']
    second = links['150.60.70.80']
    third = links['159.69.79.89']
    assert len(first['outputs']) == 0
    assert len(first['inputs']) == 2 and sum([x['links'] for x in first['inputs']]) == 3
    assert len(second['outputs']) == 0
    assert len(second['inputs']) == 0
    assert len(third['outputs']) == 2 and sum([x['links'] for x in third['outputs']]) == 3
    assert len(third['inputs']) == 0

    # '110.20.30.40' TCP   # 8 out 1 in
    protocol = 'TCP'
    links = l_model.get_links(['110.20.30.40'], timerange, port, protocol)
    first = links['110.20.30.40']
    assert len(first['outputs']) == 4 and sum([x['links'] for x in first['outputs']]) == 8
    assert len(first['inputs']) == 1

    # '110.20.30.40' UDP   # 8 out 0 in
    protocol = 'UDP'
    links = l_model.get_links(['110.20.30.40'], timerange, port, protocol)
    first = links['110.20.30.40']
    assert len(first['outputs']) == 2 and sum([x['links'] for x in first['outputs']]) == 8
    assert len(first['inputs']) == 0


def test_get_links_combined():
    l_model = models.links.Links(sub_id, ds_full)
    timerange = (time.mktime(datetime(2018, 1, 1).timetuple()), time.mktime(datetime(2019, 1, 1).timetuple()))
    port = 180
    protocol = 'TCP'

    # '110.20.30.40' TCP 2018 180  # 2 out 0 in
    links = l_model.get_links(['110.20.30.40'], timerange, port, protocol)
    first = links['110.20.30.40']
    assert len(first['outputs']) == 1 and sum([x['links'] for x in first['outputs']]) == 2
    assert len(first['inputs']) == 0

    # '110.20.30.40' 2018 180  # 3 out 1 in
    protocol = None
    links = l_model.get_links(['110.20.30.40'], timerange, port, protocol)
    first = links['110.20.30.40']
    assert len(first['outputs']) == 2 and sum([x['links'] for x in first['outputs']]) == 3
    assert len(first['inputs']) == 1 and sum([x['links'] for x in first['inputs']]) == 1

    # '110.20.30.40' TCP 2018  # 4 out 0 in
    protocol = 'TCP'
    port = None
    links = l_model.get_links(['110.20.30.40'], timerange, port, protocol)
    first = links['110.20.30.40']
    assert len(first['outputs']) == 2 and sum([x['links'] for x in first['outputs']]) == 4
    assert len(first['inputs']) == 0

    # '110.20.30.40' TCP 180  # 4 out 0 in
    port = 180
    protocol = 'TCP'
    timerange = None
    links = l_model.get_links(['110.20.30.40'], timerange, port, protocol)
    first = links['110.20.30.40']
    assert len(first['outputs']) == 3 and sum([x['links'] for x in first['outputs']]) == 4
    assert len(first['inputs']) == 1 and sum([x['links'] for x in first['inputs']]) == 1


def test_get_all_endpoints():
    l_model = models.links.Links(sub_id, ds_full)
    eps = l_model.get_all_endpoints()
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
        '59.69.79.89',
        '110.20.30.40',
        '110.20.30.41',
        '110.20.32.42',
        '110.20.32.43',
        '110.24.34.44',
        '110.24.34.45',
        '110.24.36.46',
        '110.24.36.47',
        '150.60.70.80',
        '150.60.70.81',
        '150.60.72.82',
        '150.60.72.83',
        '150.64.74.84',
        '150.64.74.85',
        '150.64.76.86',
        '150.64.76.87',
        '159.69.79.89'])
    eps.sort()
    assert eps == expected

    l_model = models.links.Links(sub_id, ds_empty)
    eps = l_model.get_all_endpoints()
    assert eps == []
