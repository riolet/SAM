import os
import re
import yaml
from spec.python import db_connection
from sam.models.security import rule, rule_template
from sam import constants

db = db_connection.db
sub_id = db_connection.default_sub
ds_full = db_connection.dsid_default


def get_dummy_rule():
    dummy_yml = """---
name: Test Yaml
type: immediate
include:
  bad_hosts: ./test_hosts.txt
expose:
  source_ip:
    format: text
    label: temp label
    default: "1.2.3.4"
    regex: "^([0-9]|[01]?[0-9][0-9]|2[0-4][0-9]|25[0-5])(\\\\.([0-9]|[01]?[0-9][0-9]|2[0-4][0-9]|25[0-5])){3}$"
  dest_ip:
    format: text
    label: temp label 2
    default: "5.6.7.8"
    regex: "^([0-9]|[01]?[0-9][0-9]|2[0-4][0-9]|25[0-5])(\\\\.([0-9]|[01]?[0-9][0-9]|2[0-4][0-9]|25[0-5])){3}$"
  port:
    format: text
    label: temp label 3
    default: "(80,443)"
    regex: "("  # intentially malformed regex
  bidirectional:
    format: checkbox
    label: Check both ways
    default: false
  color:
    format: dropdown
    label: Favorite Color
    default: blue
    options:
      - red
      - blue
      - green
actions:
  alert_severity: 8
  alert_label: Special Label
  email_address: abc@zyx.com
  email_subject: "[SAM] Special Email Subject"
  sms_number: 1 123 456 7890
  sms_message: "[SAM] Special SMS Message"
subject: src
when: src host $source_ip and dst host $dest_ip and dst port $port
"""
    data = yaml.load(dummy_yml)
    base_path = os.path.dirname(rule_template.__file__)
    rule_path = os.path.join(base_path, os.path.pardir, constants.templates_folder)
    template = rule_template.RuleTemplate(rule_path, data)
    r = rule.Rule(123, True, "My Test Rule", "Description of My Test Rule", rule_path)
    r.definition = template
    r.active = True
    r.exposed_params = r.get_initial_exposed_params()
    r.action_params = r.get_initial_action_params()
    return r


def test_init():
    r = rule.Rule(123, True, "my rule", "description of my rule", 'compromised.yml')
    assert r.id == 123
    assert r.active == True
    assert r.name == "my rule"
    assert r.desc == "description of my rule"
    assert r.path == "compromised.yml"
    assert isinstance(r.definition, rule_template.RuleTemplate)
    assert r.exposed_params == {}
    assert r.action_params == r.get_initial_action_params()


def test_nice_path():
    r = rule.Rule(123, True, "my rule", "description of my rule", 'compromised.yml')
    assert r.nice_path('compromised') == 'compromised'
    assert r.nice_path('compromised.yml') == 'compromised'
    assert r.nice_path('compromised.yml.yml') == 'compromised.yml'
    assert r.nice_path('plugin: slatch.yml') == 'slatch'
    assert r.nice_path('custom: yodello') == 'yodello'


def test_get_type():
    r = rule.Rule(123, True, "my rule", "description of my rule", 'compromised.yml')
    assert r.get_type() == "immediate"
    r = rule.Rule(123, True, "my rule", "description of my rule", 'dos.yml')
    assert r.get_type() == "periodic"
    r = rule.Rule(123, True, "my rule", "description of my rule", 'plugin: missing_plugin.yml')
    assert r.get_type() == "Error."


def test_get_def_name():
    r = rule.Rule(123, True, "my rule", "description of my rule", 'compromised.yml')
    assert r.get_def_name() == "Compromised Traffic"
    r = rule.Rule(123, True, "my rule", "description of my rule", 'dos.yml')
    assert r.get_def_name() == "Traffic Threshold"
    r = rule.Rule(123, True, "my rule", "description of my rule", 'plugin: missing_plugin.yml')
    assert r.get_def_name() == "Error."


