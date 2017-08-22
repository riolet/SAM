# coding=utf-8
from spec.python import db_connection
import pytest
from sam.pages.rules import Rules, RulesApply, RulesEdit, RulesNew
from sam.models.security import rules, rule_template
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
    # disable portscan.yml rule
    r.edit_rule(ids[2], {'active': False})


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
            {'id': ids[1], 'name': 'DDoS', 'desc': 'desc2', 'template': 'Traffic Threshold', 'type': 'periodic', 'active': True},
            {'id': ids[2], 'name': 'port scans', 'desc': 'desc3', 'template': 'Port Scanning', 'type': 'periodic', 'active': False},
            {'id': ids[3], 'name': 'suspicious traffic', 'desc': 'desc4', 'template': 'TCPDUMP Rule', 'type': 'immediate', 'active': True},
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
    all_templates = rule_template.get_all()
    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        r = RulesNew()
        response = r.perform_get_command(None)
        assert response == all_templates


def test_rulesnew_get_encode():
    all_templates = rule_template.get_all()

    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        r = RulesNew()
        response = r.encode_get_response(all_templates)
        expected = {'templates': [
            'portscan.yml',
            'netscan.yml',
            'suspicious.yml',
            'compromised.yml',
            'dos.yml',
            'custom: test_rule.yml']}
        assert response == expected


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
    assert False


def test_rulesedit_decode_exposed():
    assert False


def test_rulesedit_decode_actions():
    assert False


def test_rulesedit_post_decode():
    assert False


def test_rulesedit_post_perform():
    assert False


def test_rulesedit_post_encode():
    assert False


# ================= RulesApply =================


def test_rulesapply_get_encode():
    assert False


def test_rulesapply_post_decode():
    assert False


def test_rulesapply_post_perform():
    assert False


def test_rulesapply_post_encode():
    assert False