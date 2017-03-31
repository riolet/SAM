from spec.python import db_connection

import models.filters
import models.tables
import models.nodes

db = db_connection.db
sub_id = db_connection.default_sub
ds_full = db_connection.dsid_default


def correct_format(data):
    try:
        if len(data) == 0:
            return isinstance(data, list)
        for row in data:
            if not isinstance(row, dict) or 'address' not in row:
                return False
    except:
        return False
    return True


def test_get_table_info():
    m_table = models.tables.Table(sub_id, ds_full)
    rows = m_table.get_table_info([], page=0, page_size=100, order_by=0, order_dir='asc')
    assert len(rows) == 68
    assert correct_format(rows)


def test_get_table_pages():
    m_table = models.tables.Table(sub_id, ds_full)
    rows = m_table.get_table_info([], page=0, page_size=10, order_by=0, order_dir='asc')
    assert len(rows) == 11
    rows = m_table.get_table_info([], page=1, page_size=50, order_by=0, order_dir='asc')
    assert len(rows) == 18
    rows = m_table.get_table_info([], page=1, page_size=30, order_by=0, order_dir='asc')
    assert len(rows) == 31

    ps = 20
    p = 0
    safety = 0
    while safety < 10:
        rows = m_table.get_table_info([], page=p, page_size=ps, order_by=0, order_dir='asc')
        if len(rows) > ps:
            p += 1
        else:
            break
        safety += 1
    assert len(rows) == 8


def test_get_table_order():
    m_table = models.tables.Table(sub_id, ds_full)
    rows = m_table.get_table_info([], page=0, page_size=10, order_by=0, order_dir='asc')
    actual = [x['address'] for x in rows]
    expected = [u'10.0.0.0/8', u'10.20.0.0/16', u'10.20.30.0/24',
                u'10.20.30.40/32', u'10.20.30.41/32', u'10.20.32.0/24',
                u'10.20.32.42/32', u'10.20.32.43/32', u'10.24.0.0/16',
                u'10.24.34.0/24', u'10.24.34.44/32']
    assert actual == expected

    rows = m_table.get_table_info([], page=0, page_size=10, order_by=0, order_dir='desc')
    actual = [x['address'] for x in rows]
    expected = [u'159.69.79.89/32', u'159.69.79.0/24', u'159.69.0.0/16',
                u'159.0.0.0/8', u'150.64.76.87/32', u'150.64.76.86/32',
                u'150.64.76.0/24', u'150.64.74.85/32', u'150.64.74.84/32',
                u'150.64.74.0/24', u'150.64.0.0/16']
    assert actual == expected

    rows = m_table.get_table_info([], page=0, page_size=10, order_by=5, order_dir='desc')
    actual = [int(x['bytes_in'] + x['bytes_out']) for x in rows]
    expected = [218250, 207650, 110550, 107700, 106500, 101150, 56950, 56600, 54150, 53950, 53550]
    assert actual == expected

    rows = m_table.get_table_info([], page=0, page_size=10, order_by=5, order_dir='asc')
    actual = [int(x['bytes_in'] + x['bytes_out']) for x in rows]
    expected = [100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100]
    assert actual == expected


def test_get_table_filter_subnet():
    m_table = models.tables.Table(sub_id, ds_full)
    filters = []
    filters.append(models.filters.SubnetFilter(True, '16'))
    rows = m_table.get_table_info(filters, page=0, page_size=10, order_by=0, order_dir='asc')
    addresses = [x['address'].endswith('/16') for x in rows]
    assert len(addresses) == 10
    assert all(addresses)


def test_get_table_filter_mask():
    m_table = models.tables.Table(sub_id, ds_full)
    filters = [models.filters.MaskFilter(True, '10.20')]
    rows = m_table.get_table_info(filters, page=0, page_size=10, order_by=0, order_dir='asc')
    addresses = [x['address'] for x in rows]
    expected = [u'10.20.0.0/16', u'10.20.30.0/24', u'10.20.30.40/32', u'10.20.30.41/32',
                u'10.20.32.0/24', u'10.20.32.42/32', u'10.20.32.43/32']
    assert addresses == expected


