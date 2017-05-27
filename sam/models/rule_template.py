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
        self.yml = yml
        self.type = "Unknown"
        self.name = "Unknown"
        self.exposed = {}
        self.actions = []
        self.inclusions = {}
        self.when = ""

        self.import_yml(yml)

    def import_yml(self, data):
        try:
            self.name = data['name']
            self.type = data['type']
        except:
            if 'name' not in data:
                raise ValueError("Bad rule: 'name' key not found.")
            else:
                raise ValueError("Bad rule: 'type' key not found.")

        self.exposed = self.load_exposed(self.yml)
        self.inclusions = self.load_inclusions(self.yml)
        self.actions = self.load_actions(self.yml)
        self.when = self.load_conditions(self.yml)

    def load_exposed(self, yml):
        if 'expose' not in yml:
            return
        exposed = {}

        for key, param in yml['expose'].iteritems():
            label = param.get('label', None)
            format = param.get('format', None)
            default = param.get('default', None)
            if default is not None:
                default = str(default)
            regex = param.get('regex', None)
            options = param.get('options', None)

            if label is None or format is None or default is None:
                print("Unable to expose parameter {} of {}: Missing keys '{}'".format(key, self.name, "', '".join([x[1] for x in [(label, "label"), (format, "format"), (default, "default")] if x[0] is None])))
                continue
            exposed_param = {
                'label': label,
                'format': format,
                'value': default
            }
            if format == 'checkbox':
                pass
            elif format == 'text':
                if regex is not None:
                    try:
                        compiled_regex = re.compile(regex)
                        exposed_param['regex'] = regex
                        exposed_param['regex_compiled'] = compiled_regex
                    except:
                        print("Unable to compile regular expression: /{}/".format(repr(regex)))
            elif format == 'dropdown':
                if options is None:
                    print("Missing options for exposed parameter {}".format(key))
                    continue
                exposed_param['options'] = options
            else:
                print("Invalid format for exposed parameter {}".format(key))
                continue

            exposed[key] = exposed_param
        return exposed

    def load_inclusions(self, yml):
        inclusions = {}
        if not yml.get('include', None):
            return
        for ref in yml['include'].keys():
            path = os.path.join(self.cwd, yml['include'][ref])
            try:
                with open(path, 'r') as f:
                    data = f.read()
                inclusions[ref] = data.splitlines()
            except Exception as e:
                print("Failed to load inclusion {}: {}".format(ref, str(e)))
        return inclusions

    def load_actions(self, yml):
        yml_actions = yml.get('actions', [])
        actions = []
        for action in yml_actions:
            if 'type' not in action:
                print("Action skipped, type not specified: {}".format(action))
                continue
            a_type = action['type']
            if a_type == 'alert':
                if 'severity' not in action:
                    print("Action skipped, 'severity' key missing from alert.")
                    continue
                elif 'label' not in action:
                    print("Action skipped, 'label' key missing from alert.")
                    continue
                else:
                    actions.append(action)
            elif a_type == 'email':
                if 'address' not in action:
                    print("Action skipped, 'address' key missing from email.")
                    continue
                elif 'subject' not in action:
                    print("Action skipped, 'subject' key missing from email.")
                    continue
                else:
                    actions.append(action)
            elif a_type == 'sms':
                if 'number' not in action:
                    print("Action skipped, 'number' key missing from email.")
                    continue
                elif 'message' not in action:
                    print("Action skipped, 'message' key missing from email.")
                    continue
                else:
                    actions.append(action)
            else:
                print("Action skipped, type not supported: {}".format(action))
        if len(actions) == 0:
            raise ValueError("Rule invalid--no{} actions specified.".format("" if len(yml_actions) == 0 else " valid"))
        return actions

    def load_conditions(self, yml):
        if 'when' not in yml:
            raise ValueError("Rule invalid--no conditions specified")
        when = yml['when']
        return when
