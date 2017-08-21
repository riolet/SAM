from datetime import datetime
from sam import errors, common
from sam.pages import base
from sam.models.security import anomaly_plugin


class ADPlugin(base.headless_post):
    POST_METHODS = ['accept', 'reject', 'ignore', 'disable', 'enable', 'reset', 'reset_all']

    def __init__(self):
        super(ADPlugin, self).__init__()
        self.AD = anomaly_plugin.ADPlugin(common.db, self.page.user.viewing)

    # ================== GET ===================

    def decode_get_request(self, data):
        # GET requests are for:
        # GET status()  # is STEVE accessible, alive, busy?
        # GET warnings()  # get uncategorized warnings (or all if "all" is sent as true)
        # GET warning()  # get more detailed info on a particular warning
        method = data.get('method', 'status')
        if method not in ('status', 'warnings', 'warning'):
            raise errors.MalformedRequest('Invalid method.')
        request = {
            'method': method
        }
        if method == "warnings":
            request['show_all'] = data.get('all', 'false').lower() == 'true'
        elif method == "warning":
            try:
                request['warning_id'] = int(data['warning_id'])
            except KeyError:
                raise errors.RequiredKey('Warning #', 'warning_id')
            except:
                raise errors.MalformedRequest('unable to read warning_id')
        return request

    def perform_get_command(self, request):
        response = {}
        if request['method'] == 'status':
            response['active'] = self.AD.get_active()
            response['status'] = self.AD.get_status()
            response['stats'] = self.AD.get_stats()
        elif request['method'] == 'warnings':
            wlist = self.AD.get_warnings(show_all=request['show_all'])
            response['warnings'] = wlist
        elif request['method'] == 'warning':
            warning = self.AD.get_warning(request['warning_id'])
            response['warning'] = warning
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
        if 'warning' in response:
            old = response['warning']
            warning = {
                'id': old['id'],
                'host': common.IPtoString(old['host']),
                'log_time': datetime.fromtimestamp(old['log_time']).strftime('%Y-%m-%d %H:%M:%S'),
                'reason': old['reason'],
                'status': old['status'],
                'details': old['details']
            }
            response['warning'] = warning
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

        elif method in ('accept', 'reject', 'ignore'):
            try:
                request['warning_id'] = int(data['warning_id'])
            except:
                raise errors.MalformedRequest('Error parsing {} parameters'.format(method))

        return request

    def perform_post_command(self, request):
        m = request['method']
        if m in 'accept':
            self.AD.accept_warning(request['warning_id'])
        elif m == 'reject':
            self.AD.reject_warning(request['warning_id'])
        elif m == 'ignore':
            self.AD.ignore_warning(request['warning_id'])
        elif m == 'enable':
            self.AD.enable()
        elif m == 'disable':
            self.AD.disable()
        elif m == 'reset':
            host = request['host']
            # self.AD.reset_profile(host)
            raise errors.MalformedRequest('Method not implemented')
        elif m == 'reset_all':
            # self.AD.reset_all_profiles()
            raise errors.MalformedRequest('Method not implemented')
        else:
            raise errors.MalformedRequest('Method could not be handled')

        return "success"

    def encode_post_response(self, response):
        encoded = {'result': response}
        return encoded
