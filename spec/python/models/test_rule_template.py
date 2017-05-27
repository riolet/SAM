import os
import yaml
import pytest
from sam import constants
from sam.models import rule_template


def test_get_all():
    all_templates = rule_template.get_all()
    all_templates.sort()
    expected = [
        'compromised.yml',
        'dos.yml',
        'netscan.yml',
        'portscan.yml',
        'suspicious.yml',
        'unexpected.yml'
    ]
    expected.sort()
    assert all_templates == expected


def test_abs_rule_path():
    s = 'compromised.yml'
    found = rule_template.abs_rule_path(s)
    assert os.path.exists(found)

    s = 'error.yml'
    not_found = rule_template.abs_rule_path(s)
    assert not_found is None


def test_get_definition():
    s = 'compromised.yml'
    dfn = rule_template.get_definition(s)
    assert dfn is None

    dfn = rule_template.get_definition(rule_template.abs_rule_path(s))
    assert isinstance(dfn, rule_template.RuleTemplate)


def test_yml_compromised():
    s = 'compromised.yml'
    dfn = rule_template.get_definition(rule_template.abs_rule_path(s))
    assert isinstance(dfn, rule_template.RuleTemplate)


def xtest_yml_dos():
    s = 'dos.yml'
    dfn = rule_template.get_definition(rule_template.abs_rule_path(s))
    assert isinstance(dfn, rule_template.RuleTemplate)


def xtest_yml_netscan():
    s = 'netscan.yml'
    dfn = rule_template.get_definition(rule_template.abs_rule_path(s))
    assert isinstance(dfn, rule_template.RuleTemplate)


def xtest_yml_portscan():
    s = 'portscan.yml'
    dfn = rule_template.get_definition(rule_template.abs_rule_path(s))
    assert isinstance(dfn, rule_template.RuleTemplate)


def xtest_yml_suspicious():
    s = 'suspicious.yml'
    dfn = rule_template.get_definition(rule_template.abs_rule_path(s))
    assert isinstance(dfn, rule_template.RuleTemplate)


def xtest_yml_unexpected():
    s = 'unexpected.yml'
    dfn = rule_template.get_definition(rule_template.abs_rule_path(s))
    assert isinstance(dfn, rule_template.RuleTemplate)

# ----------------- RuleTemplate ----------------------
dummy_yml = """---
name: Test Yaml
type: immediate
include:
  bad_hosts: ./compromised_hosts.txt
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
  severity:
    format: text
    label: Alert severity
    default: 2
    regex: "[1-8]"
  sendmail:
    format: checkbox
    label: Send email?
    default: 0
  color:
    format: dropdown
    label: Favorite Color
    default: blue
    options:
      - red
      - blue
      - green
actions:
 - type: alert
   severity: $severity
   label: $alert_label

 - type: email
   address: supe@example.com
   subject: "[SAM] Security Rule $name triggered"
   
 - type: sms
   number: +1-555-321-7789
   message: "[SAM] Security Rule $name triggered"
when: src host $source_ip and dst host $dest_ip and dst port $port
"""


def get_test_rule_template():
    """
     :rtype: rule_template.RuleTemplate
    """
    global dummy_yml
    data = yaml.load(dummy_yml)
    base_path = os.path.dirname(rule_template.__file__)
    rule_path = os.path.join(base_path, os.path.pardir, constants.templates_folder)
    template = rule_template.RuleTemplate(rule_path, data)
    return template


def test_load_exposed_text():
    rt = get_test_rule_template()

    good_text = {'expose': {'test_param': {
        'format': 'text',
        'label': 'test label',
        'default': '1.2.3.4',
        'regex': '^([0-9]|[01]?[0-9][0-9]|2[0-4][0-9]|25[0-5])(\\.([0-9]|[01]?[0-9][0-9]|2[0-4][0-9]|25[0-5])){3}$'
    }}}
    sample = rt.load_exposed(good_text)
    assert len(sample) == 1
    assert sample['test_param']['value'] == '1.2.3.4'
    assert sample['test_param']['regex'] == '^([0-9]|[01]?[0-9][0-9]|2[0-4][0-9]|25[0-5])(\\.([0-9]|[01]?[0-9][' \
                                            '0-9]|2[0-4][0-9]|25[0-5])){3}$'
    assert 'regex_compiled' in sample['test_param']
    assert sample['test_param']['format'] == 'text'
    assert sample['test_param']['label'] == 'test label'

    bad_regex = {'expose': {'test_param': {
        'format': 'text',
        'label': 'test label',
        'default': '1.2.3.4',
        'regex': '('
    }}}
    sample = rt.load_exposed(bad_regex)
    assert len(sample) == 1
    assert sample['test_param']['value'] == '1.2.3.4'
    assert 'regex' not in sample['test_param']
    assert 'regex_compiled' not in sample['test_param']
    assert sample['test_param']['format'] == 'text'
    assert sample['test_param']['label'] == 'test label'

    no_regex = {'expose': {'test_param': {
        'format': 'text',
        'label': 'test label',
        'default': '1.2.3.4'
    }}}
    sample = rt.load_exposed(no_regex)
    assert len(sample) == 1
    keys = sorted(sample['test_param'].keys())
    assert keys == ['format', 'label', 'value']

    no_format = {'expose': {'test_param': {
        'label': 'test label',
        'default': '1.2.3.4'
    }}}
    sample = rt.load_exposed(no_format)
    assert len(sample) == 0

    no_label = {'expose': {'test_param': {
        'format': 'text',
        'default': '1.2.3.4'
    }}}
    sample = rt.load_exposed(no_label)
    assert len(sample) == 0

    no_default = {'expose': {'test_param': {
        'format': 'text',
        'label': 'test label'
    }}}
    sample = rt.load_exposed(no_default)
    assert len(sample) == 0


