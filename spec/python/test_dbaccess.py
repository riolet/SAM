import dbaccess
from datetime import datetime
import time
import common


# def test_test_database():
# def test_create_database():


def test_parse_sql_file():
    expected = ['DROP TABLE IF EXISTS blah',
                '\n \n \n CREATE TABLE IF NOT EXISTS blah\n'
                ' (port              INT UNSIGNED NOT NULL\n'
                ' ,CONSTRAINT PKportAliasLUT PRIMARY KEY (port)\n'
                ' )',
                '\n \n SELECT * FROM blah\n ']
    assert dbaccess.parse_sql_file("./spec/python/test_sql.sql") == expected

# def test_exec_sql():
# def test_reset_port_names():


def test_get_timerange():
    expected = {'max': 1466557500.0, 'min': 1466554200.0}
    actual = dbaccess.get_timerange()
    assert expected == actual


def test_get_nodes():
    assert len(dbaccess.get_nodes(0, 0xffffffff)) == 8
    ipstart, ipend, _ = common.determine_range(21)
    assert len(dbaccess.get_nodes(ipstart, ipend)) == 1
    ipstart, ipend, _ = common.determine_range(52)
    assert len(dbaccess.get_nodes(ipstart, ipend)) == 0
    ipstart, ipend, _ = common.determine_range(21, 66)
    assert len(dbaccess.get_nodes(ipstart, ipend)) == 110
    ipstart, ipend, _ = common.determine_range(21, 66, 1)
    assert len(dbaccess.get_nodes(ipstart, ipend)) == 5


def test_get_links_in_plain():
    # connections into 79.0.0.0/8
    ip_start, ip_end, _ = common.determine_range(79)
    rows = dbaccess.get_links(ip_start, ip_end, inbound=True)
    assert sorted(rows[0].keys()) == ['dst_end', 'dst_start', 'links', 'src_end', 'src_start']
    simple = [(common.IPtoString(row.src_start), int(row.links)) for row in rows]
    assert simple == [('21.0.0.0', 100484), ('53.0.0.0', 9), ('79.0.0.0', 1950), ('110.0.0.0', 4585), ('189.0.0.0', 10501)]

    # connections into 79.146.0.0/16
    ip_start, ip_end, _ = common.determine_range(79, 146)
    rows = dbaccess.get_links(ip_start, ip_end, inbound=True)
    assert sorted(rows[0].keys()) == ['dst_end', 'dst_start', 'links', 'src_end', 'src_start']
    simple = [(common.IPtoString(row.src_start), int(row.links)) for row in rows]
    assert simple == [('21.0.0.0', 51686), ('79.229.0.0', 21), ('110.0.0.0', 166), ('189.0.0.0', 340)]

    # connections into 79.146.149.0/24
    ip_start, ip_end, _ = common.determine_range(79, 146, 149)
    rows = dbaccess.get_links(ip_start, ip_end, inbound=True)
    assert sorted(rows[0].keys()) == ['dst_end', 'dst_start', 'links', 'src_end', 'src_start']
    simple = [(common.IPtoString(row.src_start), int(row.links)) for row in rows]
    assert simple == [('21.0.0.0', 714), ('189.0.0.0', 6)]

    # connections into 79.146.149.40
    ip_start, ip_end, _ = common.determine_range(79, 146, 149, 40)
    rows = dbaccess.get_links(ip_start, ip_end, inbound=True)
    assert len(rows) == 21
    assert sorted(rows[0].keys()) == ['dst_end', 'dst_start', 'links', 'port', 'src_end', 'src_start']
    simple = [(common.IPtoString(row.src_start), int(row.port), int(row.links)) for row in rows]
    assert simple == [('21.0.0.0', 80, 8), ('21.0.0.0', 161, 9), ('21.0.0.0', 280, 4), ('21.0.0.0', 411, 4),
                      ('21.0.0.0', 427, 1), ('21.0.0.0', 443, 4), ('21.0.0.0', 1024, 4), ('21.0.0.0', 1311, 4),
                      ('21.0.0.0', 2069, 4), ('21.0.0.0', 3202, 4), ('21.0.0.0', 3257, 4), ('21.0.0.0', 4095, 4),
                      ('21.0.0.0', 4096, 4), ('21.0.0.0', 5989, 3), ('21.0.0.0', 8000, 4), ('21.0.0.0', 8008, 4),
                      ('21.0.0.0', 8222, 4), ('21.0.0.0', 8443, 4), ('21.0.0.0', 9990, 4), ('21.0.0.0', 9991, 4),
                      ('189.0.0.0', 2434, 6)]


