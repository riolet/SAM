import dbaccess
import common
import web
import filters

page = 0
page_size = 10
order_by = 0
order_dir = 'desc'


def is_sorted(data, keyGetter, dir):
    if len(data) < 2:
        return True

    old_key = keyGetter(data[0])

    if dir == 'desc':
        for item in data[1:]:
            new_key = keyGetter(item)
            if new_key > old_key:
                return False
            old_key = new_key
    else:
        for item in data[1:]:
            new_key = keyGetter(item)
            if new_key < old_key:
                return False
            old_key = new_key
    return True


def test_empty():
    table_data = dbaccess.get_table_info([], page, page_size, order_by, order_dir)
    assert len(table_data) == page_size + 1
    assert type(table_data[0]) == web.utils.storage # like a dict


def test_one_filter():
    filters1 = filters.readEncoded("0;1;<;i;1000")
    filters2 = filters.readEncoded("0;1;>;i;1000")
    filters3 = filters.readEncoded("0;1;<;o;1000")

    table_data = dbaccess.get_table_info(filters1, page, page_size, order_by, order_dir)
    assert all([row['conn_in'] < 1000 for row in table_data])
    table_data = dbaccess.get_table_info(filters2, page, page_size, order_by, order_dir)
    assert all([row['conn_in'] > 1000 for row in table_data])
    table_data = dbaccess.get_table_info(filters3, page, page_size, order_by, order_dir)
    assert all([row['conn_out'] < 1000 for row in table_data])


def test_many_filters():
    clauses = filters.readEncoded("0;1;<;i;1000|5;1;32|4;1;<;0.8|4;1;>;0.2")
    table_data = dbaccess.get_table_info(clauses, page, page_size, order_by, order_dir)
    assert all([row['conn_in'] < 1000 for row in table_data])
    assert all([row['address'].endswith("/32") for row in table_data])
    assert all([(float(row['conn_in']) / (float(row['conn_in']) + float(row['conn_out']))) > 0.2
         for row in table_data])
    assert all([(float(row['conn_in']) / (float(row['conn_in']) + float(row['conn_out']))) < 0.8
         for row in table_data])


def test_order():
    # ['address', 'alias', 'role', 'environment', 'tags', 'bytes', 'packets']
    table_data = dbaccess.get_table_info([], page, page_size, 0, 'desc')
    assert is_sorted(table_data, lambda x: common.IPStringtoInt(x['address']), 'desc')
    table_data = dbaccess.get_table_info([], page, page_size, 0, 'asc')
    assert is_sorted(table_data, lambda x: common.IPStringtoInt(x['address']), 'asc')
    table_data = dbaccess.get_table_info([], page, page_size, 5, 'desc')
    assert is_sorted(table_data, lambda x: x['bytes_in'] + x['bytes_out'], 'desc')
    table_data = dbaccess.get_table_info([], page, page_size, 5, 'asc')
    assert is_sorted(table_data, lambda x: x['bytes_in'] + x['bytes_out'], 'asc')


def test_pagination():
    table_data_0 = dbaccess.get_table_info([], 0, page_size, 5, 'desc')
    table_data_1 = dbaccess.get_table_info([], 1, page_size, 5, 'desc')
    table_data_2 = dbaccess.get_table_info([], 2, page_size, 5, 'desc')
    assert is_sorted(table_data_0, lambda x: x['bytes_in'] + x['bytes_out'], 'desc')
    assert is_sorted(table_data_1, lambda x: x['bytes_in'] + x['bytes_out'], 'desc')
    assert is_sorted(table_data_2, lambda x: x['bytes_in'] + x['bytes_out'], 'desc')
    assert is_sorted(table_data_0 + table_data_1 + table_data_2,
                     lambda x: x['bytes_in'] + x['bytes_out'], 'desc')


def test_page_size():
    p_size = 10
    table_data = dbaccess.get_table_info([], page, p_size, order_by, order_dir)
    assert len(table_data) == p_size + 1
    p_size = 40
    table_data = dbaccess.get_table_info([], page, p_size, order_by, order_dir)
    assert len(table_data) == p_size + 1
    p_size = 20
    table_data = dbaccess.get_table_info([], page, p_size, order_by, order_dir)
    assert len(table_data) == p_size + 1

