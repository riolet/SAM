from spec.python import db_connection
import pages.nodes

db = db_connection.db
sub_id = db_connection.default_sub
ds_full = db_connection.dsid_default


def test_decode_get():
    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        p = pages.nodes.Nodes()
        data = {'address': '10.20.30,150.20,59'}
        request = p.decode_get_request(data)
        expected = {'addresses': ['10.20.30', '150.20', '59']}
        assert request == expected

        data = {'address': '50.60.70.80'}
        request = p.decode_get_request(data)
        expected = {'addresses': ['50.60.70.80']}
        assert request == expected

        data = {}
        request = p.decode_get_request(data)
        expected = {'addresses': []}
        assert request == expected

        data = {'horseradish': 'pickles'}
        request = p.decode_get_request(data)
        expected = {'addresses': []}
        assert request == expected


def test_perform_get():
    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        p = pages.nodes.Nodes()
        request = {'addresses': []}
        response = p.perform_get_command(request)
        assert response.keys() == ['_']
        assert len(response['_']) == 6

        request = {'addresses': ['10']}
        response = p.perform_get_command(request)
        assert response.keys() == ['10']
        assert len(response['10']) == 2

        request = {'addresses': ['50.60.70.80', '150.60.70', '110.20']}
        response = p.perform_get_command(request)
        assert set(response.keys()) == {'50.60.70.80', '150.60.70', '110.20'}
        assert len(response['50.60.70.80']) == 0
        assert len(response['150.60.70']) == 2
        assert len(response['110.20']) == 2


def test_decode_post():
    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        p = pages.nodes.Nodes()
        data = {'node': '10.20.30.40', 'alias': 'test_alias', 'tags': 'tag1,tag2,,', 'env': 'dev_2', 'extra': 'peanuts'}
        request = p.decode_post_request(data)
        expected = {'node': '10.20.30.40', 'alias': 'test_alias', 'tags': 'tag1,tag2,,', 'env': 'dev_2'}
        assert request == expected

        data = {'node': '10.20', 'alias': 'test_alias'}
        request = p.decode_post_request(data)
        expected = {'node': '10.20', 'alias': 'test_alias'}
        assert request == expected

        data = {'node': '10.20', 'tags': 'tag1,tag2,,'}
        request = p.decode_post_request(data)
        expected = {'node': '10.20', 'tags': 'tag1,tag2,,'}
        assert request == expected

        data = {'node': '10.20', 'env': 'smiles'}
        request = p.decode_post_request(data)
        expected = {'node': '10.20', 'env': 'smiles'}
        assert request == expected

        data = {'node': '10.20', 'env': None, 'tags': None, 'alias': None, 'extra': 'peanuts'}
        request = p.decode_post_request(data)
        expected = {'node': '10.20'}
        assert request == expected


def test_perform_post():
    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        p = pages.nodes.Nodes()
        p.nodesModel = db_connection.mocker()

        request = {'node': '10.20.30.40', 'alias': 'test_alias', 'tags': 'tag1,tag2,,', 'env': 'dev_2'}
        p.perform_post_command(request)
        calls = p.nodesModel.calls
        assert ('set_alias', ('10.20.30.40', 'test_alias'), {}) in calls
        assert ('set_env', ('10.20.30.40', 'dev_2'), {}) in calls
        assert ('set_tags', ('10.20.30.40', ['tag1', 'tag2']), {}) in calls

        p.nodesModel.clear()
        request = {'node': '10.20.30.40'}
        p.perform_post_command(request)
        calls = p.nodesModel.calls
        assert len(calls) == 0
