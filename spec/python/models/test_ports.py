# importing db_connection has the side effect of setting the test database.
import db_connection
import models.ports

db = db_connection.get_test_db_connection()
sub_id = db_connection.default_sub


def test_get_port_info_present():
    pm = models.ports.Ports(sub_id)

    port_info = pm.get(80)

    assert len(port_info) == 1
    info = port_info[0]
    assert info.name == 'http'
    assert info.description == 'World Wide Web HTTP'
    assert info.port == 80


def test_get_port_info_absent():
    pm = models.ports.Ports(sub_id)

    port_info = pm.get(4)
    assert port_info == []


def test_get_port_info_many():
    pm = models.ports.Ports(sub_id)
    port_info = pm.get([3, 4, 5, 6])
    assert len(port_info) == 2
    info3 = port_info[0]
    info5 = port_info[1]
    assert info3.port == 3
    assert info3.name == 'compressne'
    assert info5.port == 5
    assert info5.name == 'rje'


def test_set_port_info():
    pm = models.ports.Ports(sub_id)

    test_port = 1
    try:
        # set data for port 1
        pm.set(test_port, {
            'port': test_port,
            'alias_name': "override",
            'alias_description': "lorem ipsum",
            'active': '0'
        })
        pinfo = pm.get(test_port)
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
        pm.unset(test_port)

    test_port = 4
    try:
        # set data for port 4
        pm.set(test_port, {
            'port': test_port,
            'alias_name': "this_name_is_too_long",
            'alias_description': "phony port details",
            'active': '0'
        })
        pinfo = pm.get(test_port)
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
        pm.unset(test_port)

