import dbaccess
from datetime import datetime
import time
import common


def test_parse_sql():
    expected = ['DROP TABLE IF EXISTS blah',
                '\n \n \n CREATE TABLE IF NOT EXISTS blah\n'
                ' (port              INT UNSIGNED NOT NULL\n'
                ' ,CONSTRAINT PKportAliasLUT PRIMARY KEY (port)\n'
                ' )',
                '\n \n SELECT * FROM blah\n ']
    assert dbaccess.parse_sql_file("./spec/python/test_sql.sql") == expected


# def test_reset_port_names:
#     ???


def test_determine_range_0():
    assert dbaccess.determine_range() == (0x00000000, 0xffffffff, 0x1000000)


def test_determine_range_1():
    assert dbaccess.determine_range(12) == (0xc000000, 0xcffffff, 0x10000)


def test_determine_range_2():
    assert dbaccess.determine_range(12, 8) == (0xc080000, 0xc08ffff, 0x100)


def test_determine_range_3():
    assert dbaccess.determine_range(12, 8, 192) == (0xc08c000, 0xc08c0ff, 0x1)


def test_determine_range_4():
    assert dbaccess.determine_range(12, 8, 192, 127) == (0xc08c07f, 0xc08c07f, 0x1)


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
    assert sorted(rows[0].keys()) == ['dest8', 'links', 'source8', 'x1', 'x2', 'y1', 'y2']
    simple = [(str(row.source8), str(row.dest8), int(row.links)) for row in rows]
    assert simple == [('21', '79', 24937), ('53', '79', 9), ('79', '79', 172), ('110', '79', 4566), ('189', '79', 9688)]

    # connections into 79.146.0.0/16
    rows = dbaccess.get_links_in(79, 146)
    assert sorted(rows[0].keys()) == ['dest16', 'dest8', 'links', 'source16', 'source8', 'x1', 'x2', 'y1', 'y2']
    simple = [
        (".".join((str(row.source8), str(row.source16))),
         ".".join((str(row.dest8), str(row.dest16))),
         int(row.links)
         ) for row in rows]
    assert simple == [('21.256', '79.146', 2815), ('110.256', '79.146', 166), ('189.256', '79.146', 6)]

    # connections into 79.146.149.0/24
    rows = dbaccess.get_links_in(79, 146, 149)
    assert sorted(rows[0].keys()) == ['dest16', 'dest24', 'dest8', 'links', 'source16', 'source24', 'source8', 'x1', 'x2', 'y1', 'y2']
    simple = [
        (".".join((str(row.source8), str(row.source16), str(row.source24))),
         ".".join((str(row.dest8), str(row.dest16), str(row.dest24))),
         int(row.links)
         ) for row in rows]
    assert simple == [('21.256.256', '79.146.149', 393), ('189.256.256', '79.146.149', 6)]

    # connections into 79.146.149.40
    rows = dbaccess.get_links_in(79, 146, 149, 40)
    assert len(rows) == 20
    assert sorted(rows[0].keys()) == ['dest16', 'dest24', 'dest32', 'dest8', 'links', 'port', 'source16', 'source24', 'source32', 'source8', 'x1', 'x2', 'y1', 'y2']
    simple = [
        (int(row.source8),
         int(row.port),
         int(row.links)
         ) for row in rows]
    assert simple == [(21, 80, 8), (21, 280, 4), (21, 411, 4), (21, 427, 1), (21, 443, 4), (21, 1024, 4),
                      (21, 1311, 4), (21, 2069, 4), (21, 3202, 4), (21, 3257, 4), (21, 4095, 4), (21, 4096, 4),
                      (21, 5989, 3), (21, 8000, 4), (21, 8008, 4), (21, 8222, 4), (21, 8443, 4), (21, 9990, 4),
                      (21, 9991, 4), (189, 2434, 6)]


def test_get_links_out_plain():
    # connections into 21.0.0.0/8
    rows = dbaccess.get_links_out(21)
    assert sorted(rows[0].keys()) == ['dest8', 'links', 'source8', 'x1', 'x2', 'y1', 'y2']
    simple = [(str(row.source8), str(row.dest8), int(row.links)) for row in rows]
    assert simple == [('21', '21', 20324), ('21', '79', 24937), ('21', '189', 460)]

    # connections into 21.66.0.0/16
    rows = dbaccess.get_links_out(21, 66)
    assert sorted(rows[0].keys()) == ['dest16', 'dest8', 'links', 'source16', 'source8', 'x1', 'x2', 'y1', 'y2']
    simple = [
        (".".join((str(row.source8), str(row.source16))),
         ".".join((str(row.dest8), str(row.dest16))),
         int(row.links)
         ) for row in rows]
    assert simple == [('21.66', '21.66', 20324), ('21.66', '79.256', 24937), ('21.66', '189.256', 460)]

    # connections into 21.66.138.0/24
    rows = dbaccess.get_links_out(21, 66, 138)
    assert sorted(rows[0].keys()) == ['dest16', 'dest24', 'dest8', 'links', 'source16', 'source24', 'source8', 'x1', 'x2', 'y1', 'y2']
    simple = [
        (".".join((str(row.source8), str(row.source16), str(row.source24))),
         ".".join((str(row.dest8), str(row.dest16), str(row.dest24))),
         int(row.links)
         ) for row in rows]
    assert simple == [('21.66.138', '21.66.10', 2), ('21.66.138', '21.66.141', 1), ('21.66.138', '79.256.256', 11)]

    # connections into 21.66.138.188
    rows = dbaccess.get_links_out(21, 66, 138, 188)
    assert len(rows) == 3
    assert sorted(rows[0].keys()) == ['dest16', 'dest24', 'dest32', 'dest8', 'links', 'port', 'source16', 'source24', 'source32', 'source8', 'x1', 'x2', 'y1', 'y2']
    simple = [
        (".".join((str(row.source8), str(row.source16), str(row.source24), str(row.source32))),
         ".".join((str(row.dest8), str(row.dest16), str(row.dest24), str(row.dest32))),
         int(row.port),
         int(row.links)
         ) for row in rows]
    assert simple == [('21.66.138.188', '79.256.256.256', 22, 4),
                      ('21.66.138.188', '79.256.256.256', 5414, 3),
                      ('21.66.138.188', '79.256.256.256', 9519, 3)]


