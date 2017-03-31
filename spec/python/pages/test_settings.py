from spec.python import db_connection
import pages.settings
import pytest
import errors
import models.links
import models.upload

db = db_connection.db
sub_id = db_connection.default_sub
ds_full = db_connection.dsid_default


def test_nice_name():
    assert pages.settings.nice_name('superHero') == 'Super Hero'
    assert pages.settings.nice_name('BluRay') == 'Blu Ray'
    assert pages.settings.nice_name('something_Else') == 'Something Else'
    assert pages.settings.nice_name('oneTwoThreeFour') == 'One Two Three Four'


def test_perform_get():
    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        p = pages.settings.Settings()
        request = {}
        response = p.perform_get_command(request)
        expected = {'datasources': 
                        {1: {'subscription': 1, 'ar_active': 0, 'ar_interval': 300, 'id': 1, 'name': u'default'}, 
                         2: {'subscription': 1, 'ar_active': 0, 'ar_interval': 300, 'id': 2, 'name': u'short'}, 
                         3: {'subscription': 1, 'ar_active': 0, 'ar_interval': 300, 'id': 3, 'name': u'live'}}, 
                    'settings': {'color_udp': 13391189, 'color_error': 10053222, 'color_label_bg': 16777215, 
                                 'color_bg': 11206621, 'datasource': 1, 'color_node': 5592524, 
                                 'color_label': 0, 'color_tcp': 5592524, 'subscription': 1}}
        assert response == expected


def test_encode_get():
    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        p = pages.settings.Settings()
        response = {'datasources':
                        {1: {'subscription': 1, 'ar_active': 0, 'ar_interval': 300, 'id': 1, 'name': u'default'},
                         2: {'subscription': 1, 'ar_active': 0, 'ar_interval': 300, 'id': 2, 'name': u'short'},
                         3: {'subscription': 1, 'ar_active': 0, 'ar_interval': 300, 'id': 3, 'name': u'live'}},
                    'settings': {'color_udp': 13391189, 'color_error': 10053222, 'color_label_bg': 16777215,
                                 'color_bg': 11206621, 'datasource': 1, 'color_node': 5592524,
                                 'color_label': 0, 'color_tcp': 5592524, 'subscription': 1}}
        outbound = p.encode_get_response(response)
        assert set(outbound.keys()) == {'color_udp', 'color_error', 'color_label_bg', 'datasources', 'datasource', 'color_node', 'color_bg', 'color_label', 'color_tcp', 'subscription'}
        assert outbound['datasources'] == response['datasources']
        assert outbound['datasource'] in response['datasources']


def test_get_importers():
    importers = pages.settings.Settings.get_available_importers()
    for importer in importers:
        assert len(importer) == 2
        assert isinstance(importer[0], basestring)
        assert isinstance(importer[1], basestring)


def test_decode_datasource():
    decode = pages.settings.Settings.decode_datasource
    assert decode('ds15') == 15
    assert decode('1') == 1
    assert decode('ds_1678') == 1678
    assert decode('ds') == None
    assert decode('s5_ds16') == 5


def test_post_ds_name():
    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        p = pages.settings.Settings()
        data = {'command': 'ds_name', 'ds': 'ds_1', 'name': 'test_name'}
        request = p.decode_post_request(data)
        expected = {
            'command': 'ds_name',
            'ds': 1,
            'name': 'test_name'
        }
        assert request == expected
        with pytest.raises(errors.MalformedRequest):
            data = {'command': 'ds_name', 'name': 'test_name'}
            request = p.decode_post_request(data)
        with pytest.raises(errors.MalformedRequest):
            data = {'command': 'ds_name', 'ds': 'ds_1'}
            request = p.decode_post_request(data)

        p.dsModel = db_connection.mocker()
        p.perform_post_command(expected)
        calls = p.dsModel.calls
        assert calls[0] == ('set', (1,), {'name':'test_name'})


