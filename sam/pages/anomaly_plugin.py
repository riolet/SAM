from datetime import datetime
from sam import errors, common
from sam.pages import base
from sam.models.security import anomaly_plugin


class ADPlugin(base.headless_post):
    POST_METHODS = ['accept', 'reject', 'ignore', 'disable', 'enable', 'reset', 'reset_all', 'submit_traffic']

    def __init__(self):
        super(ADPlugin, self).__init__()
        self.SP = anomaly_plugin.ADPlugin(common.db, self.page.user.viewing)

    # ================== GET ===================

    def decode_get_request(self, data):
        # GET requests are for:
        # GET status()  # is STEVE accessible, alive, busy?
        # GET warnings(last_id)  # get all warnings where id >= last_id
        method = data.get('method', 'status')
        if method not in ('status', 'warnings'):
            raise errors.MalformedRequest('Invalid method.')
        request = {
            'method': method
        }
        if method == "warnings":
            request['show_all'] = data.get('all', 'false').lower() == 'true'
        return request

    def perform_get_command(self, request):
        response = {}
        if request['method'] == 'status':
            response['active'] = self.SP.get_active()
            response['status'] = self.SP.get_status()
            response['stats'] = self.SP.get_stats()
        elif request['method'] == 'warnings':
            wlist = self.SP.get_warnings(show_all=request['show_all'])
            response['warnings'] = wlist
        else:
            raise errors.MalformedRequest('Method could not be handled')
        return response

    def encode_get_response(self, response):
        if 'warnings' in response:
            warnings = []
            for warning in response['warnings']:
                warnings.append({
                    'id': warning['id'],
                    'host': common.IPtoString(warning['host']),
                    'log_time': datetime.fromtimestamp(warning['log_time']).strftime('%Y-%m-%d %H:%M:%S'),
                    'reason': warning['reason'],
                    'status': warning['status']
                })
            response['warnings'] = warnings
        return response

    # ================== POST ===================

    def decode_post_request(self, data):
        # Post requests are for:
        # POST accept/reject(warning_id)  # so that STEVE can learn
        # POST enable/disable  # to turn the feature on and off
        # POST reset(host=None)  # to delete profile data for a specific host
        # POST reset_all

        method = data.get('method')
        if not method:
            raise errors.RequiredKey('method to perform', 'method')
        if method not in ADPlugin.POST_METHODS:
            raise errors.MalformedRequest('invalid method.')

        request = {
            'method': method
        }

        if method == 'reset':
            try:
                request['host'] = data['host']
            except:
                raise errors.MalformedRequest('Error parsing {} parameters'.format(method))

        elif method == 'submit_traffic':
            try:
                request['_known'] = data['_known'].lower() == 'true'
                request['_good'] = data['_good'].lower() == 'true'
                request['traffic'] = data['traffic']
            except:
                raise errors.MalformedRequest('Error parsing {} parameters'.format(method))

        elif method in ('accept', 'reject', 'ignore'):
            try:
                request['warning_id'] = int(data['warning_id'])
            except:
                raise errors.MalformedRequest('Error parsing {} parameters'.format(method))

        return request

    def perform_post_command(self, request):
        m = request['method']
        if m in 'accept':
            self.SP.accept_warning(request['warning_id'])
        elif m == 'reject':
            self.SP.reject_warning(request['warning_id'])
        elif m == 'ignore':
            self.SP.ignore_warning(request['warning_id'])
        elif m == 'enable':
            self.SP.enable()
        elif m == 'disable':
            self.SP.disable()
        elif m == 'reset':
            host = request['host']
            self.SP.reset_profile(host)
        elif m == 'reset_all':
            self.SP.reset_all_profiles()
        else:
            raise errors.MalformedRequest('Method could not be handled')

        return "success"

    def encode_post_response(self, response):
        encoded = {'result': response}
        return encoded
