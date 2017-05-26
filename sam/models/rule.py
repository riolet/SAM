import re
from sam.models import rule_template


class Rule(object):
    def __init__(self, rule_id, active, name, description, path):
        self.id = rule_id
        self.active = active
        self.name = name
        self.desc = description
        self.path = path
        self.params = {}
        self.definition = self.load_yml()

    def nice_path(self):
        nice_name = self.path
        if nice_name[:7] == 'plugin:':
            nice_name = nice_name[7:]
        if nice_name[-4:].lower() == '.yml':
            nice_name = nice_name[:-4]
        return nice_name

    def translate(self, s, replacements):
        """
        :param s:
         :type s: str or unicode
        :param replacements: 
         :type replacements: dict[str, Any]
        :return:
        """
        for key, value in replacements.iteritems():
            s = re.sub("\${}".format(key), unicode(value), unicode(s))
        return s

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

    def set_params(self, params):
        exposed = self.definition.exposed
        key_matches = [key for key in exposed.keys() if key in params]
        for key in key_matches:
            p_format = exposed[key]['format']
            new_value = params[key]
            if p_format == 'text':
                if 'regex_compiled' in exposed[key]:
                    regex = exposed[key]['regex_compiled']
                    if new_value is not None and regex.match(unicode(new_value)) is not None:
                        self.params[key] = new_value
                    else:
                        # print("regex failed")
                        pass
                else:
                    self.params[key] = new_value
            elif p_format == 'checkbox':
                if unicode(new_value).lower() == 'true':
                    self.params[key] = True
                elif unicode(new_value).lower() == 'false':
                    self.params[key] = False
                else:
                    # new value doesn't match true or false, so leave the existing value unchanged.
                    pass
            elif p_format == 'dropdown':
                if new_value in exposed[key]['options']:
                    self.params[key] = new_value
                else:
                    # new value isn't one of the acceptable options, so use the existing value unchanged.
                    pass
            else:
                # parameter format isn't recognized, so do not change anything.
                pass

    def get_params(self):
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
        if self.definition is None:
            return {}

        params = self.definition.exposed

        # apply stored values, where available.
        for key in params.keys():
            if key in self.params:
                params[key]['value'] = self.params[key]

        return params

    def get_conditions(self):
        cond = self.definition.when
        # replace when a simple string. Do not just replace collections.
        translated = self.translate(cond, self.params)
        return translated

    def get_actions(self):
        # replace vars when a simple string. Do not just replace collections.
        actions = []
        for original_action in self.definition.actions:
            action = {}
            for key, value in original_action.iteritems():
                d_key = "${}".format(value)
                if d_key in self.params:
                    action[key] = self.params[d_key]
                else:
                    action[key] = self.translate(value, self.params)
            actions.append(action)
        return actions

    def get_inclusions(self):
        return self.definition.inclusions

    def export_params(self):
        """
        Get all the param values as a dict
        :return: 
        """
        return {k: v['value'] for k, v in self.get_params().iteritems()}

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
