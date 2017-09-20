# coding=utf-8
from spec.python import db_connection
import operator
import pytest
from datetime import datetime
from sam.pages.rules import Rules, RulesApply, RulesEdit, RulesNew
from sam.models.security import rules, rule_template, ruling_process
from sam import errors

db = db_connection.db
sub_id = db_connection.default_sub
ds_full = db_connection.dsid_default


def reset_dummy_rules():
    r = rules.Rules(db, sub_id)
    r.clear()
    r.add_rule("compromised.yml", 'comp hosts', 'desc1', {})
    r.add_rule("dos.yml", 'DDoS', 'desc2', {})
    r.add_rule("portscan.yml", 'port scans', 'desc3', {})
    r.add_rule("suspicious.yml", 'suspicious traffic', 'desc4', {})
    all_rules = r.get_all_rules()
    ids = [rule.id for rule in all_rules]
    # enable all but portscan.yml
    r.edit_rule(ids[0], {'active': True})
    r.edit_rule(ids[1], {'active': True})
    r.edit_rule(ids[3], {'active': True})


def test_rules_decode():
    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        r = Rules()
        assert r.decode_get_request({}) is None
        assert r.decode_get_request({'method': 'nothing'}) is None
        assert r.decode_get_request('Garbage') is None


def test_rules_perform():
    reset_dummy_rules()
    r_model = rules.Rules(db, sub_id)
    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        r = Rules()
        response = r.perform_get_command(None)
        assert response == r_model.get_all_rules()


def test_rules_encode():
    reset_dummy_rules()
    r_model = rules.Rules(db, sub_id)
    all_rules = r_model.get_all_rules()
    ids = [rule.id for rule in all_rules]
    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        r = Rules()
        encoded = r.encode_get_response(all_rules)
        expected = {'all': [
            {'id': ids[0], 'name': 'comp hosts', 'desc': 'desc1', 'template': 'Compromised Traffic', 'type': 'immediate', 'active': True},
            {'id': ids[1], 'name': 'DDoS', 'desc': 'desc2', 'template': 'High Traffic', 'type': 'periodic', 'active': True},
            {'id': ids[2], 'name': 'port scans', 'desc': 'desc3', 'template': 'Port Scanning', 'type': 'periodic', 'active': False},
            {'id': ids[3], 'name': 'suspicious traffic', 'desc': 'desc4', 'template': 'IP -> IP/Port', 'type': 'immediate', 'active': True},
        ]}
        assert encoded == expected


# ================= RulesNew =================


def test_rulesnew_get_decode():
    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        r = RulesNew()
        assert r.decode_get_request({}) is None
        assert r.decode_get_request({'method': 'nothing'}) is None
        assert r.decode_get_request('Garbage') is None


def test_rulesnew_get_perform():
    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        r = RulesNew()
        response = r.perform_get_command(None)

        expected = [
            ('compromised.yml', 'Compromised Traffic'),
            ('custom: test_rule.yml', 'Test Yaml'),
            ('dos.yml', 'High Traffic'),
            ('netscan.yml', 'Network Scanning'),
            ('portscan.yml', 'Port Scanning'),
            ('suspicious.yml', 'IP -> IP/Port'),
        ]
        response.sort(key=operator.itemgetter(0))
        assert response == expected


def test_rulesnew_get_encode():
    all_templates = rule_template.get_all()

    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        r = RulesNew()
        response = r.encode_get_response(all_templates)
        expected = {
            'portscan.yml',
            'netscan.yml',
            'suspicious.yml',
            'compromised.yml',
            'dos.yml',
            'custom: test_rule.yml'}
        assert 'templates' in response
        assert set(response['templates']) == expected


def test_rulesnew_post_decode():
    """
    valid requests include:
        name: blah, desc: blah, template: blah
    :return:
    """
    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        r = RulesNew()

        # bad data input
        with pytest.raises(errors.RequiredKey):
            data = {'name': 'abc', 'desc': 'def'}
            r.decode_post_request(data)
        with pytest.raises(errors.RequiredKey):
            data = {'desc': 'def', 'template': 'ghi'}
            r.decode_post_request(data)
        with pytest.raises(errors.RequiredKey):
            data = {'name': 'abc', 'template': 'ghi'}
            r.decode_post_request(data)
        with pytest.raises(errors.RequiredKey):
            data = {'name': ' ', 'desc': 'def', 'template': 'ghi'}
            r.decode_post_request(data)
        with pytest.raises(errors.RequiredKey):
            data = {'name': 'abc', 'desc': ' ', 'template': 'ghi'}
            r.decode_post_request(data)
        with pytest.raises(errors.RequiredKey):
            data = {'name': 'abc', 'desc': 'def', 'template': ' '}
            r.decode_post_request(data)

        # good input data
        data = {'name': 'abc', 'desc': 'def', 'template': 'ghi'}
        request = r.decode_post_request(data)
        expected = {
            'name': 'abc',
            'desc': 'def',
            'template': 'ghi'
        }
        assert request == expected


