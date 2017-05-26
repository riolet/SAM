import os
import traceback
import re
import yaml
from sam import constants

BASE_PATH = os.path.dirname(__file__)
TEMPLATES_FOLDER = 'rule_templates'
RULE_PATH = os.path.join(BASE_PATH, os.path.pardir, TEMPLATES_FOLDER)

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
    return filter(lambda f: f.endswith(".yml"), os.listdir(RULE_PATH))


def abs_rule_path(path):
    if path[0:7] == "plugin:":
        abspath = os.path.join(constants.plugins['root'], path[7:])
        if not os.path.exists(abspath):
            print('security.models.definition: WARNING: absolute rule path not found.')
            print('  (Checked "{}"->"{}")'.format(path, abspath))
            return None
    else:
        abspath = os.path.join(RULE_PATH, "{}".format(path))
        if not os.path.exists(abspath):
            print('Cannot find definition path.')
            print('  (Checked "{}"->"{}")'.format(path, abspath))
            return None
    return abspath


def get_definition(path, flyweight={}):
    if path in flyweight:
        return flyweight[path]
    else:
        try:
            with open(path, 'r') as f:
                data = yaml.load(f)
            rule_def = RuleTemplate(os.path.dirname(path), data)
        except:
            # print errors, but move on.
            traceback.print_exc()
            return None
        flyweight[path] = rule_def
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
        if 'type' in data:
            self.type = data['type']
        if 'name' in data:
            self.name = data['name']

        self.load_exposed()
        self.load_inclusions()
        self.load_actions()
        self.load_conditions()

    def load_exposed(self):
        if 'expose' not in self.yml:
            return
        exposed = self.yml['expose']
        for key, param in exposed.iteritems():
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

            self.exposed[key] = exposed_param

    def load_inclusions(self):
        if not self.yml.get('include', None):
            return
        for ref in self.yml['include'].keys():
            path = os.path.join(self.cwd, self.yml['include'][ref])
            try:
                with open(path, 'r') as f:
                    data = f.read()
                self.inclusions[ref] = data.splitlines()
            except Exception as e:
                print("Failed to load inclusion {}: {}".format(ref, str(e)))

    def load_actions(self):
        actions = self.yml.get('actions', [])
        for action in actions:
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
                    self.actions.append(action)
            elif a_type == 'email':
                print("Email actions not supported yet.")
                continue
            else:
                print("Action skipped, type not supported: {}".format(action))
        if len(self.actions) == 0:
            raise ValueError("Rule invalid--no{} actions specified.".format("" if len(actions) == 0 else " valid"))

    def load_conditions(self):
        if 'when' not in self.yml:
            raise ValueError("Rule invalid--no conditions specified")
        self.when = self.yml['when']