def test_is_active():
    r = rule.Rule(123, True, "my rule", "description of my rule", 'compromised.yml')
    assert r.is_active() is True
    r = rule.Rule(123, False, "my rule", "description of my rule", 'compromised.yml')
    assert r.is_active() is False
    r = rule.Rule(123, True, "my rule", "description of my rule", 'plugin: missing_plugin.yml')
    assert r.is_active() is False


def test_get_name():
    r = rule.Rule(123, True, "my rule1", "description of my rule", 'compromised.yml')
    assert r.get_name() == "my rule1"
    r = rule.Rule(123, False, "my rule2", "description of my rule", 'dos.yml')
    assert r.get_name() is "my rule2"
    r = rule.Rule(123, True, "my rule3", "description of my rule", 'plugin: missing_plugin.yml')
    assert r.get_name() is "my rule3"


def test_get_desc():
    r = rule.Rule(123, True, "my rule1", "description of my rule1", 'compromised.yml')
    assert r.get_desc() == "description of my rule1"
    r = rule.Rule(123, False, "my rule2", "description of my rule2", 'dos.yml')
    assert r.get_desc() is "description of my rule2"
    r = rule.Rule(123, True, "my rule3", "description of my rule3", 'plugin: missing_plugin.yml')
    assert r.get_desc() is "description of my rule3"


def test_get_initial_exposed_params():
    r = rule.Rule(123, True, "my rule1", "description of my rule1", 'compromised.yml')
    assert r.get_initial_exposed_params() == {}

    r = get_dummy_rule()
    params = r.get_initial_exposed_params()
    assert set(params.keys()) == {'source_ip', 'dest_ip', 'port', 'bidirectional', 'color'}
    rc = re.compile("^\\d+$")
    # cannot assert equality on freshly compiled object.
    regex_compiled = params['source_ip'].pop('regex_compiled')
    assert type(rc) == type(regex_compiled)
    regex_compiled = params['dest_ip'].pop('regex_compiled')
    assert type(rc) == type(regex_compiled)
    assert params == {
        'source_ip': {
            'label': 'temp label',
            'format': 'text',
            'value': '1.2.3.4',
            'regex': "^([0-9]|[01]?[0-9][0-9]|2[0-4][0-9]|25[0-5])(\\.([0-9]|[01]?[0-9][0-9]|2[0-4][0-9]|25[0-5])){3}$"
        },
        'dest_ip': {
            'label': 'temp label 2',
            'format': 'text',
            'value': '5.6.7.8',
            'regex': "^([0-9]|[01]?[0-9][0-9]|2[0-4][0-9]|25[0-5])(\\.([0-9]|[01]?[0-9][0-9]|2[0-4][0-9]|25[0-5])){3}$"
        },
        'port': {
            'label': 'temp label 3',
            'format': 'text',
            'value': '(80,443)',
        },
        'bidirectional': {
            'label': 'Check both ways',
            'format': 'checkbox',
            'value': 'False',
        },
        'color': {
            'label': 'Favorite Color',
            'format': 'dropdown',
            'value': 'blue',
            'options': ['red', 'blue', 'green']
        },
    }

    r = rule.Rule(123, True, "my rule3", "description of my rule3", 'plugin: missing_plugin.yml')
    assert r.get_initial_exposed_params() == {}