def test_rulesnew_post_perform():
    r_model = rules.Rules(db, sub_id)
    r_model.clear()
    assert r_model.count() == 0

    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        r = RulesNew()
        request = {'name': 'abc', 'desc': 'def', 'template': 'ghi'}
        r.perform_post_command(request)
        assert r_model.count() == 1
        new_rule = r_model.get_all_rules()[0]
        assert new_rule.get_name() == 'abc'
        assert new_rule.get_desc() == 'def'


def test_rulesnew_post_encode():
    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        r = RulesNew()
        assert r.encode_post_response("success") == {'result': 'success'}
        assert r.encode_post_response("failure") == {'result': 'failure'}


# ================= RulesEdit =================


def test_rulesedit_get_decode():
    reset_dummy_rules()
    r_model = rules.Rules(db, sub_id)
    all_rules = r_model.get_all_rules()
    ids = [rule.id for rule in all_rules]
    # valid requests require a rule id ('id') to be specified

    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        r = RulesEdit()

        # bad data input
        with pytest.raises(errors.RequiredKey):
            data = {}
            r.decode_get_request(data)
        with pytest.raises(errors.MalformedRequest):
            data = {'id': 'not a number'}
            r.decode_get_request(data)

        # good input data

        data = {'id': ids[0]}
        request = r.decode_get_request(data)
        expected = {
            'id': ids[0]
        }
        assert request == expected
    

def test_rulesedit_get_perform():
    reset_dummy_rules()
    r_model = rules.Rules(db, sub_id)
    all_rules = r_model.get_all_rules()
    test_rule = all_rules[0]
    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        r = RulesEdit()
        request = {'id': test_rule.id}
        response = r.perform_get_command(request)
        assert response == test_rule

        with pytest.raises(errors.MalformedRequest):
            data = {'id': -200}
            r.perform_get_command(data)


def test_rulesedit_get_encode():
    reset_dummy_rules()
    r_model = rules.Rules(db, sub_id)
    all_rules = r_model.get_all_rules()
    test_rule = all_rules[0]
    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        r = RulesEdit()
        encoded = r.encode_get_response(test_rule)
        assert set(encoded.keys()) == {'id', 'name', 'desc', 'type', 'active', 'exposed', 'actions'}
        assert encoded['name'] == 'comp hosts'
        assert encoded['desc'] == 'desc1'
        assert set(encoded['actions'].keys()) == {
            'alert_active', 'alert_severity', 'alert_label', 'email_active', 'email_address',
            'email_subject', 'sms_active', 'sms_number', 'sms_message'}
        assert set(encoded['exposed'].keys()) == set()


def test_rulesedit_decode_exposed():
    data = {
        'edits[active]': u'false',
        'edits[exposed][color]': u'blue',
        'edits[actions][alert_label]': u'label of alert',
        'edits[exposed][pattern]': u'src_port > 1024',
        'edits[actions][sms_message]': u'secret message',
        'edits[exposed][sendmail]': u'true',
    }
    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        r = RulesEdit()
        exposed = r.decode_exposed(data)
        expected = {
            'color': u'blue',
            'pattern': u'src_port > 1024',
            'sendmail': u'true'
        }
        assert exposed == expected


def test_rulesedit_decode_actions():
    data = {
        'edits[active]': u'false',
        'edits[exposed][color]': u'blue',
        'edits[actions][alert_label]': u'label of alert',
        'edits[exposed][pattern]': u'src_port > 1024',
        'edits[actions][sms_message]': u'secret message',
        'edits[exposed][sendmail]': u'true',
    }
    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        r = RulesEdit()
        exposed = r.decode_actions(data)
        expected = {
            'alert_label': u'label of alert',
            'sms_message': u'secret message',
        }
        assert exposed == expected


