import constants
import db_connection
import models.nodes
import web.template
import common

sub_id = constants.demo['id']


def test_get_all_endpoints():
    m_nodes = models.nodes.Nodes(sub_id)
    actual = m_nodes.get_all_endpoints()
    actual.sort()
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
    assert expected == actual

def test_get_children():
    m_nodes = models.nodes.Nodes(sub_id)
    kids = m_nodes.get_children("10.20")
    ips = [kid['ipstart'] for kid in kids]
    ips.sort()
    assert len(ips) == 2
    assert ips[0] == common.IPStringtoInt('10.20.30.0')
    assert ips[1] == common.IPStringtoInt('10.20.32.0')

def test_get_root_nodes():
    m_nodes = models.nodes.Nodes(sub_id)
    roots = m_nodes.get_root_nodes()
    ips = [root['ipstart'] for root in roots]
    ips.sort()
    assert len(ips) == 3
    assert ips[0] == common.IPStringtoInt('10.0.0.0')
    assert ips[1] == common.IPStringtoInt('50.0.0.0')
    assert ips[2] == common.IPStringtoInt('59.0.0.0')

def test_tags():
    m_nodes = models.nodes.Nodes(sub_id)
    m_nodes.delete_custom_tags()
    m_nodes.set_tags('10', ['tag8'])
    m_nodes.set_tags('10.20', ['tag16'])
    m_nodes.set_tags('10.20.30', ['tag24'])
    m_nodes.set_tags('10.20.30.40', ['tag32', 'bonus'])
    m_nodes.set_tags('10.20.30.41', ['tag32b'])
    m_nodes.set_tags('10.20.32', ['tag24b'])
    m_nodes.set_tags('10.24', ['tag16b'])
    m_nodes.set_tags('50', ['tag8b'])
    m_nodes.set_tags('50.60', ['tag16b'])
    m_nodes.set_tags('50.60.70', ['tag24b'])
    m_nodes.set_tags('50.60.70.80', ['tag32b'])

    all_tags = m_nodes.get_tag_list()
    assert set(all_tags) == {'tag8', 'tag16', 'tag24', 'tag32', 'bonus', 'tag8b', 'tag16b', 'tag24b', 'tag32b'}

    tags = m_nodes.get_tags('10.20.30')
    assert set(tags['p_tags']) == {'tag8', 'tag16'}
    assert set(tags['tags']) == {'tag24'}

    tags = m_nodes.get_tags('10.20.30.40')
    assert set(tags['p_tags']) == {'tag8', 'tag16', 'tag24'}
    assert set(tags['tags']) == {'tag32', 'bonus'}

    m_nodes.delete_custom_tags()
    tags = m_nodes.get_tags('10.20.30.40')
    assert set(tags['p_tags']) == set()
    assert set(tags['tags']) == set()

def test_env():
    m_nodes = models.nodes.Nodes(sub_id)
    m_nodes.delete_custom_envs()
    m_nodes.set_env('10', 'inherit')
    m_nodes.set_env('10.20', 'dev')
    m_nodes.set_env('50', None)
    m_nodes.set_env('50.60', 'production')
    m_nodes.set_env('50.64', 'test_env')

    all_envs = m_nodes.get_env_list()
    assert set(all_envs) == {'production', 'dev', 'test_env', 'inherit'}

    assert m_nodes.get_env('10') == {'env': 'inherit', 'p_env': 'production'}
    assert m_nodes.get_env('10.20') == {'env': 'dev', 'p_env': 'production'}
    assert m_nodes.get_env('10.24') == {'env': 'inherit', 'p_env': 'production'}
    assert m_nodes.get_env('10.20.30') == {'env': 'inherit', 'p_env': 'dev'}
    assert m_nodes.get_env('50') == {'env': 'inherit', 'p_env': 'production'}
    assert m_nodes.get_env('50.60') == {'env': 'production', 'p_env': 'production'}
    assert m_nodes.get_env('50.64') == {'env': 'test_env', 'p_env': 'production'}
    m_nodes.set_env('10', 'test_env')
    m_nodes.set_env('50', 'test_env')
    assert m_nodes.get_env('50.60') == {'env': 'production', 'p_env': 'test_env'}
    assert m_nodes.get_env('10.24') == {'env': 'inherit', 'p_env': 'test_env'}

    m_nodes.delete_custom_envs()
    assert m_nodes.get_env('10') == {'env': 'inherit', 'p_env': 'production'}
    assert m_nodes.get_env('50') == {'env': 'inherit', 'p_env': 'production'}

def test_alias():
    m_nodes = models.nodes.Nodes(sub_id)
    m_nodes.set_alias('10', 'hero')
    m_nodes.set_alias('10.20', 'side-kick')
    m_nodes.set_alias('10.20.30', 'henchman')
    m_nodes.set_alias('10.20.30.40', 'villain')

    assert m_nodes.get('10').alias == 'hero'
    assert m_nodes.get('10.20').alias == 'side-kick'
    assert m_nodes.get('10.20.30').alias == 'henchman'
    assert m_nodes.get('10.20.30.40').alias == 'villain'

    m_nodes.delete_custom_hostnames()

    assert m_nodes.get('10').alias == None
    assert m_nodes.get('10.20').alias == None
    assert m_nodes.get('10.20.30').alias == None
    assert m_nodes.get('10.20.30.40').alias == None
