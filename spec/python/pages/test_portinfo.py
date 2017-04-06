from spec.python import db_connection
import pages.portinfo
import pytest
import errors

db = db_connection.db
sub_id = db_connection.default_sub
ds_full = db_connection.dsid_default


def test_decode_get():
    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        p = pages.portinfo.Portinfo()
        data = {'port': '80,,443,8080'}
        request = p.decode_get_request(data)
        expected = {'ports': [80, 443, 8080]}
        assert request == expected

        data = {'port': '127'}
        request = p.decode_get_request(data)
        expected = {'ports': [127]}
        assert request == expected

        data = {'port': ''}
        with pytest.raises(errors.RequiredKey):
            p.decode_get_request(data)

        data = {'port': '14, 16, 18'}
        request = p.decode_get_request(data)
        expected = {'ports': [14, 16, 18]}
        assert request == expected


def test_perform_get():
    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        p = pages.portinfo.Portinfo()
        request = {'ports': [80, 443, 8080]}
        response = p.perform_get_command(request)
        assert len(response) == 3
        assert set([x['port'] for x in response]) == {80, 443, 8080}

        request = {'ports': [160]}
        response = p.perform_get_command(request)
        assert len(response) == 1
        port = response[0]
        assert port['port'] == 160
        assert port['name'] == 'sgmp-traps'

        request = {'ports': [4]}
        response = p.perform_get_command(request)
        assert len(response) == 0


def test_encode_get():
    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        p = pages.portinfo.Portinfo()
        response = [{'port': 40, 'name': 'test1'}, {'port': 48, 'name': 'test2'}, {'port': 56, 'name': 'test3'}]
        encoded = p.encode_get_response(response)
        expected = {
            '40': {'port': 40, 'name': 'test1'},
            '48': {'port': 48, 'name': 'test2'},
            '56': {'port': 56, 'name': 'test3'}
        }
        assert encoded == expected


def test_decode_post():
    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        p = pages.portinfo.Portinfo()
        data = {'port': '80', 'alias_name': 'test_alias', 'alias_description': 'test_description', 'active': '1'}
        request = p.decode_post_request(data)
        expected = {'port': 80, 'alias_name': 'test_alias', 'alias_description': 'test_description', 'active': '1'}
        assert request == expected

        data = {'port': '80', 'xalias_name': 'test_alias', 'xalias_description': 'test_description', 'xactive': '1'}
        request = p.decode_post_request(data)
        expected = {'port': 80}
        assert request == expected

        data = {'xport': '80', 'alias_name': 'test_alias', 'alias_description': 'test_description', 'active': '1'}
        with pytest.raises(errors.RequiredKey):
            p.decode_post_request(data)

        data = {'port': 'frog', 'alias_name': 'test_alias', 'alias_description': 'test_description', 'active': '1'}
        with pytest.raises(errors.MalformedRequest):
            p.decode_post_request(data)


def test_perform_post():
    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        p = pages.portinfo.Portinfo()
        p.portModel = db_connection.mocker()

        request = {'port': 80, 'alias_name': 'test_alias', 'alias_description': 'test_description', 'active': '1'}
        p.perform_post_command(request)
        calls = p.portModel.calls
        assert calls[0] == ('set',
                            (80, {'alias_name': 'test_alias', 'alias_description': 'test_description', 'active': '1'}),
                            {})

        request = {'port': 160}
        p.portModel.clear()
        p.perform_post_command(request)
        calls = p.portModel.calls
        assert calls[0] == ('set', (160, {}), {})
