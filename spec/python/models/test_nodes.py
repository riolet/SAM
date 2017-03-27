from spec.python import db_connection
import common
import models.nodes

db = db_connection.db
sub_id = db_connection.default_sub
ds_full = db_connection.dsid_default


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
    assert expected == actual

def test_get_children():
    m_nodes = models.nodes.Nodes(sub_id)
    kids = m_nodes.get_children("110.20")
    ips = [kid['ipstart'] for kid in kids]
    ips.sort()
    assert len(ips) == 2
    assert ips[0] == common.IPStringtoInt('110.20.30.0')
    assert ips[1] == common.IPStringtoInt('110.20.32.0')

def test_get_root_nodes():
    m_nodes = models.nodes.Nodes(sub_id)
    roots = m_nodes.get_root_nodes()
    ips = [root['ipstart'] for root in roots]
    ips.sort()
    assert len(ips) == 6
    assert set(ips) == set(map(common.IPStringtoInt,['10.0.0.0', '50.0.0.0', '59.0.0.0',
                                                     '110.0.0.0', '150.0.0.0', '159.0.0.0']))

def test_tags():
    m_nodes = models.nodes.Nodes(sub_id)
    m_nodes.delete_custom_tags()
    m_nodes.set_tags('110', ['tag8'])
    m_nodes.set_tags('110.20', ['tag16'])
    m_nodes.set_tags('110.20.30', ['tag24'])
    m_nodes.set_tags('110.20.30.40', ['tag32', 'bonus'])
    m_nodes.set_tags('110.20.30.41', ['tag32b'])
    m_nodes.set_tags('110.20.32', ['tag24b'])
    m_nodes.set_tags('110.24', ['tag16b'])
    m_nodes.set_tags('150', ['tag8b'])
    m_nodes.set_tags('150.60', ['tag16b'])
    m_nodes.set_tags('150.60.70', ['tag24b'])
    m_nodes.set_tags('150.60.70.80', ['tag32b'])

    all_tags = m_nodes.get_tag_list()
    assert set(all_tags) == {'tag8', 'tag16', 'tag24', 'tag32', 'bonus', 'tag8b', 'tag16b', 'tag24b', 'tag32b'}

    tags = m_nodes.get_tags('110.20.30')
    assert set(tags['p_tags']) == {'tag8', 'tag16'}
    assert set(tags['tags']) == {'tag24'}

    tags = m_nodes.get_tags('110.20.30.40')
    assert set(tags['p_tags']) == {'tag8', 'tag16', 'tag24'}
    assert set(tags['tags']) == {'tag32', 'bonus'}

    m_nodes.delete_custom_tags()
    tags = m_nodes.get_tags('110.20.30.40')
    assert set(tags['p_tags']) == set()
    assert set(tags['tags']) == set()

def test_env():
    m_nodes = models.nodes.Nodes(sub_id)
    m_nodes.delete_custom_envs()
    m_nodes.set_env('110', 'inherit')
    m_nodes.set_env('110.20', 'dev')
    m_nodes.set_env('150', None)
    m_nodes.set_env('150.60', 'production')
    m_nodes.set_env('150.64', 'test_env')

    all_envs = m_nodes.get_env_list()
    assert set(all_envs) == {'production', 'dev', 'test_env', 'inherit'}

    assert m_nodes.get_env('110') == {'env': 'inherit', 'p_env': 'production'}
    assert m_nodes.get_env('110.20') == {'env': 'dev', 'p_env': 'production'}
    assert m_nodes.get_env('110.24') == {'env': 'inherit', 'p_env': 'production'}
    assert m_nodes.get_env('110.20.30') == {'env': 'inherit', 'p_env': 'dev'}
    assert m_nodes.get_env('150') == {'env': 'inherit', 'p_env': 'production'}
    assert m_nodes.get_env('150.60') == {'env': 'production', 'p_env': 'production'}
    assert m_nodes.get_env('150.64') == {'env': 'test_env', 'p_env': 'production'}
    m_nodes.set_env('110', 'test_env')
    m_nodes.set_env('150', 'test_env')
    assert m_nodes.get_env('150.60') == {'env': 'production', 'p_env': 'test_env'}
    assert m_nodes.get_env('110.24') == {'env': 'inherit', 'p_env': 'test_env'}

    m_nodes.delete_custom_envs()
    assert m_nodes.get_env('110') == {'env': 'inherit', 'p_env': 'production'}
    assert m_nodes.get_env('150') == {'env': 'inherit', 'p_env': 'production'}

def test_alias():
    m_nodes = models.nodes.Nodes(sub_id)
    m_nodes.set_alias('110', 'hero')
    m_nodes.set_alias('110.20', 'side-kick')
    m_nodes.set_alias('110.20.30', 'henchman')
    m_nodes.set_alias('110.20.30.40', 'villain')

    assert m_nodes.get('110').alias == 'hero'
    assert m_nodes.get('110.20').alias == 'side-kick'
    assert m_nodes.get('110.20.30').alias == 'henchman'
    assert m_nodes.get('110.20.30.40').alias == 'villain'

    m_nodes.delete_custom_hostnames()

    assert m_nodes.get('110').alias is None
    assert m_nodes.get('110.20').alias is None
    assert m_nodes.get('110.20.30').alias is None
    assert m_nodes.get('110.20.30.40').alias is None