def test_get_table_filter_port():
    m_table = models.tables.Table(sub_id, ds_full)

    # nodes that start '110.' and connect to another on port 180
    filters = [models.filters.MaskFilter(True, '110'), models.filters.PortFilter(True, '0', '180')]
    rows = m_table.get_table_info(filters, page=0, page_size=20, order_by=0, order_dir='asc')
    addresses = [x['address'] for x in rows]
    expected = [u'110.0.0.0/8', u'110.20.0.0/16', u'110.20.30.0/24', u'110.20.30.40/32']
    assert addresses == expected

    # nodes that start '110.' and don't connect to another on port 180
    filters = [models.filters.MaskFilter(True, '110'), models.filters.PortFilter(True, '1', '180')]
    rows = m_table.get_table_info(filters, page=0, page_size=20, order_by=0, order_dir='asc')
    addresses = [x['address'] for x in rows]
    expected = [u'110.20.30.41/32', u'110.20.32.0/24', u'110.20.32.42/32', u'110.20.32.43/32',
                u'110.24.0.0/16', u'110.24.34.0/24', u'110.24.34.44/32', u'110.24.34.45/32',
                u'110.24.36.0/24', u'110.24.36.46/32', u'110.24.36.47/32']
    assert addresses == expected

    # nodes that start '110.' and receive connections on port 180
    filters = [models.filters.MaskFilter(True, '110'), models.filters.PortFilter(True, '2', '180')]
    rows = m_table.get_table_info(filters, page=0, page_size=20, order_by=0, order_dir='asc')
    addresses = [x['address'] for x in rows]
    expected = [u'110.0.0.0/8', u'110.20.0.0/16', u'110.20.30.0/24', u'110.20.30.40/32',
                u'110.20.30.41/32', u'110.20.32.0/24', u'110.20.32.42/32', u'110.20.32.43/32']
    assert addresses == expected

    # nodes that start '110.' and don't receive connections on port 180
    filters = [models.filters.MaskFilter(True, '110'), models.filters.PortFilter(True, '3', '180')]
    rows = m_table.get_table_info(filters, page=0, page_size=20, order_by=0, order_dir='asc')
    addresses = [x['address'] for x in rows]
    expected = [u'110.24.0.0/16', u'110.24.34.0/24', u'110.24.34.44/32', u'110.24.34.45/32',
                u'110.24.36.0/24', u'110.24.36.46/32', u'110.24.36.47/32']
    assert addresses == expected


def test_get_table_filter_conn():
    m_table = models.tables.Table(sub_id, ds_full)

    # fewer than 0.0002 inbound connections / second
    filters = [models.filters.ConnectionsFilter(True, '<', 'i', '0.0002')]
    rows = m_table.get_table_info(filters, page=0, page_size=100, order_by=0, order_dir='asc')
    assert len(rows) == 46

    # more than 0.0002 inbound connections / second
    filters = [models.filters.ConnectionsFilter(True, '>', 'i', '0.0002')]
    rows = m_table.get_table_info(filters, page=0, page_size=100, order_by=0, order_dir='asc')
    assert len(rows) == 22

    # more than 0.0002 outbound connections / second
    filters = [models.filters.ConnectionsFilter(True, '>', 'o', '0.0002')]
    rows = m_table.get_table_info(filters, page=0, page_size=100, order_by=0, order_dir='asc')
    assert len(rows) == 20

    # fewer than 0.0002 outbound connections / second
    filters = [models.filters.ConnectionsFilter(True, '<', 'o', '0.0002')]
    rows = m_table.get_table_info(filters, page=0, page_size=100, order_by=0, order_dir='asc')
    assert len(rows) == 48


