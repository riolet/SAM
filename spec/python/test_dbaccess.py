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


def test_tags():
    ip1 = "21"
    ip2 = "21.66"
    ip3 = "21.66.116"
    ip4 = "21.66.116.37"
    tt1 = "test_tag_one"
    tt2 = "test_tag_two"
    tt3 = "test_tag_three"
    tt4 = "test_tag_four"
    # get the old tags
    temp1 = dbaccess.get_tags(ip1)
    assert sorted(temp1.keys()) == ['p_tags', 'tags']
    temp4 = dbaccess.get_tags(ip4)
    assert sorted(temp4.keys()) == ['p_tags', 'tags']
    old_1 = temp1['tags']
    old_2 = dbaccess.get_tags(ip2)['tags']
    old_3 = dbaccess.get_tags(ip3)['tags']
    old_4 = temp4['tags']

    try:
        # set some test tags
        dbaccess.set_tags(ip1, old_1 + [tt1])
        dbaccess.set_tags(ip2, old_2 + [tt2])
        dbaccess.set_tags(ip3, old_3 + [tt3])
        dbaccess.set_tags(ip4, old_4 + [tt4])
        # read new tags
        new_1 = dbaccess.get_tags(ip1)
        new_2 = dbaccess.get_tags(ip2)
        new_3 = dbaccess.get_tags(ip3)
        new_4 = dbaccess.get_tags(ip4)
        # test new tags
        assert tt1     in new_1['tags'] and tt1 not in new_1['p_tags']
        assert tt2 not in new_1['tags'] and tt2 not in new_1['p_tags']
        assert tt3 not in new_1['tags'] and tt3 not in new_1['p_tags']
        assert tt4 not in new_1['tags'] and tt4 not in new_1['p_tags']

        assert tt1 not in new_2['tags'] and tt1     in new_2['p_tags']
        assert tt2     in new_2['tags'] and tt2 not in new_2['p_tags']
        assert tt3 not in new_2['tags'] and tt3 not in new_2['p_tags']
        assert tt4 not in new_2['tags'] and tt4 not in new_2['p_tags']

        assert tt1 not in new_3['tags'] and tt1     in new_3['p_tags']
        assert tt2 not in new_3['tags'] and tt2     in new_3['p_tags']
        assert tt3     in new_3['tags'] and tt3 not in new_3['p_tags']
        assert tt4 not in new_3['tags'] and tt4 not in new_3['p_tags']

        assert tt1 not in new_4['tags'] and tt1     in new_4['p_tags']
        assert tt2 not in new_4['tags'] and tt2     in new_4['p_tags']
        assert tt3 not in new_4['tags'] and tt3     in new_4['p_tags']
        assert tt4     in new_4['tags'] and tt4 not in new_4['p_tags']

        # check the full tag list
        tags = dbaccess.get_tag_list()
        assert tt1 in tags
        assert tt2 in tags
        assert tt3 in tags
        assert tt4 in tags

    finally:
        # remove test tags
        dbaccess.set_tags(ip1, old_1)
        dbaccess.set_tags(ip2, old_2)
        dbaccess.set_tags(ip3, old_3)
        dbaccess.set_tags(ip4, old_4)


def test_env():
    ip1 = "21"
    ip2 = "21.66"
    ip3 = "21.66.116"
    ip4 = "21.66.116.37"
    te1 = "test_env_one"
    te2 = "test_env_two"
    te3 = "test_env_three"
    te4 = "test_env_four"
    # get the old tags
    temp1 = dbaccess.get_env(ip1)
    assert sorted(temp1.keys()) == ['env', 'p_env']
    temp4 = dbaccess.get_env(ip4)
    assert sorted(temp4.keys()) == ['env', 'p_env']
    old_1 = temp1['env']
    old_2 = dbaccess.get_env(ip2)['env']
    old_3 = dbaccess.get_env(ip3)['env']
    old_4 = temp4['env']

    try:
        # set some test tags
        dbaccess.set_env(ip1, te1)
        dbaccess.set_env(ip2, te2)
        dbaccess.set_env(ip3, te3)
        dbaccess.set_env(ip4, te4)
        # read new tags
        new_1 = dbaccess.get_env(ip1)
        new_2 = dbaccess.get_env(ip2)
        new_3 = dbaccess.get_env(ip3)
        new_4 = dbaccess.get_env(ip4)
        # test new tags
        assert te1 == new_1['env'] and te1 != new_1['p_env']
        assert te2 != new_1['env'] and te2 != new_1['p_env']
        assert te3 != new_1['env'] and te3 != new_1['p_env']
        assert te4 != new_1['env'] and te4 != new_1['p_env']

        assert te1 != new_2['env'] and te1 == new_2['p_env']
        assert te2 == new_2['env'] and te2 != new_2['p_env']
        assert te3 != new_2['env'] and te3 != new_2['p_env']
        assert te4 != new_2['env'] and te4 != new_2['p_env']

        assert te1 != new_3['env'] and te1 != new_3['p_env']
        assert te2 != new_3['env'] and te2 == new_3['p_env']
        assert te3 == new_3['env'] and te3 != new_3['p_env']
        assert te4 != new_3['env'] and te4 != new_3['p_env']

        assert te1 != new_4['env'] and te1 != new_4['p_env']
        assert te2 != new_4['env'] and te2 != new_4['p_env']
        assert te3 != new_4['env'] and te3 == new_4['p_env']
        assert te4 == new_4['env'] and te4 != new_4['p_env']

        # check the full env list
        envs = dbaccess.get_env_list()
        assert te1 in envs
        assert te2 in envs
        assert te3 in envs
        assert te4 in envs
    finally:
        # remove test tags
        dbaccess.set_env(ip1, old_1)
        dbaccess.set_env(ip2, old_2)
        dbaccess.set_env(ip3, old_3)
        dbaccess.set_env(ip4, old_4)


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
