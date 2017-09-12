from datetime import datetime
import re
import web
from sam import errors, common
from sam.pages import base
from sam.models.security import rule, rules, rule_template, ruling_process


class Rules(base.Headless):
    """
    For getting the list of rules
    """
    def decode_get_request(self, data):
        # no options with this request
        return None

    def perform_get_command(self, request):
        r_model = rules.Rules(common.db, self.page.user.viewing)
        response = r_model.get_all_rules()
        return response

    def encode_get_response(self, response):
        encoded = {}
        all_rules = []
        for rule in response:
            all_rules.append({
                'id': rule.id,
                'name': rule.get_name(),
                'desc': rule.get_desc(),
                'template': rule.get_def_name(),
                'type': rule.get_type(),
                'active': rule.is_active()
            })
        encoded['all'] = all_rules
        return encoded


class RulesNew(base.HeadlessPost):
    # ----------- GET ------------
    def decode_get_request(self, data):
        # no options for this request
        return None

    def perform_get_command(self, request):
        response = rule_template.get_all()
        return response

    def encode_get_response(self, response):
        encoded = {
            'templates': response
        }
        return encoded

    # ----------- POST ------------
    def decode_post_request(self, data):
        if "name" not in data:
            raise errors.RequiredKey("name", "name")
        name = data['name']
        name = name.strip()
        if len(name) == 0:
            raise errors.RequiredKey("name", "name")

        if "desc" not in data:
            raise errors.RequiredKey("Description", "desc")
        desc = data['desc']
        desc = desc.strip()
        if len(desc) == 0:
            raise errors.RequiredKey("Description", "desc")

        if "template" not in data:
            raise errors.RequiredKey("Template", "template")
        template = data['template']
        template = template.strip()
        if len(template) == 0:
            raise errors.RequiredKey("Template", "template")

        request = {
            'name': name,
            'desc': desc,
            'template': template
        }
        return request

    def perform_post_command(self, request):
        r_model = rules.Rules(common.db, self.page.user.viewing)
        r_model.add_rule(path=request['template'], name=request['name'], description=request['desc'], params={})
        return "success"

    def encode_post_response(self, response):
        encoded = {'result': response}
        return encoded