def test_rulesedit_post_decode():
    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        r = RulesEdit()

        data = {}
        with pytest.raises(errors.RequiredKey):
            r.decode_post_request(data)

        data = {'id': 'NAN'}
        with pytest.raises(errors.MalformedRequest):
            r.decode_post_request(data)

        data = {'id': '13', 'method': 'bad-method'}
        with pytest.raises(errors.MalformedRequest):
            r.decode_post_request(data)

        data = {'id': '13', 'method': 'delete'}
        request = r.decode_post_request(data)
        assert request == {
            'id': 13,
            'method': 'delete',
            'active': None,
            'name': None,
            'desc': None,
            'actions': None,
            'exposed': None
        }

        data = {'id': '13', 'method': 'edit'}
        request = r.decode_post_request(data)
        assert request == {
            'id': 13,
            'method': 'edit',
            'active': None,
            'name': None,
            'desc': None,
            'actions': None,
            'exposed': None
        }

        data = {
            'id': '13',
            'method': 'edit',
            'edits[name]': u'new name',
            'edits[desc]': u'new desc',
            'edits[active]': u'false',
            'edits[exposed][color]': u'blue',
            'edits[actions][alert_label]': u'label of alert',
            'edits[exposed][pattern]': u'src_port > 1024',
            'edits[actions][sms_message]': u'secret message',
            'edits[exposed][sendmail]': u'true',
        }
        request = r.decode_post_request(data)
        assert request == {
            'id': 13,
            'method': 'edit',
            'active': False,
            'name': u'new name',
            'desc': u'new desc',
            'actions': {
                'alert_label': u'label of alert',
                'sms_message': u'secret message'
            },
            'exposed': {
                'color': u'blue',
                'pattern': u'src_port > 1024',
                'sendmail': u'true',
            }
        }


def test_rulesedit_post_perform():
    rn = rules.Rules(db, sub_id)
    params = {
        'exposed': {
            'source_ip': '44.33.22.11',
            'dest_ip': '88.77.66.55',
            'port': '8088'
        }, 'actions': {
            'alert_active': True,
            'alert_severity': 'a',
            'alert_label': 'b',
            'email_active': True,
            'email_address': 'c',
            'email_subject': 'd',
            'sms_active': True,
            'sms_number': 'e',
            'sms_message': 'f',
        }
    }
    rn.clear()
    rn.add_rule("suspicious.yml", 'sus rule', 'sus desc', params)

    # confirm initial state
    test_rule = rn.get_all_rules()[0]
    id = test_rule.id
    test_rule = rn.get_rule(rule_id=id) # get_all_rules above only retrieves a subset of info
    assert test_rule.get_name() == 'sus rule'
    action_params = test_rule.get_action_params()
    assert action_params['alert_active'] == True
    assert action_params['alert_severity'] == 'a'
    assert action_params['alert_label'] == 'b'
    assert action_params['email_active'] == True
    assert action_params['email_address'] == 'c'
    assert action_params['email_subject'] == 'd'
    assert action_params['sms_active'] == True
    assert action_params['sms_number'] == 'e'
    assert action_params['sms_message'] == 'f'
    exposed_params = test_rule.get_exposed_params()
    assert exposed_params['source_ip']['value'] == '44.33.22.11'
    assert exposed_params['dest_ip']['value'] == '88.77.66.55'
    assert exposed_params['port']['value'] == '8088'

    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        r = RulesEdit()

        # edit everything
        request = {
            'id': id,
            'method': 'edit',
            'active': False,
            'name': u'new name',
            'desc': u'new desc',
            'actions': {
                'alert_active': False,
                'alert_severity': '1',
                'alert_label': '2',
                'email_active': False,
                'email_address': '3',
                'email_subject': '4',
                'sms_active': True,
                'sms_number': '5',
                'sms_message': '6',
            },
            'exposed': {
                'source_ip': '55.44.33.22',
                'dest_ip': '99.88.77.66',
                'port': '9099',
            }
        }
        r.perform_post_command(request)

        # check that rule has been updated
        test_rule = rn.get_rule(rule_id=id)
        assert test_rule.get_name() == 'new name'
        assert test_rule.get_desc() == 'new desc'
        assert test_rule.is_active() == False
        action_params = test_rule.get_action_params()
        assert action_params['alert_active'] == False
        assert action_params['alert_severity'] == '1'
        assert action_params['alert_label'] == '2'
        assert action_params['email_active'] == False
        assert action_params['email_address'] == '3'
        assert action_params['email_subject'] == '4'
        assert action_params['sms_active'] == True
        assert action_params['sms_number'] == '5'
        assert action_params['sms_message'] == '6'
        exposed_params = test_rule.get_exposed_params()
        assert exposed_params['source_ip']['value'] == '55.44.33.22'
        assert exposed_params['dest_ip']['value'] == '99.88.77.66'
        assert exposed_params['port']['value'] == '9099'

        # delete the rule
        request = {
            'id': id,
            'method': 'delete',
            'active': None,
            'name': None,
            'desc': None,
            'actions': None,
            'exposed': None
        }
        assert rn.count() == 1
        r.perform_post_command(request)
        assert rn.count() == 0