def test_load_exposed_checkbox():
    rt = get_test_rule_template()

    good_checkbox = {'expose': {'test_param': {
        'format': 'checkbox',
        'label': 'test label',
        'default': '0',
    }}}
    sample = rt.load_exposed(good_checkbox)
    assert len(sample) == 1

    no_format = {'expose': {'test_param': {
        'label': 'test label',
        'default': '0'
    }}}
    sample = rt.load_exposed(no_format)
    assert len(sample) == 0

    no_label = {'expose': {'test_param': {
        'format': 'checkbox',
        'default': '0'
    }}}
    sample = rt.load_exposed(no_label)
    assert len(sample) == 0

    no_default = {'expose': {'test_param': {
        'format': 'checkbox',
        'label': 'test label'
    }}}
    sample = rt.load_exposed(no_default)
    assert len(sample) == 0


def test_load_exposed_dropdown():
    rt = get_test_rule_template()

    good_dropdown = {'expose': {'test_param': {
        'format': 'dropdown',
        'label': 'test label',
        'default': 'blue',
        'options': ['red', 'blue', 'green']
    }}}
    sample = rt.load_exposed(good_dropdown)
    assert len(sample) == 1
    assert sample['test_param']['options'] == ['red', 'blue', 'green']

    no_options = {'expose': {'test_param': {
        'format': 'dropdown',
        'label': 'test label',
        'default': 'blue'
    }}}
    sample = rt.load_exposed(no_options)
    assert len(sample) == 0

    no_format = {'expose': {'test_param': {
        'label': 'test label',
        'default': 'blue',
        'options': ['red', 'blue', 'green']
    }}}
    sample = rt.load_exposed(no_format)
    assert len(sample) == 0

    no_label = {'expose': {'test_param': {
        'format': 'dropdown',
        'default': 'blue',
        'options': ['red', 'blue', 'green']
    }}}
    sample = rt.load_exposed(no_label)
    assert len(sample) == 0

    no_default = {'expose': {'test_param': {
        'format': 'dropdown',
        'label': 'test label',
        'options': ['red', 'blue', 'green']
    }}}
    sample = rt.load_exposed(no_default)
    assert len(sample) == 0


def test_load_inclusions():
    rt = get_test_rule_template()

    good_include = {'include': {
        'inc_1': './compromised_hosts.txt'
    }}
    inclusions = rt.load_inclusions(good_include)
    assert len(inclusions) == 1
    assert len(inclusions['inc_1']) > 500

    bad_include = {'include': {
        'inc_1': './uncompromising_hosts.txt'
    }}
    inclusions = rt.load_inclusions(bad_include)
    assert len(inclusions) == 0


def test_load_actions_alert():
    rt = get_test_rule_template()

    good_alert = {'actions': [{
        'type': 'alert',
        'severity': '5',
        'label': 'hello'
    }]}
    actions = rt.load_actions(good_alert)
    assert len(actions) == 1
    assert sorted(actions[0].keys()) == ['label', 'severity', 'type']

    bad_alert1 = {'actions': [{
        'type': 'alert',
        'severity': '5'
    }]}
    with pytest.raises(ValueError):
        actions = rt.load_actions(bad_alert1)
        assert len(actions) == 0

    bad_alert2 = {'actions': [{
        'type': 'alert',
        'label': 'hello'
    }]}
    with pytest.raises(ValueError):
        actions = rt.load_actions(bad_alert2)
        assert len(actions) == 0


def test_load_actions_email():
    rt = get_test_rule_template()

    good_email = {'actions': [{
        'type': 'email',
        'address': 'example@example.com',
        'subject': '[SAM] Security Rule $name triggered'
    }]}
    actions = rt.load_actions(good_email)
    assert len(actions) == 1
    assert sorted(actions[0].keys()) == ['address', 'subject', 'type']

    bad_email1 = {'actions': [{
        'type': 'email',
        'subject': '[SAM] Security Rule $name triggered'
    }]}
    with pytest.raises(ValueError):
        actions = rt.load_actions(bad_email1)
        assert len(actions) == 0

    bad_email2 = {'actions': [{
        'type': 'email',
        'address': 'example@example.com',
    }]}
    with pytest.raises(ValueError):
        actions = rt.load_actions(bad_email2)
        assert len(actions) == 0


def test_load_actions_sms():
    rt = get_test_rule_template()

    good_sms = {'actions': [{
        'type': 'sms',
        'number': '+1-555-123-7789',
        'message': '[SAM] Security Rule $name triggered'
    }]}
    actions = rt.load_actions(good_sms)
    assert len(actions) == 1
    assert sorted(actions[0].keys()) == ['message', 'number', 'type']

    bad_sms1 = {'actions': [{
        'type': 'sms',
        'message': '[SAM] Security Rule $name triggered'
    }]}
    with pytest.raises(ValueError):
        actions = rt.load_actions(bad_sms1)
        assert len(actions) == 0

    bad_sms2 = {'actions': [{
        'type': 'sms',
        'number': '+1-555-123-7789'
    }]}
    with pytest.raises(ValueError):
        actions = rt.load_actions(bad_sms2)
        assert len(actions) == 0