def test_post_ds_live():
    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        p = pages.settings.Settings()
        data = {'command': 'ds_live', 'ds': 'ds_1', 'is_active': 'true'}
        request = p.decode_post_request(data)
        expected = {
            'command': 'ds_live',
            'ds': 1,
            'is_active': True
        }
        assert request == expected
        with pytest.raises(errors.MalformedRequest):
            data = {'command': 'ds_live', 'is_active': 'true'}
            request = p.decode_post_request(data)
        with pytest.raises(errors.MalformedRequest):
            data = {'command': 'ds_live', 'ds': 'ds_1'}
            request = p.decode_post_request(data)

        p.dsModel = db_connection.mocker()
        p.perform_post_command(expected)
        calls = p.dsModel.calls
        assert calls[0] == ('set', (1,), {'ar_active':1})


def test_post_ds_interval():
    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        p = pages.settings.Settings()
        data = {'command': 'ds_interval', 'ds': 'ds_1', 'interval': '300'}
        request = p.decode_post_request(data)
        expected = {
            'command': 'ds_interval',
            'ds': 1,
            'interval': 300
        }
        assert request == expected
        with pytest.raises(errors.MalformedRequest):
            data = {'command': 'ds_interval', 'interval': '300'}
            request = p.decode_post_request(data)
        with pytest.raises(errors.MalformedRequest):
            data = {'command': 'ds_interval', 'ds': 'ds_1'}
            request = p.decode_post_request(data)

        p.dsModel = db_connection.mocker()
        p.perform_post_command(expected)
        calls = p.dsModel.calls
        assert calls[0] == ('set', (1,), {'ar_interval':300})


def test_post_ds_new():
    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        p = pages.settings.Settings()
        data = {'command': 'ds_new', 'name': 'test datasource'}
        request = p.decode_post_request(data)
        expected = {
            'command': 'ds_new',
            'name': 'test datasource'
        }
        assert request == expected
        with pytest.raises(errors.MalformedRequest):
            data = {'command': 'ds_new'}
            request = p.decode_post_request(data)

        p.dsModel = db_connection.mocker()
        p.perform_post_command(expected)
        calls = p.dsModel.calls
        assert calls[0] == ('create_datasource', ('test datasource',), {})


def test_post_ds_rm():
    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        p = pages.settings.Settings()
        data = {'command': 'ds_rm', 'ds': 'ds12'}
        request = p.decode_post_request(data)
        expected = {
            'command': 'ds_rm',
            'ds': 12,
        }
        assert request == expected
        with pytest.raises(errors.MalformedRequest):
            data = {'command': 'ds_rm'}
            request = p.decode_post_request(data)

        p.dsModel = db_connection.mocker()
        p.perform_post_command(expected)
        calls = p.dsModel.calls
        assert calls[0] == ('remove_datasource', (12,), {})


def test_post_ds_select():
    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        p = pages.settings.Settings()
        data = {'command': 'ds_select', 'ds': 'ds12'}
        request = p.decode_post_request(data)
        expected = {
            'command': 'ds_select',
            'ds': 12,
        }
        assert request == expected
        with pytest.raises(errors.MalformedRequest):
            data = {'command': 'ds_select'}
            request = p.decode_post_request(data)

        p.settingsModel = db_connection.mocker()
        p.perform_post_command(expected)
        print(p.settingsModel.kvs)
        print(type(p.settingsModel.kvs))
        assert p.settingsModel.kvs == {'datasource': 12}


def test_post_rm_hosts():
    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        p = pages.settings.Settings()
        data = {'command': 'rm_hosts'}
        request = p.decode_post_request(data)
        expected = {
            'command': 'rm_hosts',
        }
        assert request == expected

        p.nodesModel = db_connection.mocker()
        p.perform_post_command(expected)
        calls = p.nodesModel.calls
        assert calls[0] == ('delete_custom_hostnames', (), {})


