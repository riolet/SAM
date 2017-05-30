import web
import re
from sam import errors, common
from sam.pages import base
from sam.models import rule, rules, rule_template, ruling_process


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
        return rule_data

    def encode_get_response(self, response):
        """
        :param response: The requested rule
         :type response: rule.Rule
        :return: 
        """
        if response is None:
            encoded = {
                'result': 'failure',
                'message': 'Could not retrive rule {}'.format(self.request['id'])
            }
        else:
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
    def decode_params(self, data):
        """
        translates from:
            data = {
                'edits[params][color]': u'blue',
                'edits[params][pattern]': u'src_port > 1024',
                'edits[params][sendmail]': u'true',
            }
        to:
            params = {
                'color': u'blue',
                'pattern': u'src_port > 1024',
                'sendmail': u'true'
            }
        """
        params = {}
        for key in data.keys():
            if not key.startswith("edits[params]"):
                continue
            k = key[14:-1]
            v = data[key]
            params[k] = v
        return params

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

        params = self.decode_params(data)
        if len(params) == 0:
            params = None
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
            'params': params,
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
            if request['params'] is not None:
                edits['params'] = request['params']
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
            ds_match = re.search("(\d+)", data['ds'])
            if ds_match:
                ds = int(ds_match.group())
            else:
                raise errors.MalformedRequest("Could not read data source ('ds')")
        else:
            raise errors.RequiredKey('data source', 'ds')

        try:
            end = int(data['end'])
        except:
            end = 2**31 - 1

        try:
            start = int(data['start'])
        except:
            start = 0

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
        print("PAGE: submitting")
        job_id = ruling_process.submit_job(job)
        print("PAGE: returning")

        return "success", job_id

    def encode_post_response(self, response):
        if isinstance(response, tuple):
            encoded = {
                'result': response[0],
                'job_id': response[1]
            }
        else:
            encoded = {'result': response}
        return encoded
