import dbaccess
from datetime import datetime
import time
import common


def test_parse_sql():
    expected = ['DROP TABLE IF EXISTS myKey_blah',
                '\n \n \n CREATE TABLE IF NOT EXISTS myKey_blah\n'
                ' (port              INT UNSIGNED NOT NULL\n'
                ' ,CONSTRAINT PKportAliasLUT PRIMARY KEY (port)\n'
                ' )',
                '\n \n SELECT * FROM myKey_blah\n ']
    replacements = {'id': "myKey"}
    actual = dbaccess.parse_sql_file("./spec/python/test_sql.sql", replacements)
    print actual
    assert actual == expected


# def test_reset_port_names:
#     ???

def test_get_nodes_0():
    assert len(dbaccess.get_nodes()) == 8


def test_get_nodes_1():
    assert len(dbaccess.get_nodes(21)) == 1
    assert len(dbaccess.get_nodes(52)) == 0


def test_get_nodes_2():
    assert len(dbaccess.get_nodes(21, 66)) == 80


def test_get_nodes_3():
    assert len(dbaccess.get_nodes(21, 66, 1)) == 5


def test_get_links_in_plain():
    # connections into 79.0.0.0/8
    rows = dbaccess.get_links_in(79)
    assert sorted(rows[0].keys()) == ['dst_end', 'dst_start', 'links', 'src_end', 'src_start']
    simple = [(common.IPtoString(row.src_start), int(row.links)) for row in rows]
    assert simple == [('21.0.0.0', 24937), ('53.0.0.0', 9), ('79.0.0.0', 172), ('110.0.0.0', 4566), ('189.0.0.0', 9688)]

    # connections into 79.146.0.0/16
    rows = dbaccess.get_links_in(79, 146)
    assert sorted(rows[0].keys()) == ['dst_end', 'dst_start', 'links', 'src_end', 'src_start']
    simple = [(common.IPtoString(row.src_start), int(row.links)) for row in rows]
    assert simple == [('21.0.0.0', 2815), ('110.0.0.0', 166), ('189.0.0.0', 6)]

    # connections into 79.146.149.0/24
    rows = dbaccess.get_links_in(79, 146, 149)
    assert sorted(rows[0].keys()) == ['dst_end', 'dst_start', 'links', 'src_end', 'src_start']
    simple = [(common.IPtoString(row.src_start), int(row.links)) for row in rows]
    assert simple == [('21.0.0.0', 393), ('189.0.0.0', 6)]

    # connections into 79.146.149.40
    rows = dbaccess.get_links_in(79, 146, 149, 40)
    assert len(rows) == 20
    assert sorted(rows[0].keys()) == ['dst_end', 'dst_start', 'links', 'port', 'src_end', 'src_start']
    simple = [(common.IPtoString(row.src_start), int(row.port), int(row.links)) for row in rows]
    assert simple == [('21.0.0.0', 80, 8), ('21.0.0.0', 280, 4), ('21.0.0.0', 411, 4), ('21.0.0.0', 427, 1),
                      ('21.0.0.0', 443, 4), ('21.0.0.0', 1024, 4), ('21.0.0.0', 1311, 4), ('21.0.0.0', 2069, 4),
                      ('21.0.0.0', 3202, 4), ('21.0.0.0', 3257, 4), ('21.0.0.0', 4095, 4), ('21.0.0.0', 4096, 4),
                      ('21.0.0.0', 5989, 3), ('21.0.0.0', 8000, 4), ('21.0.0.0', 8008, 4), ('21.0.0.0', 8222, 4),
                      ('21.0.0.0', 8443, 4), ('21.0.0.0', 9990, 4), ('21.0.0.0', 9991, 4), ('189.0.0.0', 2434, 6)]


