import re
from sam.models import rule_template
from sam import constants


class Rule(object):
    ACTION_KEYS = ['alert_active', 'alert_severity', 'alert_label',
                   'email_active', 'email_address', 'email_subject',
                   'sms_active', 'sms_number', 'sms_message']

    def __init__(self, rule_id, active, name, description, path):
        self.id = rule_id
        self.active = active
        self.name = name
        self.desc = description
        self.path = path
        self.definition = self.load_yml()
        self.exposed_params = self.get_initial_exposed_params()
        # exposed_params is a dict of dicts where each value dict has type, format, value...
        self.action_params = self.get_initial_action_params()
        # action_params is a dict with the action keys above

    def nice_path(self):
        nice_name = self.path
        if nice_name[:7] == 'plugin:':
            nice_name = nice_name[7:]
        if nice_name[-4:].lower() == '.yml':
            nice_name = nice_name[:-4]
        return nice_name

    def get_type(self):
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
        # get all exposed parameters
        exposed = self.definition.get_exposed()
        return exposed

    def get_initial_action_params(self):
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

        # update action parameters to rule definitions as needed
        action_defaults = self.definition.get_action_defaults()
        for k, v in action_defaults.iteritems():
            a_params[k] = v

        return a_params

    def set_params(self, new_action_params, new_exposed_params):
        # import new action params:
        valid_keys = [key for key in new_action_params.keys() if key in self.action_params]
        for key in valid_keys:
            # TODO: validate new value
            self.action_params[key] = new_action_params[key]

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
        p_values = {
            'alert_active': constants.security['alert_active'],
            'alert_severity': constants.security['alert_active'],
            'alert_label': constants.security['alert_active'],
            'email_active': constants.security['email_active'],
            'email_address': constants.security['email_address'],
            'email_subject': constants.security['email_subject'],
            'sms_active': constants.security['sms_active'],
            'sms_number': constants.security['sms_number'],
            'sms_message': constants.security['sms_message']
        }

        # update action parameters to rule definitions as needed
        action_defaults = self.definition.get_action_defaults()
        for k, v in action_defaults.iteritems():
            p_values[k] = v

        # get all exposed parameters
        exposed = self.get_exposed_params()
        p_values.update(exposed)

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
        # get default action parameters
        tr_table = {
            'alert_active': constants.security['alert_active'],
            'alert_severity': constants.security['alert_active'],
            'alert_label': constants.security['alert_active'],
            'email_active': constants.security['email_active'],
            'email_address': constants.security['email_address'],
            'email_subject': constants.security['email_subject'],
            'sms_active': constants.security['sms_active'],
            'sms_number': constants.security['sms_number'],
            'sms_message': constants.security['sms_message']
        }

        # update action parameters to rule definitions as needed
        action_defaults = self.definition.get_action_defaults()
        for k, v in action_defaults.iteritems():
            tr_table[k] = v

        # get all exposed parameters
        exposed = self.get_exposed_params()
        for k, v in exposed.iteritems():
            tr_table[k] = v['value']

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
