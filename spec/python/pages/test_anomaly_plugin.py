from spec.python import db_connection
import pytest
from sam.pages.anomaly_plugin import ADPlugin
from spec.python.models.security import test_warnings
from sam.models.security import anomaly_plugin as model_ap
from sam import errors

db = db_connection.db
sub_id = db_connection.default_sub
ds_full = db_connection.dsid_default


def test_decode_get_request():
    # request can be:
    #   (opt) method: "status"(default) | "warnings" | "warning"
    #   if warnings:
    #      (opt) all: "true" | "false"(default)
    #   if warning:
    #      warning_id: r"\d+"
    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        ad = ADPlugin()
        data = {}
        expected = {'method': 'status'}
        request = ad.decode_get_request(data)
        assert request == expected

        data = {'method': 'status'}
        expected = {'method': 'status'}
        request = ad.decode_get_request(data)
        assert request == expected

        data = {'method': 'warning'}
        with pytest.raises(errors.RequiredKey):
            request = ad.decode_get_request(data)
        data = {'method': 'warning', 'warning_id': ''}
        with pytest.raises(errors.MalformedRequest):
            request = ad.decode_get_request(data)
        data = {'method': 'warning', 'warning_id': 'huh'}
        with pytest.raises(errors.MalformedRequest):
            request = ad.decode_get_request(data)
        
        data = {'method': 'warning', 'warning_id': '12'}
        expected = {'method': 'warning', 'warning_id': 12}
        request = ad.decode_get_request(data)
        assert request == expected

        data = {'method': 'warnings'}
        expected = {'method': 'warnings', 'show_all': False}
        request = ad.decode_get_request(data)
        assert request == expected

        data = {'method': 'warnings', 'all': 'false'}
        expected = {'method': 'warnings', 'show_all': False}
        request = ad.decode_get_request(data)
        assert request == expected

        data = {'method': 'warnings', 'all': 'other'}
        expected = {'method': 'warnings', 'show_all': False}
        request = ad.decode_get_request(data)
        assert request == expected

        data = {'method': 'warnings', 'all': 'true'}
        expected = {'method': 'warnings', 'show_all': True}
        request = ad.decode_get_request(data)
        assert request == expected

        data = {'method': 'warnings', 'all': 'TRUE'}
        expected = {'method': 'warnings', 'show_all': True}
        request = ad.decode_get_request(data)
        assert request == expected
        

def test_perform_get_command():
    # request can be one of:
    #   {'method': 'warning', 'warning_id': ###}
    #   {'method': 'warnings', 'show_all': True|False}
    #   {'method': 'status'}
    test_warnings.populate_db_warnings()

    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        ad = ADPlugin()
        ap = model_ap.ADPlugin(db, sub_id)
        ws = ap.get_warnings(show_all=True)

        # test `warning`
        i = ws[7]['id']
        request = {'method': 'warning', 'warning_id': i}
        response = ad.perform_get_command(request)
        assert 'warning' in response
        assert response['warning']['id'] == i
        assert response['warning']['warning_id'] == 7

        request = {'method': 'warning', 'warning_id': -200}
        response = ad.perform_get_command(request)
        assert 'warning' in response
        assert response['warning'] is None
        
        # test `warnings`
        request = {'method': 'warnings', 'show_all': False}
        response = ad.perform_get_command(request)
        assert 'warnings' in response
        ws = {w['warning_id'] for w in response['warnings']}
        assert ws == {1,5,8,10,14}

        request = {'method': 'warnings', 'show_all': True}
        response = ad.perform_get_command(request)
        assert 'warnings' in response
        ws = {w['warning_id'] for w in response['warnings']}
        assert ws == set(range(1, 15))

        # test `status`
        request = {'method': 'status'}
        response = ad.perform_get_command(request)
        assert 'active' in response
        assert 'status' in response
        assert 'stats' in response
        assert response['active'] is True
        assert response['status'] == 'unavailable'
        assert response['stats'] is None


def test_encode_get_response():
    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        ad = ADPlugin()
        # status responses aren't affected
        response = {'status': 'anything'}
        assert ad.encode_get_response(response) == response
        response = {'status': {'any': 'thing', 'else': '.'}}
        assert ad.encode_get_response(response) == response

        # warning responses are translated
        warnings = [
            {'status': u'uncategorized', 'host': 1684366951L, 'log_time': 1471532192L, 'reason': u'test1', 'warning_id': 14L, 'id': 28L},
            {'status': u'accepted',      'host': 1684366952L, 'log_time': 1471532192L, 'reason': u'test1', 'warning_id': 13L, 'id': 27L},
            {'status': u'rejected',      'host': 1684367209L, 'log_time': 1500669918L, 'reason': u'test1', 'warning_id': 12L, 'id': 26L},
            {'status': u'ignored',       'host': 1684367209L, 'log_time': 1503088818L, 'reason': u'test1', 'warning_id': 4L,  'id': 18L},
        ]
        response = {'warnings': warnings}
        encoded = ad.encode_get_response(response)
        expected = {'warnings': [
            {'status': u'uncategorized', 'host': "100.101.102.103", 'log_time': "2016-08-18 07:56:32", 'reason': u'test1', 'id': 28L},
            {'status': u'accepted',      'host': "100.101.102.104", 'log_time': "2016-08-18 07:56:32", 'reason': u'test1', 'id': 27L},
            {'status': u'rejected',      'host': "100.101.103.105", 'log_time': "2017-07-21 13:45:18", 'reason': u'test1', 'id': 26L},
            {'status': u'ignored',       'host': "100.101.103.105", 'log_time': "2017-08-18 13:40:18", 'reason': u'test1', 'id': 18L},
        ]}
        assert encoded == expected

        # warning responses are translated too
        warning = {
            'status': u'rejected',
            'host': 1684432746L,
            'details': {
                'key2': 'val2',
                'activities': [
                    {'title': 'title1', 'score': 3, 'id': 1L, 'warning_id': 2L, 'description': 'desc1'},
                    {'title': 'title2', 'score': 4, 'id': 2L, 'warning_id': 2L, 'description': 'desc2'}],
                'title2': 'Warning score: 4',
                'title1': 'Warning score: 3'},
            'log_time': 1503002718L,
            'reason': u'test1',
            'warning_id': 7L,
            'id': 21L}
        response = {'warning': warning}
        encoded = ad.encode_get_response(response)
        expected = {'warning': {
            'status': u'rejected',
            'host': '100.102.103.106',
            'details': {
                'key2': 'val2',
                'activities': [
                    {'title': 'title1', 'score': 3, 'id': 1L, 'warning_id': 2L, 'description': 'desc1'},
                    {'title': 'title2', 'score': 4, 'id': 2L, 'warning_id': 2L, 'description': 'desc2'}],
                'title2': 'Warning score: 4',
                'title1': 'Warning score: 3'},
            'log_time': "2017-08-17 13:45:18",
            'reason': u'test1',
            'id': 21L}}
        assert encoded == expected