def test_get_links_out_plain():
    # connections into 21.0.0.0/8
    ip_start, ip_end, _ = common.determine_range(21)
    rows = dbaccess.get_links(ip_start, ip_end, inbound=False)
    assert sorted(rows[0].keys()) == ['dst_end', 'dst_start', 'links', 'src_end', 'src_start']
    simple = [(common.IPtoString(row.dst_start), int(row.links)) for row in rows]
    assert simple == [('21.0.0.0', 55381), ('79.0.0.0', 100484), ('110.0.0.0', 2), ('189.0.0.0', 653)]

    # connections into 21.66.0.0/16
    ip_start, ip_end, _ = common.determine_range(21, 66)
    rows = dbaccess.get_links(ip_start, ip_end, inbound=False)
    assert sorted(rows[0].keys()) == ['dst_end', 'dst_start', 'links', 'src_end', 'src_start']
    simple = [(common.IPtoString(row.dst_start), int(row.links)) for row in rows]
    assert simple == [('21.66.0.0', 55381), ('79.0.0.0', 100484), ('110.0.0.0', 2), ('189.0.0.0', 653)]

    # connections into 21.66.138.0/24
    ip_start, ip_end, _ = common.determine_range(21, 66, 138)
    rows = dbaccess.get_links(ip_start, ip_end, inbound=False)
    assert sorted(rows[0].keys()) == ['dst_end', 'dst_start', 'links', 'src_end', 'src_start']
    simple = [(common.IPtoString(row.dst_start), int(row.links)) for row in rows]
    assert simple == [('21.66.10.0', 111), ('21.66.81.0', 1), ('21.66.116.0', 3), ('21.66.121.0', 44),
                      ('21.66.141.0', 1), ('21.66.159.0', 2), ('21.66.237.0', 1), ('79.0.0.0', 1840)]

    # connections into 21.66.138.188
    ip_start, ip_end, _ = common.determine_range(21, 66, 138, 188)
    rows = dbaccess.get_links(ip_start, ip_end, inbound=False)
    assert len(rows) == 3
    assert sorted(rows[0].keys()) == ['dst_end', 'dst_start', 'links', 'port', 'src_end', 'src_start']
    simple = [(common.IPtoString(row.dst_start), int(row.port), int(row.links)) for row in rows]
    assert simple == [('79.0.0.0', 22, 4), ('79.0.0.0', 5414, 3), ('79.0.0.0', 9519, 3)]


def test_get_links_out_filter():
    test_port = 12345
    ip_start, ip_end, _ = common.determine_range(21, 66, 42, 22)
    rows = dbaccess.get_links(ip_start, ip_end, inbound=False, port_filter=test_port)
    assert sorted(rows[0].keys()) == ['dst_end', 'dst_start', 'links', 'port', 'src_end', 'src_start']
    ports = set([int(i.port) for i in rows])
    assert ports == {test_port}
    assert len(rows) == 5

    ip_start, ip_end, _ = common.determine_range(21, 66)
    rows = dbaccess.get_links(ip_start, ip_end, inbound=False, port_filter=test_port)
    assert sorted(rows[0].keys()) == ['dst_end', 'dst_start', 'links', 'src_end', 'src_start']
    assert len(rows) == 2


def make_timestamp(ts):
    d = datetime.strptime(ts, "%Y-%m-%d %H:%M")
    ts = time.mktime(d.timetuple())
    return int(ts)


def test_get_links_out_timerange():
    time_all = (1, 2 ** 31 - 1)
    time_crop = (make_timestamp('2016-06-21 17:10'), make_timestamp('2016-06-21 18:05'))
    time_tiny = (make_timestamp('2016-06-21 17:45'), make_timestamp('2016-06-21 17:50'))
    ip_start, ip_end, _ = common.determine_range(21, 66, 42, 22)

    rows = dbaccess.get_links(ip_start, ip_end, inbound=False, timerange=time_all)
    assert len(rows) == 5
    rows = dbaccess.get_links(ip_start, ip_end, inbound=False, timerange=time_crop)
    assert len(rows) == 5
    rows = dbaccess.get_links(ip_start, ip_end, inbound=False, timerange=time_tiny)
    assert len(rows) == 4

    ip_start, ip_end, _ = common.determine_range(21, 66)
    rows = dbaccess.get_links(ip_start, ip_end, inbound=False, timerange=time_all)
    assert len(rows) == 4
    rows = dbaccess.get_links(ip_start, ip_end, inbound=False, timerange=time_crop)
    assert len(rows) == 4
    rows = dbaccess.get_links(ip_start, ip_end, inbound=False, timerange=time_tiny)
    assert len(rows) == 3