def test_get_initial_action_params():
    r = rule.Rule(123, True, "my rule1", "description of my rule1", 'dos.yml')
    actions = r.get_initial_action_params()
    assert set(actions.keys()) == {'alert_active','alert_severity','alert_label','email_active',
        'email_address','email_subject','sms_active','sms_number','sms_message'}
    assert actions['alert_active'] == constants.security['alert_active']
    assert actions['alert_severity'] == constants.security['alert_severity']
    assert actions['alert_label'] == constants.security['alert_label']
    assert actions['email_active'] == constants.security['email_active']
    assert actions['email_address'] == constants.security['email_address']
    assert actions['email_subject'] == constants.security['email_subject']
    assert actions['sms_active'] == constants.security['sms_active']
    assert actions['sms_number'] == constants.security['sms_number']
    assert actions['sms_message'] == constants.security['sms_message']

    r = get_dummy_rule()
    actions = r.get_initial_action_params()
    assert set(actions.keys()) == {'alert_active','alert_severity','alert_label','email_active',
        'email_address','email_subject','sms_active','sms_number','sms_message'}
    assert actions['alert_active'] == constants.security['alert_active']
    assert actions['alert_severity'] == '8'
    assert actions['alert_label'] == 'Special Label'
    assert actions['email_active'] == constants.security['email_active']
    assert actions['email_address'] == 'abc@zyx.com'
    assert actions['email_subject'] == '[SAM] Special Email Subject'
    assert actions['sms_active'] == constants.security['sms_active']
    assert actions['sms_number'] == '1 123 456 7890'
    assert actions['sms_message'] == '[SAM] Special SMS Message'


def test_get_set_action_params():
    # verify initial conditions
    r = get_dummy_rule()
    actions = r.get_action_params()
    expected = {
        'alert_active': constants.security['alert_active'],
        'alert_severity': '8',
        'alert_label': 'Special Label',
        'email_active': constants.security['email_active'],
        'email_address': 'abc@zyx.com',
        'email_subject': '[SAM] Special Email Subject',
        'sms_active': constants.security['sms_active'],
        'sms_number': '1 123 456 7890',
        'sms_message': '[SAM] Special SMS Message',
    }
    import pprint
    pprint.pprint(actions)
    assert actions == expected

    # edit a few params
    r.set_action_params({'alert_severity': '1', 'email_address': 'example@example.com'})
    r.set_action_params({'sms_message': 'bogus'})
    r.set_action_params({})

    actions = r.get_action_params()
    expected = {
        'alert_active': constants.security['alert_active'],
        'alert_severity': '1',
        'alert_label': 'Special Label',
        'email_active': constants.security['email_active'],
        'email_address': 'example@example.com',
        'email_subject': '[SAM] Special Email Subject',
        'sms_active': constants.security['sms_active'],
        'sms_number': '1 123 456 7890',
        'sms_message': 'bogus',
    }
    assert actions == expected