def test_rulesedit_post_encode():
    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        r = RulesEdit()
        assert r.encode_post_response("success") == {'result': 'success'}
        assert r.encode_post_response("failure") == {'result': 'failure'}


# ================= RulesApply =================


def test_rulesapply_get():
    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        r = RulesApply()
        page = r.GET()
        assert page is None


def test_rulesapply_post_decode():
    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        r = RulesApply()

        data = {}
        with pytest.raises(errors.RequiredKey):
            r.decode_post_request(data)

        data = {'ds': 'NAN'}
        with pytest.raises(errors.MalformedRequest):
            r.decode_post_request(data)

        data = {'ds': ds_full}
        request = r.decode_post_request(data)
        expected = {
            'ds': ds_full,
            'start': datetime.fromtimestamp(1),
            'end': datetime.fromtimestamp(2**31 - 1)
        }
        assert request == expected

        data = {'ds': ds_full, 'start': '11223344'}
        request = r.decode_post_request(data)
        expected = {
            'ds': ds_full,
            'start': datetime.fromtimestamp(11223344),
            'end': datetime.fromtimestamp(2**31 - 1)
        }
        assert request == expected

        data = {'ds': ds_full, 'end': '11223344'}
        request = r.decode_post_request(data)
        expected = {
            'ds': ds_full,
            'start': datetime.fromtimestamp(1),
            'end': datetime.fromtimestamp(11223344)
        }
        assert request == expected

        data = {'ds': ds_full, 'start': '11223344', 'end': '44332211'}
        request = r.decode_post_request(data)
        expected = {
            'ds': ds_full,
            'start': datetime.fromtimestamp(11223344),
            'end': datetime.fromtimestamp(44332211)
        }
        assert request == expected

        data = {'ds': ds_full, 'start': 'abc', 'end': 'def'}
        request = r.decode_post_request(data)
        expected = {
            'ds': ds_full,
            'start': datetime.fromtimestamp(1),
            'end': datetime.fromtimestamp(2**31 - 1)
        }
        assert request == expected


def test_rulesapply_post_perform():
    reset_dummy_rules()
    old_submit_job = ruling_process.submit_job
    try:
        ruling_process.submit_job = db_connection.Mocker()
        ruling_process.submit_job._retval = 32768
        with db_connection.env(mock_input=True, login_active=False, mock_session=True):
            r = RulesApply()
            request = {
                'ds': ds_full,
                'start': datetime.fromtimestamp(0),
                'end': datetime.fromtimestamp(2**31 - 1)
            }
            response, job_id = r.perform_post_command(request)
            assert response == 'success'
            calls = ruling_process.submit_job.calls
            assert calls[0][0] == 'self'
            args = calls[0][1]
            rj = args[0]
            assert isinstance(rj, ruling_process.RuleJob)
            # assert rj.id == job_id  # this can't be tested here because I'm overriding the function that
            # assigns the id with a generic mocker that won't
            assert rj.ds_id == ds_full
            assert rj.time_end == request['end']
            assert rj.time_start == request['start']
    finally:
        ruling_process.submit_job = old_submit_job


def test_rulesapply_post_encode():
    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        r = RulesApply()
        response = ('success', 14)
        encoded = r.encode_post_response(response)
        expected = {'result': 'success', 'job_id': 14}
        assert encoded == expected

        response = ('unknown', )
        encoded = r.encode_post_response(response)
        expected = {'result': 'unknown'}
        assert encoded == expected

        response = 'failure'
        encoded = r.encode_post_response(response)
        expected = {'result': 'failure'}
        assert encoded == expected