def test_get_details_summary():
    details = dbaccess.get_details_summary(*common.determine_range(21)[:2])
    assert details['unique_in'] == 13322L
    assert details['unique_out'] == 2398L
    assert details['unique_ports'] == 20370L

    details = dbaccess.get_details_summary(*common.determine_range(21, 66)[:2])
    assert details['unique_in'] == 13322L
    assert details['unique_out'] == 2398L
    assert details['unique_ports'] == 20370L

    details = dbaccess.get_details_summary(*common.determine_range(21, 66, 10)[:2])
    assert details['unique_in'] == 2798L
    assert details['unique_out'] == 1
    assert details['unique_ports'] == 3463L

    details = dbaccess.get_details_summary(*common.determine_range(21, 66, 10, 70)[:2])
    assert details['unique_in'] == 28
    assert details['unique_out'] == 0
    assert details['unique_ports'] == 29

    details = dbaccess.get_details_summary(*common.determine_range(21, 66, 40, 231)[:2])
    assert details['unique_in'] == 7
    assert details['unique_out'] == 30
    assert details['unique_ports'] == 1


def test_get_details_summary_ports():
    ip_start, ip_end, _ = common.determine_range(21, 66, 40, 231)
    details = dbaccess.get_details_summary(ip_start, ip_end, port=445)
    assert details['unique_in'] == 7
    assert details['unique_out'] == 0
    assert details['unique_ports'] == 1

    details = dbaccess.get_details_summary(ip_start, ip_end, port=80)
    assert details['unique_in'] == 0
    assert details['unique_out'] == 2
    assert details['unique_ports'] == 0

    details = dbaccess.get_details_summary(ip_start, ip_end, port=1)
    assert details['unique_in'] == 0
    assert details['unique_out'] == 0
    assert details['unique_ports'] == 0


def test_get_details_summary_timerange():
    time_all = (1, 2 ** 31 - 1)
    time_crop = (make_timestamp('2016-06-21 17:10'), make_timestamp('2016-06-21 18:05'))
    time_tiny = (make_timestamp('2016-06-21 17:45'), make_timestamp('2016-06-21 17:50'))
    ip_start, ip_end, _ = common.determine_range(21, 66, 40, 231)
    ip_start2, ip_end2, _ = common.determine_range(79, 35, 103, 221)

    details = dbaccess.get_details_summary(ip_start, ip_end, timestamp_range=time_all)
    assert details['unique_in'] == 7
    assert details['unique_out'] == 30
    assert details['unique_ports'] == 1

    details = dbaccess.get_details_summary(ip_start, ip_end, timestamp_range=time_crop)
    assert details['unique_in'] == 7
    assert details['unique_out'] == 30
    assert details['unique_ports'] == 1

    details = dbaccess.get_details_summary(ip_start2, ip_end2, timestamp_range=time_crop)
    assert details['unique_in'] == 1
    assert details['unique_out'] == 0
    assert details['unique_ports'] == 1

    details = dbaccess.get_details_summary(ip_start, ip_end, timestamp_range=time_tiny)
    assert details['unique_in'] == 3
    assert details['unique_out'] == 15
    assert details['unique_ports'] == 1


def test_get_details_conn():
    ipstart, ipend, _ = common.determine_range(21)
    details = dbaccess.get_details_connections(ipstart, ipend, True)
    assert len(details) == 50
    details = dbaccess.get_details_connections(ipstart, ipend, False)
    assert len(details) == 50

    ipstart, ipend, _ = common.determine_range(21, 66)
    details = dbaccess.get_details_connections(ipstart, ipend, True)
    assert len(details) == 50
    details = dbaccess.get_details_connections(ipstart, ipend, False)
    assert len(details) == 50

    ipstart, ipend, _ = common.determine_range(21, 66, 10)
    details = dbaccess.get_details_connections(ipstart, ipend, True)
    assert len(details) == 50
    details = dbaccess.get_details_connections(ipstart, ipend, False)
    assert len(details) == 1

    ipstart, ipend, _ = common.determine_range(21, 66, 10, 70)
    details = dbaccess.get_details_connections(ipstart, ipend, True)
    assert len(details) == 50
    details = dbaccess.get_details_connections(ipstart, ipend, False)
    assert len(details) == 0

    ipstart, ipend, _ = common.determine_range(21, 66, 40, 231)
    details = dbaccess.get_details_connections(ipstart, ipend, True)
    assert len(details) == 7
    details = dbaccess.get_details_connections(ipstart, ipend, False)
    assert len(details) == 50


