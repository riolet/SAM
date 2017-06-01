import os
import traceback
import re
import yaml
from sam import constants

# will have compromisedhosts.yml, suspicioustraffic.yml, dos.yml, ...
# they will expose some controls, such as for dos:
# expose "tolerance"
#   valid: "\d+"
#   title: "Minimum connections per second to flag"
# YML files include sections:
#   include: (for files, databases)
#   exposed: (for values that should be configurable within the app)
#   action: email, create alert,
#   when: define the trigger conditions


def get_all():
    return filter(lambda f: f.endswith(".yml"), os.listdir(constants.rule_templates_path))


def abs_rule_path(path):
    if path[0:7] == "plugin:":
        abspath = os.path.join(constants.plugins['root'], path[7:])
        if not os.path.exists(abspath):
            print('WARNING: absolute rule path not found.')
            print('  (Checked "{}"->"{}")'.format(path, abspath))
            return None
    else:
        abspath = os.path.join(constants.rule_templates_path, path)
        if not os.path.exists(abspath):
            print('WARNING: Cannot find definition file.')
            print('  (Checked "{}"->"{}")'.format(path, abspath))
            return None
    return abspath


def get_definition(path, cache={}):
    if path in cache:
        return cache[path]
    else:
        try:
            with open(path, 'r') as f:
                data = yaml.load(f)
            rule_def = RuleTemplate(os.path.dirname(path), data)
        except:
            # print errors, but move on.
            traceback.print_exc()
            return None
        cache[path] = rule_def
        return rule_def


class RuleTemplate(object):
    """
    Represents the YML file that describes the rule. Meant to be READ ONLY.
    """
    def __init__(self, path, yml):
        self.cwd = path
        self._yml = yml
        self.name = "Unknown"
        self.type = "Unknown"
        self.subject = "Unknown"
        self._exposed = {}
        self._action_defaults = {}
        self._inclusions = {}
        self.when = ""

        self.import_yml(yml)

    def import_yml(self, data):
        self.name = data.get('name', None)
        self.type = data.get('type', None)
        self.subject = data.get('subject', None)
        self.when = data.get('when', None)

        if not self.name:
            raise ValueError("Bad rule: 'name' key not found.")
        elif not self.subject:
            raise ValueError("Bad rule: 'subject' key not found.")
        elif not self.type:
            raise ValueError("Bad rule: 'type' key not found.")
        elif not self.when:
            raise ValueError("Bad rule: 'when' key not found.")

        self._exposed = RuleTemplate.load_exposed(self._yml)
        self._inclusions = self.load_inclusions(self._yml)
        self._action_defaults = RuleTemplate.load_action_defaults(self._yml)

    @staticmethod
    def load_exposed(yml):
        exposed = {}
        if 'expose' not in yml or yml['expose'] is None:
            return exposed

        for key, param in yml['expose'].iteritems():
            label = param.get('label', None)
            format_ = param.get('format', None)
            default = param.get('default', None)
            if default is not None:
                default = str(default)
            regex = param.get('regex', None)
            options = param.get('options', None)

            if label is None or format_ is None or default is None:
                print("Unable to expose parameter {}: Missing keys '{}'".format(key, "', '".join(
                    [x[1] for x in [(label, "label"), (format_, "format"), (default, "default")] if x[0] is None])))
                continue
            exposed_param = {
                'label': label,
                'format': format_,
                'value': default
            }
            if format_ == 'checkbox':
                pass
            elif format_ == 'text':
                if regex is not None:
                    try:
                        compiled_regex = re.compile(regex)
                        exposed_param['regex'] = regex
                        exposed_param['regex_compiled'] = compiled_regex
                    except:
                        print("Unable to compile regular expression: /{}/".format(repr(regex)))
            elif format_ == 'dropdown':
                if options is None:
                    print("Missing options for exposed parameter {}".format(key))
                    continue
                exposed_param['options'] = options
            else:
                print("Invalid format for exposed parameter {}".format(key))
                continue

            exposed[key] = exposed_param
        return exposed

    @staticmethod
    def load_inclusions(yml):
        inclusions = {}
        if not yml.get('include', None):
            return inclusions
        for ref in yml['include'].keys():
            path = os.path.join(constants.rule_templates_path, yml['include'][ref])
            try:
                with open(path, 'r') as f:
                    data = f.read()
                inclusions[ref] = data.splitlines()
                # print("loaded inclusion: {}".format(inclusions[ref]))
            except Exception as e:
                print("Failed to load inclusion {}: {}".format(ref, str(e)))
        return inclusions

    @staticmethod
    def load_action_defaults(yml):
        actions = {}
        yml_actions = yml.get('actions', {})
        if not yml_actions:
            return actions

        for key, def_value in yml_actions.items():
            if key in ['alert_severity', 'alert_label', 'email_address', 'email_subject', 'sms_number', 'sms_message']:
                actions[key] = def_value
        return actions

    def get_exposed(self):
        return {k: v.copy() for k, v in self._exposed.iteritems()}

    def get_action_defaults(self):
        return self._action_defaults.copy()

    def get_inclusions(self):
        return self._inclusions.copy()