def test_post_rm_tags():
    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        p = pages.settings.Settings()
        data = {'command': 'rm_tags'}
        request = p.decode_post_request(data)
        expected = {
            'command': 'rm_tags',
        }
        assert request == expected

        p.nodesModel = db_connection.mocker()
        p.perform_post_command(expected)
        calls = p.nodesModel.calls
        assert calls[0] == ('delete_custom_tags', (), {})


def test_post_rm_envs():
    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        p = pages.settings.Settings()
        data = {'command': 'rm_envs'}
        request = p.decode_post_request(data)
        expected = {
            'command': 'rm_envs',
        }
        assert request == expected

        p.nodesModel = db_connection.mocker()
        p.perform_post_command(expected)
        calls = p.nodesModel.calls
        assert calls[0] == ('delete_custom_envs', (), {})


def test_post_rm_conns():
    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        p = pages.settings.Settings()
        data = {'command': 'rm_conns', 'ds': 'ds12'}
        request = p.decode_post_request(data)
        expected = {
            'command': 'rm_conns',
            'ds': 12,
        }
        assert request == expected
        with pytest.raises(errors.MalformedRequest):
            data = {'command': 'rm_conns'}
            request = p.decode_post_request(data)

        old = models.links.Links
        try:
            models.links.Links = db_connection.mocker
            p.perform_post_command(expected)
            calls = p.linksModel.calls
            assert p.linksModel.constructor == ((sub_id, 12), {})
            assert calls[0] == ('delete_connections', (), {})
        finally:
            models.links.Links = old


def test_post_upload():
    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        p = pages.settings.Settings()
        data = {'command': 'upload', 'ds': 'ds12', 'format': 'paloalto', 'file': 'b64,YWJjMTIz'}
        request = p.decode_post_request(data)
        expected = {
            'command': 'upload',
            'ds': 12,
            'format': 'paloalto',
            'file': 'b64,YWJjMTIz'
        }
        assert request == expected
        with pytest.raises(errors.MalformedRequest):
            data = {'command': 'upload', 'format': 'paloalto', 'file': 'b64,YWJjMTIz'}
            request = p.decode_post_request(data)
        with pytest.raises(errors.MalformedRequest):
            data = {'command': 'upload', 'ds': 'ds12', 'file': 'b64,YWJjMTIz'}
            request = p.decode_post_request(data)
        with pytest.raises(errors.MalformedRequest):
            data = {'command': 'upload', 'ds': 'ds12', 'format': 'paloalto'}
            request = p.decode_post_request(data)

        old = models.upload.Uploader
        try:
            models.upload.Uploader = db_connection.mocker
            p.perform_post_command(expected)
            calls = p.uploadModel.calls
            assert p.uploadModel.constructor == ((sub_id, 12, 'paloalto'), {})
            assert calls[0] == ('import_log', ('abc123',), {})
        finally:
            models.upload.Uploader = old


def test_post_add_live_key():
    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        p = pages.settings.Settings()
        data = {'command': 'add_live_key', 'ds': 'ds12'}
        request = p.decode_post_request(data)
        expected = {
            'command': 'add_live_key',
            'ds': 12,
        }
        assert request == expected
        with pytest.raises(errors.MalformedRequest):
            data = {'command': 'add_live_key'}
            request = p.decode_post_request(data)

        p.livekeyModel = db_connection.mocker()
        p.perform_post_command(expected)
        calls = p.livekeyModel.calls
        assert calls[0] == ('create', (12,), {})


def test_post_del_live_key():
    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        p = pages.settings.Settings()
        data = {'command': 'del_live_key', 'key': 'abc123'}
        request = p.decode_post_request(data)
        expected = {
            'command': 'del_live_key',
            'key': 'abc123',
        }
        assert request == expected
        with pytest.raises(errors.MalformedRequest):
            data = {'command': 'del_live_key'}
            request = p.decode_post_request(data)

        p.livekeyModel = db_connection.mocker()
        p.perform_post_command(expected)
        calls = p.livekeyModel.calls
        assert calls[0] == ('delete', ('abc123',), {})