def test_get_details_conn_ports():
    ipstart, ipend, _ = common.determine_range(21, 66, 40, 231)
    details = dbaccess.get_details_connections(ipstart, ipend, True, port=445)
    assert len(details) == 7
    details = dbaccess.get_details_connections(ipstart, ipend, False, port=445)
    assert len(details) == 0

    details = dbaccess.get_details_connections(ipstart, ipend, True, port=80)
    assert len(details) == 0
    details = dbaccess.get_details_connections(ipstart, ipend, False, port=80)
    assert len(details) == 2

    details = dbaccess.get_details_connections(ipstart, ipend, True, port=1)
    assert len(details) == 0
    details = dbaccess.get_details_connections(ipstart, ipend, False, port=1)
    assert len(details) == 0


def test_get_details_conn_timerange():
    time_all = (1, 2 ** 31 - 1)
    time_crop = (make_timestamp('2016-06-21 17:10'), make_timestamp('2016-06-21 18:05'))
    time_tiny = (make_timestamp('2016-06-21 17:45'), make_timestamp('2016-06-21 17:50'))
    ipstart, ipend, _ = common.determine_range(21, 66, 40, 231)
    ipstart2, ipend2, _ = common.determine_range(79, 35, 103, 221)

    details = dbaccess.get_details_connections(ipstart, ipend, True, timestamp_range=time_all)
    assert len(details) == 7
    details = dbaccess.get_details_connections(ipstart, ipend, False, timestamp_range=time_all)
    assert len(details) == 50

    details = dbaccess.get_details_connections(ipstart, ipend, True, timestamp_range=time_crop)
    assert len(details) == 7
    details = dbaccess.get_details_connections(ipstart, ipend, False, timestamp_range=time_crop)
    assert len(details) == 50

    details = dbaccess.get_details_connections(ipstart, ipend, True, timestamp_range=time_tiny)
    assert len(details) == 3
    details = dbaccess.get_details_connections(ipstart, ipend, False, timestamp_range=time_tiny)
    assert len(details) == 27

    details = dbaccess.get_details_connections(ipstart2, ipend2, True, timestamp_range=time_crop)
    assert len(details) == 1
    details = dbaccess.get_details_connections(ipstart2, ipend2, False, timestamp_range=time_crop)
    assert len(details) == 0


def test_get_details_ports():
    time_all = (1, 2 ** 31 - 1)
    time_crop = (make_timestamp('2016-06-21 17:10'), make_timestamp('2016-06-21 18:05'))
    time_tiny = (make_timestamp('2016-06-21 17:45'), make_timestamp('2016-06-21 17:50'))
    ipstart1, ipend1, _ = common.determine_range(21, 66, 40, 231)
    ipstart2, ipend2, _ = common.determine_range(79, 35, 103, 221)

    ipstart, ipend, _ = common.determine_range(21)
    details = dbaccess.get_details_ports(ipstart, ipend)
    assert len(details) == 50
    ipstart, ipend, _ = common.determine_range(21, 66)
    details = dbaccess.get_details_ports(ipstart, ipend)
    assert len(details) == 50
    ipstart, ipend, _ = common.determine_range(21, 66, 10)
    details = dbaccess.get_details_ports(ipstart, ipend)
    assert len(details) == 50
    ipstart, ipend, _ = common.determine_range(21, 66, 10, 70)
    details = dbaccess.get_details_ports(ipstart, ipend)
    assert len(details) == 29
    details = dbaccess.get_details_ports(ipstart1, ipend1)
    assert len(details) == 1

    details = dbaccess.get_details_ports(ipstart1, ipend1, port=445)
    assert len(details) == 1
    details = dbaccess.get_details_ports(ipstart1, ipend1, port=80)
    assert len(details) == 0
    details = dbaccess.get_details_ports(ipstart1, ipend1, port=1)
    assert len(details) == 0

    details = dbaccess.get_details_ports(ipstart1, ipend1, timestamp_range=time_all)
    assert len(details) == 1
    details = dbaccess.get_details_ports(ipstart1, ipend1, timestamp_range=time_crop)
    assert len(details) == 1
    details = dbaccess.get_details_ports(ipstart1, ipend1, timestamp_range=time_tiny)
    assert len(details) == 1
    details = dbaccess.get_details_ports(ipstart2, ipend2, timestamp_range=time_crop)
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
        common.db.update("portLUT", where="port={0}".format(test_port), active=1)
        common.db.delete("portAliasLUT", where="port={0}".format(test_port))

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
        common.db.delete("portLUT", where="port={0}".format(test_port))
        common.db.delete("portAliasLUT", where="port={0}".format(test_port))