def test_get_links_out_plain():
    # connections into 21.0.0.0/8
    rows = dbaccess.get_links_out(21)
    assert sorted(rows[0].keys()) == ['dst_end', 'dst_start', 'links', 'src_end', 'src_start']
    simple = [(common.IPtoString(row.dst_start), int(row.links)) for row in rows]
    assert [('21.0.0.0', 20324), ('79.0.0.0', 24937), ('189.0.0.0', 460)]

    # connections into 21.66.0.0/16
    rows = dbaccess.get_links_out(21, 66)
    assert sorted(rows[0].keys()) == ['dst_end', 'dst_start', 'links', 'src_end', 'src_start']
    simple = [(common.IPtoString(row.dst_start), int(row.links)) for row in rows]
    assert simple == [('21.66.0.0', 20324), ('79.0.0.0', 24937), ('189.0.0.0', 460)]

    # connections into 21.66.138.0/24
    rows = dbaccess.get_links_out(21, 66, 138)
    assert sorted(rows[0].keys()) == ['dst_end', 'dst_start', 'links', 'src_end', 'src_start']
    simple = [(common.IPtoString(row.dst_start), int(row.links)) for row in rows]
    assert simple == [('21.66.10.0', 2), ('21.66.141.0', 1), ('79.0.0.0', 11)]

    # connections into 21.66.138.188
    rows = dbaccess.get_links_out(21, 66, 138, 188)
    assert len(rows) == 3
    assert sorted(rows[0].keys()) == ['dst_end', 'dst_start', 'links', 'port', 'src_end', 'src_start']
    simple = [(common.IPtoString(row.dst_start), int(row.port), int(row.links)) for row in rows]
    assert simple == [('79.0.0.0', 22, 4), ('79.0.0.0', 5414, 3), ('79.0.0.0', 9519, 3)]


def test_get_links_out_filter():
    test_port = 12345

    rows = dbaccess.get_links_out(21, 66, 42, 22, port_filter=test_port)
    assert sorted(rows[0].keys()) == ['dst_end', 'dst_start', 'links', 'port', 'src_end', 'src_start']
    ports = set([int(i.port) for i in rows])
    assert ports == {test_port}
    assert len(rows) == 5

    rows = dbaccess.get_links_out(21, 66, port_filter=test_port)
    assert sorted(rows[0].keys()) == ['dst_end', 'dst_start', 'links', 'src_end', 'src_start']
    assert len(rows) == 2
    rows = dbaccess.get_links_out(21, 66)
    assert len(rows) == 3


def make_timestamp(ts):
    d = datetime.strptime(ts, "%Y-%m-%d %H:%M")
    ts = time.mktime(d.timetuple())
    return int(ts)


def test_get_links_out_timerange():
    time_all = (1, 2 ** 31 - 1)
    time_crop = (make_timestamp('2016-06-21 17:10'), make_timestamp('2016-06-21 18:05'))
    time_tiny = (make_timestamp('2016-06-21 17:45'), make_timestamp('2016-06-21 17:50'))

    rows = dbaccess.get_links_out(21, 66, 42, 22, timerange=time_all)
    assert len(rows) == 5
    rows = dbaccess.get_links_out(21, 66, 42, 22, timerange=time_crop)
    assert len(rows) == 5
    rows = dbaccess.get_links_out(21, 66, 42, 22, timerange=time_tiny)
    assert len(rows) == 4

    rows = dbaccess.get_links_out(21, 66, timerange=time_all)
    assert len(rows) == 3
    rows = dbaccess.get_links_out(21, 66, timerange=time_crop)
    assert len(rows) == 3
    rows = dbaccess.get_links_out(21, 66, timerange=time_tiny)
    assert len(rows) == 3


def test_get_details_summary():
    details = dbaccess.get_details_summary(common.determine_range(21))
    assert details['unique_in'] == 9311
    assert details['unique_out'] == 468
    assert details['unique_ports'] == 94

    details = dbaccess.get_details_summary(common.determine_range(21, 66))
    assert details['unique_in'] == 9311
    assert details['unique_out'] == 468
    assert details['unique_ports'] == 94

    details = dbaccess.get_details_summary(common.determine_range(21, 66, 10))
    assert details['unique_in'] == 2503
    assert details['unique_out'] == 1
    assert details['unique_ports'] == 38

    details = dbaccess.get_details_summary(common.determine_range(21, 66, 10, 70))
    assert details['unique_in'] == 16
    assert details['unique_out'] == 0
    assert details['unique_ports'] == 13

    details = dbaccess.get_details_summary(common.determine_range(21, 66, 40, 231))
    assert details['unique_in'] == 7
    assert details['unique_out'] == 4
    assert details['unique_ports'] == 1


def test_get_details_summary_ports():
    iprange = common.determine_range(21, 66, 40, 231)
    details = dbaccess.get_details_summary(iprange, port=445)
    assert details['unique_in'] == 7
    assert details['unique_out'] == 0
    assert details['unique_ports'] == 1

    details = dbaccess.get_details_summary(iprange, port=80)
    assert details['unique_in'] == 0
    assert details['unique_out'] == 2
    assert details['unique_ports'] == 0

    details = dbaccess.get_details_summary(iprange, port=1)
    assert details['unique_in'] == 0
    assert details['unique_out'] == 0
    assert details['unique_ports'] == 0


