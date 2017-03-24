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
    assert False

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
