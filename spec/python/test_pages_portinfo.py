import server
import web
import urllib
import json
import common

app = web.application(server.urls, globals())


def test_get_empty():
    req = app.request('/portinfo', 'GET')

    assert req.status == "200 OK"
    assert req.headers['Content-Type'] == "application/json"
    data = json.loads(req.data)
    assert data.keys() == ['result']
    assert data['result'].startswith("ERROR")


def test_get_single():
    test_port = 80
    input_data = {"port": test_port}
    GET_data = urllib.urlencode(input_data)
    req = app.request('/portinfo?{0}'.format(GET_data), 'GET')

    assert req.status == "200 OK"
    assert req.headers['Content-Type'] == "application/json"
    data = json.loads(req.data)
    assert data.keys() == [str(test_port)]
    assert sorted(data[str(test_port)].keys()) == ['active', 'alias_description', 'alias_name', 'description', 'name',
                                                   'port']


def test_get_missing():
    test_port = 4
    input_data = {"port": test_port}
    GET_data = urllib.urlencode(input_data)
    req = app.request('/portinfo?{0}'.format(GET_data), 'GET')

    assert req.status == "200 OK"
    assert req.headers['Content-Type'] == "application/json"
    data = json.loads(req.data)
    assert data == {}


def test_get_many():
    test_ports = "3,4,5,6"
    input_data = {"port": test_ports}
    GET_data = urllib.urlencode(input_data)
    req = app.request('/portinfo?{0}'.format(GET_data), 'GET')

    assert req.status == "200 OK"
    assert req.headers['Content-Type'] == "application/json"
    data = json.loads(req.data)
    assert sorted(data.keys()) == ['3', '5']
    assert sorted(data['3'].keys()) == ['active', 'alias_description', 'alias_name', 'description', 'name', 'port']
    assert sorted(data['5'].keys()) == ['active', 'alias_description', 'alias_name', 'description', 'name', 'port']


def test_post_new_port():
    test_port = 4
    POST_data = {'port': test_port}
    try:
        req = app.request('/portinfo', 'POST', data=POST_data)
        assert req.status == "200 OK"
        assert req.headers['Content-Type'] == "application/json"
        data = json.loads(req.data)
        result = data.get('result', "ERROR")
        assert result.lower().startswith("success")
        # check for existance of result
        req = app.request('/portinfo?port={0}'.format(test_port), 'GET')
        assert req.status == "200 OK"
        assert req.headers['Content-Type'] == "application/json"
        data = json.loads(req.data)
        assert data[str(test_port)] == {u'name': u'', u'active': 0, u'alias_name': u'', u'port': test_port,
                                        u'alias_description': u'', u'description': u''}
    finally:
        # remove test_port from database
        common.db.delete("portLUT", where="port={0}".format(test_port))
        common.db.delete("portAliasLUT", where="port={0}".format(test_port))


def test_post_disable_port():
    test_port = 3
    try:
        # verify old situation
        req = app.request('/portinfo?port={0}'.format(test_port), 'GET')
        assert '"active": 1' in req.data

        # set active to false
        POST_data = {'port': test_port, 'active': '0'}
        req = app.request('/portinfo', 'POST', data=POST_data)
        assert req.status == "200 OK"
        assert req.headers['Content-Type'] == "application/json"
        data = json.loads(req.data)
        result = data.get('result', "ERROR")
        assert result.lower().startswith("success")

        # check that active is now false
        req = app.request('/portinfo?port={0}'.format(test_port), 'GET')
        assert '"active": 0' in req.data
    finally:
        # restore port to active.
        common.db.update("portLUT", where="port={0}".format(test_port), active=1)
        common.db.delete("portAliasLUT", where="port={0}".format(test_port))


def test_post_update_port():
    test_port = 2
    try:
        # set new alias for test_port
        long_name = "too long of a name"
        POST_data = {'port': test_port, 'alias_name': long_name, 'alias_description': 'desc1'}
        req = app.request('/portinfo', 'POST', data=POST_data)
        assert req.status == "200 OK"
        assert req.headers['Content-Type'] == "application/json"
        data = json.loads(req.data)
        result = data.get('result', "ERROR")
        assert result.lower().startswith("success")

        # check that the alias is set
        req = app.request('/portinfo?port={0}'.format(test_port), 'GET')
        data = json.loads(req.data)
        assert data[str(test_port)]['active'] == 1
        assert data[str(test_port)]['alias_name'] == long_name[:10]
        assert data[str(test_port)]['alias_description'] == 'desc1'

        long_desc = "This is a long description that will easily exceed the maximum limit of two hundred fifty six " \
                    "characters in length because as long as I keep adding new text to the description there is no " \
                    "way for it not to exceed two hundred fifty six characters in length."

        # set new alias for test_port
        POST_data = {'port': test_port, 'alias_name': 'name2', 'alias_description': long_desc}
        req = app.request('/portinfo', 'POST', data=POST_data)
        assert req.status == "200 OK"
        assert req.headers['Content-Type'] == "application/json"
        data = json.loads(req.data)
        result = data.get('result', "ERROR")
        assert result.lower().startswith("success")

        # check that the alias is set
        req = app.request('/portinfo?port={0}'.format(test_port), 'GET')
        data = json.loads(req.data)
        assert data[str(test_port)]['active'] == 1
        assert data[str(test_port)]['alias_name'] == 'name2'
        assert data[str(test_port)]['alias_description'] == long_desc[:255]
    finally:
        # restore port to active.
        common.db.update("portLUT", where="port={0}".format(test_port), active=1)
        common.db.delete("portAliasLUT", where="port={0}".format(test_port))