def test_get_links_out_filter():
    test_port = 12345

    rows = dbaccess.get_links_out(21, 66, 42, 22, filter=test_port)
    assert sorted(rows[0].keys()) == ['dest16', 'dest24', 'dest32', 'dest8', 'links', 'port', 'source16', 'source24', 'source32', 'source8', 'x1', 'x2', 'y1', 'y2']
    ports = set([int(i.port) for i in rows])
    assert ports == {test_port}
    assert len(rows) == 5

    rows = dbaccess.get_links_out(21, 66, filter=test_port)
    assert sorted(rows[0].keys()) == ['dest16', 'dest8', 'links', 'source16', 'source8', 'x1', 'x2', 'y1', 'y2']
    assert len(rows) == 2
    rows = dbaccess.get_links_out(21, 66)
    assert len(rows) == 3


def make_timestamp(ts):
    d = datetime.strptime(ts, "%Y-%m-%d %H:%M")
    ts = time.mktime(d.timetuple())
    return int(ts)


def test_get_links_out_timerange():
    time_all = (1, 2**31-1)
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


def test_get_details():
    details = dbaccess.get_details(21)
    assert details['unique_in'] == 9311
    assert details['unique_out'] == 468
    assert details['unique_ports'] == 94
    assert len(details['conn_in']) == 50
    assert len(details['conn_out']) == 50
    assert len(details['ports_in']) == 50

    details = dbaccess.get_details(21, 66)
    assert details['unique_in'] == 9311
    assert details['unique_out'] == 468
    assert details['unique_ports'] == 94
    assert len(details['conn_in']) == 50
    assert len(details['conn_out']) == 50
    assert len(details['ports_in']) == 50

    details = dbaccess.get_details(21, 66, 10)
    assert details['unique_in'] == 2503
    assert details['unique_out'] == 1
    assert details['unique_ports'] == 38
    assert len(details['conn_in']) == 50
    assert len(details['conn_out']) == 1
    assert len(details['ports_in']) == 38

    details = dbaccess.get_details(21, 66, 10, 70)
    assert details['unique_in'] == 16
    assert details['unique_out'] == 0
    assert details['unique_ports'] == 13
    assert len(details['conn_in']) == 31
    assert len(details['conn_out']) == 0
    assert len(details['ports_in']) == 13

    details = dbaccess.get_details(21, 66, 40, 231)
    assert details['unique_in'] == 7
    assert details['unique_out'] == 4
    assert details['unique_ports'] == 1
    assert len(details['conn_in']) == 7
    assert len(details['conn_out']) == 9
    assert len(details['ports_in']) == 1


def test_get_details_port():
    details = dbaccess.get_details(21,66,40,231, port=445)
    assert details['unique_in'] == 7
    assert details['unique_out'] == 0
    assert details['unique_ports'] == 1
    assert len(details['conn_in']) == 7
    assert len(details['conn_out']) == 0
    assert len(details['ports_in']) == 1

    details = dbaccess.get_details(21,66,40,231, port=80)
    assert details['unique_in'] == 0
    assert details['unique_out'] == 2
    assert details['unique_ports'] == 0
    assert len(details['conn_in']) == 0
    assert len(details['conn_out']) == 2
    assert len(details['ports_in']) == 0

    details = dbaccess.get_details(21,66,40,231, port=1)
    assert details['unique_in'] == 0
    assert details['unique_out'] == 0
    assert details['unique_ports'] == 0
    assert len(details['conn_in']) == 0
    assert len(details['conn_out']) == 0
    assert len(details['ports_in']) == 0


def test_get_details_timerange():
    time_all = (1, 2**31-1)
    time_crop = (make_timestamp('2016-06-21 17:10'), make_timestamp('2016-06-21 18:05'))
    time_tiny = (make_timestamp('2016-06-21 17:45'), make_timestamp('2016-06-21 17:50'))

    details = dbaccess.get_details(21,66,40,231, timerange=time_all)
    assert details['unique_in'] == 7
    assert details['unique_out'] == 4
    assert details['unique_ports'] == 1
    assert len(details['conn_in']) == 7
    assert len(details['conn_out']) == 9
    assert len(details['ports_in']) == 1

    details = dbaccess.get_details(21,66,40,231, timerange=time_crop)
    assert details['unique_in'] == 7
    assert details['unique_out'] == 4
    assert details['unique_ports'] == 1
    assert len(details['conn_in']) == 7
    assert len(details['conn_out']) == 9
    assert len(details['ports_in']) == 1

    details = dbaccess.get_details(21,66,40,231, timerange=time_tiny)
    assert details['unique_in'] == 1
    assert details['unique_out'] == 3
    assert details['unique_ports'] == 1
    assert len(details['conn_in']) == 1
    assert len(details['conn_out']) == 4
    assert len(details['ports_in']) == 1



def test_get_node_info():
    assert dbaccess.get_node_info(21) == {}


def test_set_node_info():
    # get old info
    # set some new random
    # assert info was recorded.
    # reset old info
    assert dbaccess.get_node_info(21) == {}


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