def test_get_table_filter_target():
    m_table = models.tables.Table(sub_id, ds_full)

    # nodes that connect to 10.20.30
    filters = [models.filters.TargetFilter(True, '10.20.30', '0')]
    rows = m_table.get_table_info(filters, page=0, page_size=100, order_by=0, order_dir='asc')
    addrA = [x['address'] for x in rows]
    assert len(rows) == 28
    # nodes that don't connect to 10.20.30
    filters = [models.filters.TargetFilter(True, '10.20.30', '1')]
    rows = m_table.get_table_info(filters, page=0, page_size=100, order_by=0, order_dir='asc')
    addrB = [x['address'] for x in rows]
    assert len(rows) == 40
    assert len(set(addrA) & set(addrB)) == 0

    # nodes that receive connections from 10.20.30
    filters = [models.filters.TargetFilter(True, '10.20.30', '2')]
    rows = m_table.get_table_info(filters, page=0, page_size=100, order_by=0, order_dir='asc')
    addrA = [x['address'] for x in rows]
    assert len(rows) == 34
    # nodes that don't receive connections from 10.20.30
    filters = [models.filters.TargetFilter(True, '10.20.30', '3')]
    rows = m_table.get_table_info(filters, page=0, page_size=100, order_by=0, order_dir='asc')
    addrB = [x['address'] for x in rows]
    assert len(rows) == 34
    assert len(set(addrA) & set(addrB)) == 0


def test_get_table_filter_tags():
    m_nodes = models.nodes.Nodes(sub_id)
    m_table = models.tables.Table(sub_id, ds_full)

    try:
        m_nodes.delete_custom_tags()
        #m_nodes.set_tags('110', ['tag8'])
        m_nodes.set_tags('110.20', ['tag16'])
        m_nodes.set_tags('110.20.30', ['tag24'])
        #m_nodes.set_tags('110.20.30.40', ['tag32', 'bonus'])
        m_nodes.set_tags('110.20.30.41', ['tag32b'])
        #m_nodes.set_tags('110.20.32', ['tag24b'])
        #m_nodes.set_tags('110.24', ['tag16b'])
        #m_nodes.set_tags('150', ['tag8b'])
        #m_nodes.set_tags('150.60', ['tag16b'])
        #m_nodes.set_tags('150.60.70', ['tag24b'])
        m_nodes.set_tags('150.60.70.80', ['tag32b'])

        filters = [models.filters.TagsFilter(True, '1', 'tag24')]
        rows = m_table.get_table_info(filters, page=0, page_size=100, order_by=0, order_dir='asc')
        actual = [x['address'] for x in rows]
        expected = [u'110.20.30.0/24', u'110.20.30.40/32', u'110.20.30.41/32']
        assert actual == expected

        filters = [models.filters.TagsFilter(True, '1', 'tag16,tag32b')]
        rows = m_table.get_table_info(filters, page=0, page_size=100, order_by=0, order_dir='asc')
        actual = [x['address'] for x in rows]
        expected = [u'110.20.30.41/32']
        assert actual == expected

        filters = [models.filters.MaskFilter(True, '110'), models.filters.TagsFilter(True, '0', 'tag24')]
        rows = m_table.get_table_info(filters, page=0, page_size=100, order_by=0, order_dir='asc')
        actual = [x['address'] for x in rows]
        expected = [u'110.0.0.0/8', u'110.20.0.0/16', u'110.20.32.0/24', u'110.20.32.42/32',
                    u'110.20.32.43/32', u'110.24.0.0/16', u'110.24.34.0/24', u'110.24.34.44/32',
                    u'110.24.34.45/32', u'110.24.36.0/24', u'110.24.36.46/32', u'110.24.36.47/32']
        assert actual == expected
    finally:
        m_nodes.delete_custom_tags()


def test_get_table_filter_env():
    m_nodes = models.nodes.Nodes(sub_id)
    m_table = models.tables.Table(sub_id, ds_full)

    try:
        m_nodes.delete_custom_envs()
        m_nodes.set_env('110', 'inherit')
        m_nodes.set_env('110.20', 'dev')
        m_nodes.set_env('150', None)
        m_nodes.set_env('150.60', 'production')
        m_nodes.set_env('150.64', 'test_env')

        filters = [models.filters.EnvFilter(True, 'dev')]
        rows = m_table.get_table_info(filters, page=0, page_size=100, order_by=0, order_dir='asc')
        actual = [x['address'] for x in rows]
        expected = [u'110.20.0.0/16', u'110.20.30.0/24', u'110.20.30.40/32', u'110.20.30.41/32',
                    u'110.20.32.0/24', u'110.20.32.42/32', u'110.20.32.43/32']
        assert actual == expected

        filters = [models.filters.MaskFilter(True, '150'), models.filters.EnvFilter(True, 'test_env')]
        rows = m_table.get_table_info(filters, page=0, page_size=100, order_by=0, order_dir='asc')
        actual = [x['address'] for x in rows]
        expected = [u'150.64.0.0/16', u'150.64.74.0/24', u'150.64.74.84/32', u'150.64.74.85/32',
                    u'150.64.76.0/24', u'150.64.76.86/32', u'150.64.76.87/32']
        assert actual == expected

    finally:
        m_nodes.delete_custom_envs()