def test_get_set_exposed_params():
    # verify initial conditions
    r = get_dummy_rule()
    rc = re.compile("a")

    params = r.get_exposed_params()
    regex_compiled = params['source_ip'].pop('regex_compiled')
    assert type(rc) == type(regex_compiled)
    regex_compiled = params['dest_ip'].pop('regex_compiled')
    assert type(rc) == type(regex_compiled)
    expected = {
        'source_ip': {
            'label': 'temp label',
            'format': 'text',
            'value': '1.2.3.4',
            'regex': "^([0-9]|[01]?[0-9][0-9]|2[0-4][0-9]|25[0-5])(\\.([0-9]|[01]?[0-9][0-9]|2[0-4][0-9]|25[0-5])){3}$"
        },
        'dest_ip': {
            'label': 'temp label 2',
            'format': 'text',
            'value': '5.6.7.8',
            'regex': "^([0-9]|[01]?[0-9][0-9]|2[0-4][0-9]|25[0-5])(\\.([0-9]|[01]?[0-9][0-9]|2[0-4][0-9]|25[0-5])){3}$"
        },
        'port': {
            'label': 'temp label 3',
            'format': 'text',
            'value': '(80,443)',
        },
        'bidirectional': {
            'label': 'Check both ways',
            'format': 'checkbox',
            'value': 'False',
        },
        'color': {
            'label': 'Favorite Color',
            'format': 'dropdown',
            'value': 'blue',
            'options': ['red', 'blue', 'green']
        },
    }
    assert params == expected

    # make some a valid edits:
    r = get_dummy_rule()
    r.set_exposed_params({'source_ip': '44.33.22.11', 'color': 'red', 'bidirectional': 'true', 'port': '123'})
    params = r.get_exposed_params()
    regex_compiled = params['source_ip'].pop('regex_compiled')
    assert type(rc) == type(regex_compiled)
    regex_compiled = params['dest_ip'].pop('regex_compiled')
    assert type(rc) == type(regex_compiled)
    expected = {
        'source_ip': {
            'label': 'temp label',
            'format': 'text',
            'value': '44.33.22.11',
            'regex': "^([0-9]|[01]?[0-9][0-9]|2[0-4][0-9]|25[0-5])(\\.([0-9]|[01]?[0-9][0-9]|2[0-4][0-9]|25[0-5])){3}$"
        },
        'dest_ip': {
            'label': 'temp label 2',
            'format': 'text',
            'value': '5.6.7.8',
            'regex': "^([0-9]|[01]?[0-9][0-9]|2[0-4][0-9]|25[0-5])(\\.([0-9]|[01]?[0-9][0-9]|2[0-4][0-9]|25[0-5])){3}$"
        },
        'port': {
            'label': 'temp label 3',
            'format': 'text',
            'value': '123',
        },
        'bidirectional': {
            'label': 'Check both ways',
            'format': 'checkbox',
            'value': 'true',
        },
        'color': {
            'label': 'Favorite Color',
            'format': 'dropdown',
            'value': 'red',
            'options': ['red', 'blue', 'green']
        },
    }
    assert params == expected

    # make some invalid edits
    r = get_dummy_rule()
    r.set_exposed_params({'source_ip': '44.33.22.11', 'color': 'red', 'bidirectional': 'true', 'port': '123'})
    r.set_exposed_params({'source_ip': '12.34.56', 'dest_ip': '@coffee_machine', 'color': 'jaune', 'bidirectional': 'cantilever'})
    params = r.get_exposed_params()
    regex_compiled = params['source_ip'].pop('regex_compiled')
    assert type(rc) == type(regex_compiled)
    regex_compiled = params['dest_ip'].pop('regex_compiled')
    assert type(rc) == type(regex_compiled)
    # expected is unchanged
    assert params == expected


def test_get_actions():
    r = get_dummy_rule()
    r.set_action_params({'alert_active': 'true'})
    r.set_action_params({'email_active': 'true'})
    r.set_action_params({'sms_active': 'true'})
    actions = r.get_actions()
    expected = [
        {'type': 'alert', 'severity': '8', 'label': 'Special Label'},
        {'type': 'email', 'address': 'abc@zyx.com', 'subject': '[SAM] Special Email Subject'},
        {'type': 'sms', 'number': '1 123 456 7890', 'message': '[SAM] Special SMS Message'}]
    assert actions == expected

    r.set_action_params({'alert_active': 'true'})
    r.set_action_params({'email_active': 'false'})
    r.set_action_params({'sms_active': 'false'})
    actions = r.get_actions()
    expected = [{'type': 'alert', 'severity': '8', 'label': 'Special Label'}]
    assert actions == expected

    r.set_action_params({'alert_active': 'false'})
    r.set_action_params({'email_active': 'true'})
    r.set_action_params({'sms_active': 'false'})
    actions = r.get_actions()
    expected = [{'type': 'email', 'address': 'abc@zyx.com', 'subject': '[SAM] Special Email Subject'}]
    assert actions == expected

    r.set_action_params({'alert_active': 'false'})
    r.set_action_params({'email_active': 'false'})
    r.set_action_params({'sms_active': 'true'})
    actions = r.get_actions()
    expected = [{'type': 'sms', 'number': '1 123 456 7890', 'message': '[SAM] Special SMS Message'}]
    assert actions == expected