class RulesEdit(base.HeadlessPost):
    METHODS = 'edit', 'delete'
    """
    For editing the details/customization of a rule.
    """

    # ----------- GET ------------
    def decode_get_request(self, data):
        try:
            rule_id = int(data['id'])
        except KeyError:
            raise errors.RequiredKey('Rule id', 'id')
        except:
            raise errors.MalformedRequest()

        request = {
            'id': rule_id
        }
        return request

    def perform_get_command(self, request):
        r_model = rules.Rules(common.db, self.page.user.viewing)
        rule_data = r_model.get_rule(request['id'])
        if rule_data is None:
            raise errors.MalformedRequest("Invalid rule id")
        return rule_data

    def encode_get_response(self, response):
        """
        :param response: The requested rule
         :type response: rule.Rule
        :return: 
        """
        # Cannot transmit compiled regex expressions to client. They must be recompiled on the javascript side.
        exposed_params = response.get_exposed_params()
        for exposed_param in exposed_params.itervalues():
            exposed_param.pop('regex_compiled', None)

        encoded = {
            'id': response.id,
            'name': response.get_name(),
            'desc': response.get_desc(),
            'type': response.get_type(),
            'active': response.is_active(),
            'exposed': exposed_params,
            'actions': response.get_action_params()
        }
        return encoded

    # ----------- POST ------------
    def decode_exposed(self, data):
        """
        translates from:
            data = {
                'edits[exposed][color]': u'blue',
                'edits[exposed][pattern]': u'src_port > 1024',
                'edits[exposed][sendmail]': u'true',
            }
        to:
            exposed = {
                'color': u'blue',
                'pattern': u'src_port > 1024',
                'sendmail': u'true'
            }
        """
        exposed = {}
        token_string = 'edits[exposed]'
        for key in data.keys():
            if not key.startswith(token_string):
                continue
            k = key[len(token_string) + 1:-1]
            v = data[key]
            exposed[k] = v
        return exposed

    def decode_actions(self, data):
        """
        translates from:
            data = {
                'edits[actions][color]': u'blue',
                'edits[actions][pattern]': u'src_port > 1024',
                'edits[actions][sendmail]': u'true',
            }
        to:
            actions = {
                'color': u'blue',
                'pattern': u'src_port > 1024',
                'sendmail': u'true'
            }
        """
        actions = {}
        token_string = "edits[actions]"
        for key in data.keys():
            if not key.startswith(token_string):
                continue
            k = key[len(token_string) + 1:-1]
            v = data[key]
            actions[k] = v
        return actions

    def decode_post_request(self, data):
        try:
            rule_id = int(data['id'])
        except KeyError:
            raise errors.RequiredKey('Rule id', 'id')
        except:
            raise errors.MalformedRequest()

        method = data.get('method', None)
        if method is None:
            raise errors.RequiredKey('Method', 'method')
        elif method not in RulesEdit.METHODS:
            raise errors.MalformedRequest()

        actions = self.decode_actions(data)
        exposed = self.decode_exposed(data)
        if len(exposed) == 0:
            exposed = None
        if len(actions) == 0:
            actions = None
        desc = data.get('edits[desc]', None)
        name = data.get('edits[name]', None)
        active = data.get('edits[active]', None)
        if active is not None:
            active = active.lower() == 'true'

        request = {
            'id': rule_id,
            'method': method,
            'active': active,
            'name': name,
            'desc': desc,
            'actions': actions,
            'exposed': exposed,
        }
        return request

    def perform_post_command(self, request):
        r_model = rules.Rules(common.db, self.page.user.viewing)
        if request['method'] == 'delete':
            r_model.delete_rule(request['id'])
        elif request['method'] == 'edit':
            id = request['id']
            edits = {}
            if request['active'] is not None:
                edits['active'] = request['active']
            if request['name'] is not None:
                edits['name'] = request['name']
            if request['desc'] is not None:
                edits['description'] = request['desc']
            if request['actions'] is not None:
                edits['actions'] = request['actions']
            if request['exposed'] is not None:
                edits['exposed'] = request['exposed']
            r_model.edit_rule(id, edits)
        return "success"

    def encode_post_response(self, response):
        encoded = {'result': response}
        return encoded


class RulesApply(base.HeadlessPost):
    def GET(self):
        return None

    def decode_post_request(self, data):
        if "ds" in data:
            try:
                ds = int(data['ds'])
            except:
                ds_match = re.search("(\d+)", data['ds'])
                if ds_match:
                    ds = int(ds_match.group())
                else:
                    raise errors.MalformedRequest("Could not read data source ('ds')")
        else:
            raise errors.RequiredKey('data source', 'ds')

        try:
            end = datetime.fromtimestamp(int(data['end']))
        except:
            end = datetime.fromtimestamp(2**31 - 1)

        try:
            start = datetime.fromtimestamp(int(data['start']))
        except:
            start = datetime.fromtimestamp(1)

        request = {
            'ds': ds,
            'start': start,
            'end': end
        }

        return request

    def perform_post_command(self, request):
        # request has ds, start, end
        # start a separate process (if it isn't running) and add a job (sub, ds, start, end, ruleset)
        r_model = rules.Rules(common.db, self.page.user.viewing)
        ruleset = r_model.get_ruleset()
        job = ruling_process.RuleJob(self.page.user.viewing, request['ds'], request['start'], request['end'], ruleset)
        job_id = ruling_process.submit_job(job)

        return "success", job_id

    def encode_post_response(self, response):
        if isinstance(response, tuple):
            encoded = {
                'result': response[0]
            }
            if len(response) == 2:
                encoded['job_id'] = response[1]
        else:
            encoded = {'result': response}
        return encoded