def test_get_table_filter_role():
    m_table = models.tables.Table(sub_id, ds_full)

    filters = [models.filters.MaskFilter(True, '10'), models.filters.RoleFilter(True, '>', '0.4999')]
    rows = m_table.get_table_info(filters, page=0, page_size=100, order_by=0, order_dir='asc')
    addrA = [x['address'] for x in rows]
    assert len(rows) == 7

    filters = [models.filters.MaskFilter(True, '10'), models.filters.RoleFilter(True, '<', '0.4999')]
    rows = m_table.get_table_info(filters, page=0, page_size=100, order_by=0, order_dir='asc')
    addrB = [x['address'] for x in rows]
    assert len(rows) == 8
    assert len(set(addrA) & set(addrB)) == 0


def test_get_table_filter_protocol():
    m_table = models.tables.Table(sub_id, ds_full)

    # receives $protocol traffic
    filters = [models.filters.MaskFilter(True, '10'), models.filters.ProtocolFilter(True, '0', 'TCP')]
    rows = m_table.get_table_info(filters, page=0, page_size=100, order_by=0, order_dir='asc')
    addresses = [x['address'] for x in rows]
    expected = [u'10.0.0.0/8', u'10.20.0.0/16', u'10.20.30.0/24', u'10.20.30.40/32',
                u'10.20.30.41/32', u'10.20.32.0/24', u'10.20.32.42/32', u'10.20.32.43/32',
                u'10.24.0.0/16', u'10.24.34.0/24', u'10.24.34.44/32', u'10.24.34.45/32',
                u'10.24.36.0/24', u'10.24.36.46/32', u'10.24.36.47/32']
    assert addresses == expected

    # doesn't receives $protocol traffic
    filters = [models.filters.MaskFilter(True, '150'), models.filters.ProtocolFilter(True, '1', 'TCP')]
    rows = m_table.get_table_info(filters, page=0, page_size=100, order_by=0, order_dir='asc')
    addresses = [x['address'] for x in rows]
    expected = [u'150.0.0.0/8', u'150.60.0.0/16', u'150.60.70.0/24', u'150.60.70.80/32',
                u'150.60.70.81/32', u'150.60.72.0/24', u'150.60.72.82/32', u'150.60.72.83/32',
                u'150.64.0.0/16', u'150.64.74.0/24', u'150.64.74.84/32', u'150.64.74.85/32',
                u'150.64.76.0/24', u'150.64.76.86/32', u'150.64.76.87/32']
    assert addresses == expected

    # sends $protocol traffic
    filters = [models.filters.MaskFilter(True, '110'), models.filters.ProtocolFilter(True, '2', 'TCP')]
    rows = m_table.get_table_info(filters, page=0, page_size=100, order_by=0, order_dir='asc')
    addresses = [x['address'] for x in rows]
    expected = [u'110.0.0.0/8', u'110.20.0.0/16', u'110.20.30.0/24', u'110.20.30.40/32']
    assert addresses == expected

    # DOESN'T send $protocol traffic
    filters = [models.filters.MaskFilter(True, '110'), models.filters.ProtocolFilter(True, '3', 'TCP')]
    rows = m_table.get_table_info(filters, page=0, page_size=100, order_by=0, order_dir='asc')
    addresses = [x['address'] for x in rows]
    expected = [u'110.20.30.41/32', u'110.20.32.0/24', u'110.20.32.42/32', u'110.20.32.43/32',
                u'110.24.0.0/16', u'110.24.34.0/24', u'110.24.34.44/32', u'110.24.34.45/32',
                u'110.24.36.0/24', u'110.24.36.46/32', u'110.24.36.47/32']
    assert addresses == expected