def test_get_details_summary_timerange():
    time_all = (1, 2 ** 31 - 1)
    time_crop = (make_timestamp('2016-06-21 17:10'), make_timestamp('2016-06-21 18:05'))
    time_tiny = (make_timestamp('2016-06-21 17:45'), make_timestamp('2016-06-21 17:50'))
    iprange = common.determine_range(21, 66, 40, 231)
    iprange2 = common.determine_range(79, 35, 103, 221)

    details = dbaccess.get_details_summary(iprange, timestamp_range=time_all)
    assert details['unique_in'] == 7
    assert details['unique_out'] == 4
    assert details['unique_ports'] == 1

    details = dbaccess.get_details_summary(iprange, timestamp_range=time_crop)
    assert details['unique_in'] == 7
    assert details['unique_out'] == 4
    assert details['unique_ports'] == 1

    details = dbaccess.get_details_summary(iprange2, timestamp_range=time_crop)
    assert details['unique_in'] == 1
    assert details['unique_out'] == 0
    assert details['unique_ports'] == 1

    details = dbaccess.get_details_summary(iprange, timestamp_range=time_tiny)
    assert details['unique_in'] == 3
    assert details['unique_out'] == 3
    assert details['unique_ports'] == 1


def test_get_details_conn():
    details = dbaccess.get_details_connections(common.determine_range(21), True)
    assert len(details) == 50
    details = dbaccess.get_details_connections(common.determine_range(21), False)
    assert len(details) == 50

    details = dbaccess.get_details_connections(common.determine_range(21, 66), True)
    assert len(details) == 50
    details = dbaccess.get_details_connections(common.determine_range(21, 66), False)
    assert len(details) == 50

    details = dbaccess.get_details_connections(common.determine_range(21, 66, 10), True)
    assert len(details) == 50
    details = dbaccess.get_details_connections(common.determine_range(21, 66, 10), False)
    assert len(details) == 1

    details = dbaccess.get_details_connections(common.determine_range(21, 66, 10, 70), True)
    assert len(details) == 31
    details = dbaccess.get_details_connections(common.determine_range(21, 66, 10, 70), False)
    assert len(details) == 0

    details = dbaccess.get_details_connections(common.determine_range(21, 66, 40, 231), True)
    assert len(details) == 7
    details = dbaccess.get_details_connections(common.determine_range(21, 66, 40, 231), False)
    assert len(details) == 9


def test_get_details_conn_ports():
    ip = common.determine_range(21, 66, 40, 231)
    details = dbaccess.get_details_connections(ip, True, port=445)
    assert len(details) == 7
    details = dbaccess.get_details_connections(ip, False, port=445)
    assert len(details) == 0

    details = dbaccess.get_details_connections(ip, True, port=80)
    assert len(details) == 0
    details = dbaccess.get_details_connections(ip, False, port=80)
    assert len(details) == 2

    details = dbaccess.get_details_connections(ip, True, port=1)
    assert len(details) == 0
    details = dbaccess.get_details_connections(ip, False, port=1)
    assert len(details) == 0


def test_get_details_conn_timerange():
    time_all = (1, 2 ** 31 - 1)
    time_crop = (make_timestamp('2016-06-21 17:10'), make_timestamp('2016-06-21 18:05'))
    time_tiny = (make_timestamp('2016-06-21 17:45'), make_timestamp('2016-06-21 17:50'))
    ip1 = common.determine_range(21, 66, 40, 231)
    ip2 = common.determine_range(79, 35, 103, 221)

    details = dbaccess.get_details_connections(ip1, True, timestamp_range=time_all)
    assert len(details) == 7
    details = dbaccess.get_details_connections(ip1, False, timestamp_range=time_all)
    assert len(details) == 9

    details = dbaccess.get_details_connections(ip1, True, timestamp_range=time_crop)
    assert len(details) == 7
    details = dbaccess.get_details_connections(ip1, False, timestamp_range=time_crop)
    assert len(details) == 9

    details = dbaccess.get_details_connections(ip1, True, timestamp_range=time_tiny)
    assert len(details) == 3
    details = dbaccess.get_details_connections(ip1, False, timestamp_range=time_tiny)
    assert len(details) == 7

    details = dbaccess.get_details_connections(ip2, True, timestamp_range=time_crop)
    assert len(details) == 1
    details = dbaccess.get_details_connections(ip2, False, timestamp_range=time_crop)
    assert len(details) == 0


