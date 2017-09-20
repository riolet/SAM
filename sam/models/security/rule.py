import os
import re
import yaml
import operator
import web
from sam.models.security import rule_template, rule_parser
from sam import constants


def validate_rule(path, db, sub_id, ds_id, args):
    """

    :param path: rule template path. relative or absolute.
    :param db: database connection
    :type db: web.DB
    :param sub_id: subscription id
    :param ds_id: datasource id
    :param args: any extra args in the invocation.
    :return:
    """
    path = os.path.abspath(path)
    if not os.path.exists(path):
        print("Rule not found: {}".format(path))
        return False
    try:
        with open(path, 'r') as f:
            data = yaml.load(f)
        template = rule_template.RuleTemplate(os.path.dirname(path), data)
    except Exception as e:
        print("Error parsing template: {}".format(str(e)))
        return False
    placeholder = rule_template.get_all()[0]
    rule = Rule(1, False, "test", "test desc", placeholder)
    rule.definition = template
    rule.exposed_params = rule.get_initial_exposed_params()
    rule.action_params = rule.get_initial_action_params()

    # basic rule data
    print("="*70)
    print("Rule name: {}".format(template.name))
    if template.type == template._yml.get('type'):
        print("Rule type: {}".format(template.type))
    else:
        print("* Rule type: {} (failed; reverted to {})".format(template._yml.get('type'), template.type))
    if template.subject == template._yml.get('subject'):
        print("Rule subject: {}".format(template.subject))
    else:
        print("* Rule subject: {} (failed; reverted to {})".format(template._yml.get('subject'), template.subject))

    # included files
    incs = template.get_inclusions()
    yml_incs = template._yml.get("include")
    if not yml_incs or len(yml_incs) == 0:
        print("Rule inclusions: None")
    else:
        print("Rule inclusions:")
        for key, val in yml_incs.iteritems():
            print("\t({}) {}: {}".format("passed" if key in incs else "failed; not found", key, val))
    if yml_incs and len(yml_incs) != len(incs):
        return False

    # exposed parameters
    exps = template.get_exposed()
    yml_exps = template._yml.get("expose")
    if not yml_exps or len(yml_exps) == 0:
        print("Exposed parameters: None")
    else:
        print("Exposed parameters:")
        for key, val in yml_exps.iteritems():
            print("\t({}) {}:".format("passed" if key in exps else "failed", key, val))
            for k, v in val.iteritems():
                if k in ['label', 'format', 'default', 'options']:
                    print("\t\t{}: {}".format(k, v))
                elif k == 'regex':
                    if key in exps and 'regex_compiled' in exps[key]:
                        print("\t\tregex (valid): {}".format(yml_exps[key]['regex']))
                    else:
                        print("\t   *\tregex (invalid): {}".format(yml_exps[key]['regex']))
                else:
                    print("\t   *\t{} (invalid): {}".format(k, v))
    if yml_exps and len(yml_exps) != len(exps):
        return False

    # default actions
    acts = template.get_action_defaults()
    yml_acts = template._yml.get('actions')
    if not yml_acts or len(yml_acts) == 0:
        print("Action defaults: None")
    else:
        print("Action defaults:")
        for key, val in yml_acts.iteritems():
            print("{} {}: {}".format('\t(passed)' if key in acts else '   *\t(failed)', key, val))

    # when / trigger conditions
    translations = rule.get_translation_table()
    conditions = rule.get_conditions()
    subject = rule.definition.subject
    try:
        rp = rule_parser.RuleParser(translations, subject, conditions, None)
    except Exception as e:
        print("Trigger condition: Failed")
        print("\t{}".format(e))
        return False
    print("Trigger condition:\n\t{}".format(conditions))
    tokens = rule_parser.RuleParser.tokenize(conditions)
    rule_parser.RuleParser.decode_tokens(translations, tokens)
    translated = ' '.join(map(str, map(operator.itemgetter(1), tokens)))
    print("Translated condition:\n\t{}".format(translated))
    sql = rp.sql.get_query('s{}_ds{}_Links'.format(sub_id, ds_id))

    # SQL tests
    print("\nRule SQL: ")
    print(sql)
    t = db.transaction()
    try:
        db.query(sql)
    except Exception as e:
        print("\nTest SQL execution: Failed")
        print(e)
        return False
    else:
        print("\nTest SQL execution: Success")
    finally:
        t.rollback()

    print("")
    return True