def test_get_param_values():
    r = get_dummy_rule()
    params = r.get_param_values()
    expected = {
        'alert_active': constants.security['alert_active'],
        'alert_severity': '8',
        'alert_label': 'Special Label',
        'email_active': constants.security['email_active'],
        'email_address': 'abc@zyx.com',
        'email_subject': '[SAM] Special Email Subject',
        'sms_active': constants.security['sms_active'],
        'sms_number': '1 123 456 7890',
        'sms_message': '[SAM] Special SMS Message',
        'source_ip': '1.2.3.4',
        'dest_ip': '5.6.7.8',
        'port': '(80,443)',
        'bidirectional': 'False',
        'color': 'blue',
    }
    assert params == expected


def test_get_translation_table():
    r = get_dummy_rule()
    params = r.get_translation_table()
    expected = {
        'alert_active': constants.security['alert_active'],
        'alert_severity': '8',
        'alert_label': 'Special Label',
        'email_active': constants.security['email_active'],
        'email_address': 'abc@zyx.com',
        'email_subject': '[SAM] Special Email Subject',
        'sms_active': constants.security['sms_active'],
        'sms_number': '1 123 456 7890',
        'sms_message': '[SAM] Special SMS Message',
        'source_ip': '1.2.3.4',
        'dest_ip': '5.6.7.8',
        'port': '(80,443)',
        'bidirectional': 'False',
        'color': 'blue',
        'bad_hosts': "['1.2.3.4', '2.3.4.5', '3.4.5.6', '4.5.6.7', '5.6.7.8', '6.7.8.9', '7.8.9.0', '79.146.47.84']",
        'rule_desc': 'Description of My Test Rule',
        'rule_name': 'My Test Rule'
    }
    assert params == expected

    # try out the pretranslate
    r.set_action_params({'alert_label': 'Special $rule_name Label', 'email_subject': '[SAM] $color'})
    params = r.get_translation_table()
    assert params['alert_label'] == 'Special My Test Rule Label'
    assert params['email_subject'] == '[SAM] blue'


def test_get_conditions():
    r = get_dummy_rule()
    assert r.get_conditions() == "src host $source_ip and dst host $dest_ip and dst port $port"
    r = rule.Rule(123, True, "my rule", "description of my rule", 'compromised.yml')
    assert r.get_conditions() == "dst host in $bad_hosts"
    r = rule.Rule(123, True, "my rule", "description of my rule", 'dos.yml')
    assert r.get_conditions() == "having conn[links] > $threshold"
    r = rule.Rule(123, True, "my rule", "description of my rule", 'plugin: missing_plugin.yml')
    assert r.get_conditions() == "Error."


def test_export_params():
    r = get_dummy_rule()
    params = r.export_params()
    assert set(params.keys()) == {'actions', 'exposed'}
    expected_actions = {
        'alert_active': constants.security['alert_active'],
        'alert_severity': '8',
        'alert_label': 'Special Label',
        'email_active': constants.security['email_active'],
        'email_address': 'abc@zyx.com',
        'email_subject': '[SAM] Special Email Subject',
        'sms_active': constants.security['sms_active'],
        'sms_number': '1 123 456 7890',
        'sms_message': '[SAM] Special SMS Message',
    }
    assert params['actions'] == expected_actions
    expected_exposed = {
        'source_ip': '1.2.3.4',
        'dest_ip': '5.6.7.8',
        'port': '(80,443)',
        'bidirectional': 'False',
        'color': 'blue',
    }
    assert params['exposed'] == expected_exposed


def test_load_yml():
    r = rule.Rule(123, True, "my rule", "description of my rule", 'compromised.yml')
    assert isinstance(r.definition, rule_template.RuleTemplate)
    assert r.active == True
    r = rule.Rule(123, True, "my rule", "description of my rule", 'plugin: missing_plugin.yml')
    assert r.definition is None
    assert r.active == False