def test_get_details_ports():
    time_all = (1, 2 ** 31 - 1)
    time_crop = (make_timestamp('2016-06-21 17:10'), make_timestamp('2016-06-21 18:05'))
    time_tiny = (make_timestamp('2016-06-21 17:45'), make_timestamp('2016-06-21 17:50'))
    ip1 = common.determine_range(21, 66, 40, 231)
    ip2 = common.determine_range(79, 35, 103, 221)

    details = dbaccess.get_details_ports(common.determine_range(21))
    assert len(details) == 50
    details = dbaccess.get_details_ports(common.determine_range(21, 66))
    assert len(details) == 50
    details = dbaccess.get_details_ports(common.determine_range(21, 66, 10))
    assert len(details) == 38
    details = dbaccess.get_details_ports(common.determine_range(21, 66, 10, 70))
    assert len(details) == 13
    details = dbaccess.get_details_ports(ip1)
    assert len(details) == 1

    details = dbaccess.get_details_ports(ip1, port=445)
    assert len(details) == 1
    details = dbaccess.get_details_ports(ip1, port=80)
    assert len(details) == 0
    details = dbaccess.get_details_ports(ip1, port=1)
    assert len(details) == 0

    details = dbaccess.get_details_ports(ip1, timestamp_range=time_all)
    assert len(details) == 1
    details = dbaccess.get_details_ports(ip1, timestamp_range=time_crop)
    assert len(details) == 1
    details = dbaccess.get_details_ports(ip1, timestamp_range=time_tiny)
    assert len(details) == 1
    details = dbaccess.get_details_ports(ip2, timestamp_range=time_crop)
    assert len(details) == 1


def test_get_node_info():
    # dbaccess.get_node_info("21")
    assert 1 == 1


def test_set_node_info():
    # get old info
    # set some new random
    # assert info was recorded.
    # reset old info

    # dbaccess.set_node_info("21", info)
    assert 1 == 1


def test_get_port_info_present():
    port_info = list(dbaccess.get_port_info(80))
    assert len(port_info) == 1
    info = port_info[0]
    assert info.name == 'http'
    assert info.description == 'World Wide Web HTTP'
    assert info.port == 80
    assert sorted(info.keys()) == ['active', 'alias_description', 'alias_name', 'description', 'name', 'port']


def test_get_port_info_absent():
    port_info = list(dbaccess.get_port_info(4))
    assert port_info == []


def test_get_port_info_many():
    port_info = list(dbaccess.get_port_info([3, 4, 5, 6]))
    assert len(port_info) == 2
    info3 = port_info[0]
    info5 = port_info[1]
    assert info3.port == 3
    assert info3.name == 'compressne'
    assert info5.port == 5
    assert info5.name == 'rje'


def test_set_port_info():
    test_port = 1
    try:
        # set data for port 1
        dbaccess.set_port_info({
            'port': test_port,
            'alias_name': "override",
            'alias_description': "lorem ipsum",
            'active': '0'
        })
        pinfo = list(dbaccess.get_port_info(test_port))
        assert len(pinfo) == 1
        assert pinfo[0]['name'] == "tcpmux"
        assert pinfo[0]['description'] == "TCP Port Service Multiplexer"
        assert pinfo[0]['alias_name'] == "override"
        assert pinfo[0]['alias_description'] == "lorem ipsum"
        assert pinfo[0]['active'] == 0
    except AssertionError as e:
        raise e
    finally:
        # clear data for test_port
        common.db.update("Ports", where="port={0}".format(test_port), active=1)
        common.db.delete("PortAliases", where="port={0}".format(test_port))

    test_port = 4
    try:
        # set data for port 4
        dbaccess.set_port_info({
            'port': test_port,
            'alias_name': "this_name_is_too_long",
            'alias_description': "phony port details",
            'active': '0'
        })
        pinfo = list(dbaccess.get_port_info(test_port))
        assert len(pinfo) == 1
        assert pinfo[0]['name'] == ""
        assert pinfo[0]['description'] == ""
        assert pinfo[0]['alias_name'] == "this_name_"
        assert pinfo[0]['alias_description'] == "phony port details"
        assert pinfo[0]['active'] == 0
    except AssertionError as e:
        raise e
    finally:
        # clear data for test_port
        common.db.delete("Ports", where="port={0}".format(test_port))
        common.db.delete("PortAliases", where="port={0}".format(test_port))
