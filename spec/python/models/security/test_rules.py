import cPickle
import pytest
import web
from spec.python import db_connection
from sam.models.security import rules

db = db_connection.db
sub_id = db_connection.default_sub
ds_full = db_connection.dsid_default


def test_decode_row():
    r = rules.Rules(db, sub_id)
    decoded = r.decode_row({'a': 1, 'active': 1, 'params': cPickle.dumps({'1': True, '2': 3.141, '3': 'else'})})
    expected = {
        'a': 1,
        'active': True,
        'params': {'1': True, '2': 3.141, '3': 'else'}
    }
    assert decoded == expected


def test_add_rule():
    path = "custom: test_rule.yml"
    name = "test_rule_612"
    description = "lorem ipsum dolor sit amet"
    params = {'1': True, '2': 3.141, '3': 'else'}
    r = rules.Rules(db, sub_id)

    # no rules present:
    r.clear()
    assert r.count() == 0

    # add some bad rules first:
    with pytest.raises(ValueError):
        r.add_rule(path, '', description, params)
    with pytest.raises(ValueError):
        r.add_rule(path, 42, description, params)
    with pytest.raises(ValueError):
        r.add_rule(path, name, False, params)

    # add a real rule
    r.add_rule(path, name, description, params)
    assert r.count() == 1
    all_rules = r.get_all_rules()
    new_rule = all_rules[0]
    assert new_rule.get_name() == name
    assert new_rule.get_desc() == description
    assert new_rule.path == path


def test_row_to_rule():
    row = {
        'id': 321,
        'active': True,
        'name': 'test_rule_941',
        'description': 'wrembule',
        'rule_path': 'custom: test_rule.yml',
        'params': {
            'actions': {'alert_label': 'myopic elephant'},
            'exposed': {'port': '777'}
        },
    }
    r = rules.Rules(db, sub_id)
    new_rule = r.row_to_rule(row)
    assert new_rule.get_name() == 'test_rule_941'
    assert new_rule.get_desc() == "wrembule"
    actions = new_rule.get_action_params()
    assert actions['alert_label'] == 'myopic elephant'
    exposed = new_rule.get_exposed_params()
    assert exposed['port']['value'] == '777'


def test_get_all_rules():
    r = rules.Rules(db, sub_id)
    r.clear()
    path = "custom: test_rule.yml"
    r.add_rule(path, 'n1', 'd1', {})
    r.add_rule(path, 'n2', 'd2', {})
    r.add_rule(path, 'n3', 'd3', {})
    all_rules = r.get_all_rules()
    rule_names = [rule.get_name() for rule in all_rules]
    assert rule_names == ['n1', 'n2', 'n3']


def test_get_ruleset():
    r = rules.Rules(db, sub_id)
    r.clear()
    path = "custom: test_rule.yml"
    r.add_rule(path, 'n1', 'd1', {})
    r.add_rule(path, 'n2', 'd2', {})
    r.add_rule(path, 'n3', 'd3', {})
    r.add_rule(path, 'n4', 'd4', {})

    all_rules = r.get_all_rules()
    ids = [rule.id for rule in all_rules]
    for id in ids[1::2]:
        r.edit_rule(id, {'active': True})

    ruleset = r.get_ruleset()
    assert len(ruleset) == 2
    rule_names = [rule.get_name() for rule in ruleset]
    assert rule_names == ['n2', 'n4']


def test_get_rule():
    r = rules.Rules(db, sub_id)
    r.clear()
    path = "custom: test_rule.yml"
    r.add_rule(path, 'n1', 'd1', {})
    r.add_rule(path, 'n2', 'd2', {})

    all_rules = r.get_all_rules()
    ids = [rule.id for rule in all_rules]
    one_rule = r.get_rule(ids[0])
    assert one_rule.get_name() == 'n1'
    one_rule = r.get_rule(ids[1])
    assert one_rule.get_name() == 'n2'


def test_delete_rule():
    r = rules.Rules(db, sub_id)
    r.clear()
    path = "custom: test_rule.yml"
    r.add_rule(path, 'n1', 'd1', {})
    r.add_rule(path, 'n2', 'd2', {})
    r.add_rule(path, 'n3', 'd3', {})
    r.add_rule(path, 'n4', 'd4', {})

    all_rules = r.get_all_rules()
    ids = [rule.id for rule in all_rules]
    for id in ids:
        r.edit_rule(id, {'active': True})
    for id in ids[::2]:
        r.delete_rule(id)

    all_rules = r.get_all_rules()
    ruleset = r.get_ruleset()
    assert len(ruleset) == 2
    rule_names = [rule.get_name() for rule in all_rules]
    assert rule_names == ['n2', 'n4']


def test_edit_rule():
    r = rules.Rules(db, sub_id)
    r.clear()
    path = "custom: test_rule.yml"
    r.add_rule(path, 'n1', 'd1', {})
    rule = r.get_all_rules()[0]
    assert rule.active == False
    assert rule.get_action_params()['alert_label'] == 'Special Label'
    assert rule.get_exposed_params()['color']['value'] == 'blue'

    #perform edits:
    r.edit_rule(rule.id, {
        'active': True,
        'actions': {'alert_label': 'secret-sauce'},
        'exposed': {'color': 'green'}
    })

    updated = r.get_rule(rule.id)
    assert updated.active == True
    assert updated.get_exposed_params()['color']['value'] == 'green'
    assert updated.get_action_params()['alert_label'] == 'secret-sauce'