class Rule(object):
    ACTION_KEYS = ['alert_active', 'alert_severity', 'alert_label',
                   'email_active', 'email_address', 'email_subject',
                   'sms_active', 'sms_number', 'sms_message']

    def __init__(self, rule_id, active, name, description, path):
        """

        :param rule_id: ID to match this rule to a database entry
        :param active: True or False. Is this rule in effect?
        :param name: Short Name of this rule
        :param description: Long Description of this rule
        :param path: Path to the rule template file.
            Path may have a prefix of "custom: " or "plugin: "
            Path is either in default rule folder:
                "compromised.yml", "dos.yml"
            Or in custom rule folder:  (defined in constants.security['rule_folder']
                "custom: test_rule.yml"
            Or in a plugin-defined folder:  (list of folders is constants.plugin_rules)
                "plugin: my-plugin-rule.yml"
        """
        self.id = rule_id
        self.active = active
        self.name = name
        self.desc = description
        self.path = path
        self.definition = self.load_yml()
        # exposed_params is a dict of dicts where each value dict has type, format, value...
        self.exposed_params = self.get_initial_exposed_params()
        # action_params is a dict with the keys ACTION_KEYS defined above
        self.action_params = self.get_initial_action_params()

    def nice_path(self, path):
        nice_name = path
        if nice_name[:7] == 'plugin:':
            nice_name = nice_name[7:].lstrip()
        if nice_name[:7] == 'custom:':
            nice_name = nice_name[7:].lstrip()
        if nice_name[-4:].lower() == '.yml':
            nice_name = nice_name[:-4]
        return nice_name

    def get_type(self):
        if self.definition is None:
            return "Error."
        else:
            return self.definition.type

    def get_def_name(self):
        if self.definition is None:
            return "Error."
        else:
            return self.definition.name

    def is_active(self):
        return self.active

    def get_name(self):
        return self.name

    def get_desc(self):
        return self.desc

    def get_initial_exposed_params(self):
        """
        :rtype: dict
        """
        # get all exposed parameters
        if self.definition:
            exposed = self.definition.get_exposed()
        else:
            exposed = {}

        return exposed

    def get_initial_action_params(self):
        """
        Builds a dictionary of actions for the rule to perform on a match.
            - Fills in default values from config file.
            - Overrides those defaults with any optional defaults found
                in the rule definition file.
        :return:
        :rtype: dict [str, str]
        """
        a_params = {
            'alert_active': constants.security['alert_active'],
            'alert_severity': constants.security['alert_severity'],
            'alert_label': constants.security['alert_label'],
            'email_active': constants.security['email_active'],
            'email_address': constants.security['email_address'],
            'email_subject': constants.security['email_subject'],
            'sms_active': constants.security['sms_active'],
            'sms_number': constants.security['sms_number'],
            'sms_message': constants.security['sms_message']
        }

        if self.definition:
            # update action parameters to rule definitions as needed
            action_defaults = self.definition.get_action_defaults()
            for k, v in action_defaults.iteritems():
                a_params[k] = v

        a_params['alert_severity'] = str(a_params['alert_severity'])

        return a_params

    def set_action_params(self, new_action_params):
        # import new action params:
        valid_keys = [key for key in new_action_params.keys() if key in self.action_params]
        for key in valid_keys:
            # TODO: validate new value
            self.action_params[key] = new_action_params[key]

    def set_exposed_params(self, new_exposed_params):
        # import new exposed param values
        valid_keys = [key for key in new_exposed_params.keys() if key in self.exposed_params]
        for key in valid_keys:
            p_format = self.exposed_params[key]['format']
            new_value = unicode(new_exposed_params[key])
            if p_format == 'text':
                if 'regex_compiled' in self.exposed_params[key]:
                    regex = self.exposed_params[key]['regex_compiled']
                    if new_value is not None and regex.match(new_value) is not None:
                        self.exposed_params[key]['value'] = new_value
                    else:
                        # print("regex failed")  # keep the default value.
                        pass
                else:
                    self.exposed_params[key]['value'] = new_value
            elif p_format == 'checkbox':
                if new_value.lower() == 'true':
                    self.exposed_params[key]['value'] = 'true'
                elif new_value.lower() == 'false':
                    self.exposed_params[key]['value'] = 'false'
                else:
                    # new value doesn't match true or false, so leave the existing value unchanged.
                    pass
            elif p_format == 'dropdown':
                if new_value in self.exposed_params[key]['options']:
                    self.exposed_params[key]['value'] = new_value
                else:
                    # new value isn't one of the acceptable options, so use the existing value unchanged.
                    pass
            else:
                # parameter format isn't recognized, so do not change anything.
                pass

    def get_exposed_params(self):
        """
        Gets a dictionary of params like:
        params = {
            <key1> = {
                label: <nice_text>
                format: (text|dropdown|checkbox)
                value: the current value of the parameter, either the default value or the value saved in the db.
                regex: optional regex to validate text format
                options: list of acceptable values, mandatory for dropdown format
            }
        }
        """
        return self.exposed_params

    def get_action_params(self):
        """
        Gets a dictionary of action-related params and their values like:
        params = {
            'alert_active': 'true',
            'sms_number': '555-213-7749',
            ...
        }
        """
        return self.action_params

    def get_actions(self):
        """
        Get a list of actions to perform when rules match. Only returns active actions.
        returns something like:
        actions = [
            {type: alert, severity: 2, label: "Unusual Connection"},
            {type: email, address: "jdoe@example.com", subject: "[SAM] Rule $rule_name Triggered"},
            {type: sms, number: "11234567890", msg: "[SAM] Rule $rule_name Triggered"}
        ]
        :return:
         :rtype: list[ dict[str, str] ]
        """
        params = self.get_action_params()
        actions = []
        if params['alert_active'].lower() == 'true':
            actions.append({
                'type': 'alert',
                'severity': params['alert_severity'],
                'label': params['alert_label']
            })
        if params['email_active'].lower() == 'true':
            actions.append({
                'type': 'email',
                'address': params['email_address'],
                'subject': params['email_subject']
            })
        if params['sms_active'].lower() == 'true':
            actions.append({
                'type': 'sms',
                'number': params['sms_number'],
                'message': params['sms_message']
            })
        return actions

    def get_param_values(self):
        """
        All params as key-value pairs.
        Parameters included:
            1. All action parameters: alert (active, severity, label), email (active, address, subject), sms (active, number, message).
            2. All exposed parameters.

        Resolution order is:
            1. Default values from constants.py (from default.cfg or environment variables).
            2. Default values from rule definition.
            3. Values stored in database.

        :return:
        """
        p_values = dict(self.get_action_params())

        # get all exposed parameters
        exposed = self.get_exposed_params()
        for k, v in exposed.iteritems():
            p_values[k] = v['value']

        return p_values

    def get_translation_table(self):
        """
        All translation params as key-value pairs.
        Parameters included:
            1. All action parameters: alert_(active, severity, label), email_(active, address, subject), sms_(active, number, message).
            2. All exposed parameters.
            3. Metadata params: rule_name, rule_desc
            4. Included data

        Resolution order is:
            1. Default values from constants.py (from default.cfg or environment variables).
            2. Default values from rule definition.
            3. Values stored in database.
        :return:
        """
        # get action parameters and exposed parameters
        tr_table = self.get_param_values()

        # get all metadata parameters
        tr_table['rule_name'] = self.name
        tr_table['rule_desc'] = self.desc

        # get all inclusions
        tr_table.update(self.definition.get_inclusions())

        # pretranslate symbols where possible.
        for key, value in tr_table.iteritems():
            tr_table[key] = re.sub(r'\$(\S+)', lambda match: tr_table[match.group(1)] if match.group(1) in tr_table else match.group(1), unicode(value))

        return tr_table

    def get_conditions(self):
        if self.definition is None:
            return "Error."
        else:
            return self.definition.when

    def export_params(self):
        """
        Get all saveable values for persistant storage. Looks like:
        params = {
            'actions': {
                'alert_active': 'true',
                'alert_label': 'test',
                [...]
            },
            'exposed': {
                [...]
            }
        }
        """
        actions = {k: v for k, v in self.get_action_params().iteritems()}
        exposed = {k: v['value'] for k, v in self.get_exposed_params().iteritems()}
        params = {
            'actions': actions,
            'exposed': exposed,
        }
        return params

    def load_yml(self):
        """
        :return: the original rule template, loaded from its YML file, or None.
         :rtype: rule_template.RuleTemplate or None
        """
        abs_path = rule_template.abs_rule_path(self.path)
        rule_def = rule_template.get_definition(abs_path)
        if rule_def is None:
            self.active = False
        return rule_def

    def __str__(self):
        return '<Rule {}: "{}">'.format(self.id, self.name)

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        if isinstance(other, Rule):
            return self.id == other.id
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)