def test_decode_post_request():
    # request can be:
    #   method: 'accept', 'reject', 'ignore', 'disable', 'enable', 'reset', 'reset_all'
    #   if accept | reject | ignore:
    #      warning_id: r"\d+"
    #   if reset:
    #      host: string
    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        ad = ADPlugin()

        data = {}
        with pytest.raises(errors.RequiredKey):
            ad.decode_post_request(data)
        data = {'method': 'garbage'}
        with pytest.raises(errors.MalformedRequest):
            ad.decode_post_request(data)
            
        data = {'method': 'accept'}
        with pytest.raises(errors.MalformedRequest):
            ad.decode_post_request(data)
        data = {'method': 'accept', 'warning_id': 'not-a-number'}
        with pytest.raises(errors.MalformedRequest):
            ad.decode_post_request(data)
        data = {'method': 'accept', 'warning_id': '13'}
        request = ad.decode_post_request(data)
        assert request == {'method': 'accept', 'warning_id': 13}
            
        data = {'method': 'reject'}
        with pytest.raises(errors.MalformedRequest):
            ad.decode_post_request(data)
        data = {'method': 'reject', 'warning_id': 'not-a-number'}
        with pytest.raises(errors.MalformedRequest):
            ad.decode_post_request(data)
        data = {'method': 'reject', 'warning_id': '14'}
        request = ad.decode_post_request(data)
        assert request == {'method': 'reject', 'warning_id': 14}
            
        data = {'method': 'ignore'}
        with pytest.raises(errors.MalformedRequest):
            ad.decode_post_request(data)
        data = {'method': 'ignore', 'warning_id': 'not-a-number'}
        with pytest.raises(errors.MalformedRequest):
            ad.decode_post_request(data)
        data = {'method': 'ignore', 'warning_id': '15'}
        request = ad.decode_post_request(data)
        assert request == {'method': 'ignore', 'warning_id': 15}

        data = {'method': 'enable'}
        request = ad.decode_post_request(data)
        assert request == data
        data = {'method': 'disable'}
        request = ad.decode_post_request(data)
        assert request == data
        data = {'method': 'reset_all'}
        request = ad.decode_post_request(data)
        assert request == data

        data = {'method': 'reset'}
        with pytest.raises(errors.MalformedRequest):
            ad.decode_post_request(data)
        data = {'method': 'reset', 'host': '1.2.3.4'}
        request = ad.decode_post_request(data)
        assert request == {'method': 'reset', 'host': '1.2.3.4'}


def test_perform_post_command():
    # request can be one of:
    #   {'method': 'enable' | 'disable' | 'reset_all'}
    #   {'method': accept|reject|ignore, 'warning_id': ###}
    #   {'method': reset, 'host': 'a.b.c.d'}
    test_warnings.populate_db_warnings()

    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        ad = ADPlugin()
        ap = model_ap.ADPlugin(db, sub_id)
        ws = ap.get_warnings(show_all=True)
        i = ws[7]['id']

        assert ad.perform_post_command({'method': 'disable'}) == 'success'
        assert ad.perform_post_command({'method': 'enable'}) == 'success'
        assert ad.perform_post_command({'method': 'accept', 'warning_id': i}) == 'success'
        assert ad.perform_post_command({'method': 'reject', 'warning_id': i}) == 'success'
        assert ad.perform_post_command({'method': 'ignore', 'warning_id': i}) == 'success'

        with pytest.raises(errors.MalformedRequest):
            ad.perform_post_command({'method': 'accept', 'warning_id': -200})
        with pytest.raises(errors.MalformedRequest):
            ad.perform_post_command({'method': 'reject', 'warning_id': -200})
        with pytest.raises(errors.MalformedRequest):
            ad.perform_post_command({'method': 'ignore', 'warning_id': -200})
        with pytest.raises(errors.MalformedRequest):
            ad.perform_post_command({'method': 'reset_all'})
        with pytest.raises(errors.MalformedRequest):
            ad.perform_post_command({'method': 'reset', 'host': '10.20.30.40'})
        with pytest.raises(errors.MalformedRequest):
            ad.perform_post_command({'method': 'bogus'})


def test_encode_post_response():
    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        ad = ADPlugin()
        assert ad.encode_post_response("success") == {'result': 'success'}
        assert ad.encode_post_response("failure") == {'result': 'failure'}
