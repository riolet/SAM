import math
import re
from datetime import datetime
from sam import errors, common
from sam.pages import base
from sam.models.security import alerts


def time_to_seconds(tstring):
    matches = Alerts.REGEX.findall(tstring)
    timespan = 0
    for quantity, period in matches:
        if period == 'y':
            factor = 31556926
        elif period == 'w':
            factor = 604800
        elif period == 'd':
            factor = 86400
        elif period == 'h':
            factor = 3600
        elif period == 'm':
            factor = 60
        else:
            factor = 1
        timespan += int(quantity) * factor
    return timespan


def iprange_to_string(ipstart, ipend):
    ip = common.IPtoString(ipstart)
    if ipend == ipstart:
        return ip
    else:
        subnet = 32 - (ipend - ipstart).bit_length()
        return "{}/{}".format(ip, subnet)


def fuzzy_time(seconds):
    if seconds < 120:
        return "{:.0f} seconds".format(seconds)
    seconds /= 60.0
    if seconds < 10:
        return "{:.1f} minutes".format(seconds)
    if seconds < 120:
        return "{:.0f} minutes".format(seconds)
    seconds /= 60.0
    if seconds < 12:
        return "{:.1f} hours".format(seconds)
    if seconds < 48:
        return "{:.0f} hours".format(seconds)
    seconds /= 24.0
    if seconds < 5:
        return "{:.0f} days".format(seconds)
    if seconds < 14:
        return "{:.0f} days".format(seconds)
    seconds /= 7.0
    if seconds < 10:
        return "{:.1f} weeks".format(seconds)
    if seconds < 106:
        return "{:.0f} weeks".format(seconds)
    seconds /= 52.177457
    if seconds < 10:
        return "{:.1f} years".format(seconds)
    return "{:.0f} years".format(seconds)


class Alerts(base.headless_post):
    REGEX = re.compile(r'(\d+)\s*([ywdhms])', re.I)

    # ------------------- GET ---------------------

    def decode_get_request(self, data):
        # request should (but doesn't need to) include: 'subnet', 'severity', 'time', 'sort', 'sort_dir', 'page_size', 'page_num'
        subnet = data.get('subnet', None)


        try:
            severity = int(data.get('severity', 1))
        except:
            severity = 1

        time = time_to_seconds(data.get('time', '1 week'))
        sort = data.get('sort', 'id')
        sort_dir = 'ASC' if data.get('sort_dir', 'DESC').upper() == 'ASC' else 'DESC'

        try:
            page_size = int(data['page_size'])
        except:
            page_size = 50

        try:
            page_num = int(data['page_num'])
        except:
            page_num = 1

        request = {
            'subnet': subnet,
            'severity': severity,
            'time': time,
            'sort': sort,
            'sort_dir': sort_dir,
            'page_size': page_size,
            'page_num': page_num
        }

        return request

    def perform_get_command(self, request):
        response = {}
        m_alerts = alerts.Alerts(common.db, self.page.user.viewing)

        page_offset = (request['page_num'] - 1) * request['page_size']

        alert_filters = alerts.AlertFilter(min_severity=request['severity'], sort=request['sort'], order=request['sort_dir'], age_limit=request['time'], limit=request['page_size'], offset=page_offset)
        if request['subnet'] is None:
            response['alerts'] = m_alerts.get(alert_filters)
        else:
            ipstart, ipend = common.determine_range_string(request['subnet'])
            response['alerts'] = m_alerts.get_by_host(alert_filters, ipstart, ipend)

        total_alerts = m_alerts.count()
        response['results'] = total_alerts
        response['page'] = request['page_num']
        response['pages'] = int(math.ceil(float(total_alerts) / request['page_size']))

        return response

    def encode_get_response(self, response):
        encoded = {}

        alert_list = []
        for alert in response['alerts']:
            alert_list.append({
                'id': str(alert['id']),
                'host': iprange_to_string(alert['ipstart'], alert['ipend']),
                'log_time': datetime.fromtimestamp(alert['log_time']).strftime('%Y-%m-%d %H:%M:%S'),
                'report_time': datetime.fromtimestamp(alert['report_time']).strftime('%Y-%m-%d %H:%M:%S'),
                'severity': "sev{}".format(alert['severity']),
                'label': alert['label'],
                'rule_name': alert['rule_name']
            })
        encoded['alerts'] = alert_list
        encoded['results'] = response['results']
        encoded['page'] = response['page']
        encoded['pages'] = response['pages']

        return encoded

    # ------------------- POST ---------------------

    def decode_post_request(self, data):
        method = data.get('method', None)
        if method not in ('delete_all', 'delete'):
            raise errors.MalformedRequest("method must be either 'delete' or 'delete_all'")

        alert_id = None

        if method == 'delete':
            try:
                alert_id = int(data.get('id'))
            except:
                raise errors.RequiredKey('alert id', 'id')

        request = {
            'method': method,
            'id': alert_id
        }
        return request

    def perform_post_command(self, request):
        m_alerts = alerts.Alerts(common.db, self.page.user.viewing)

        if request['method'] == 'delete_all':
            m_alerts.clear()
        elif request['method'] == 'delete':
            m_alerts.delete(request['id'])
        else:
            raise errors.MalformedRequest('Method not understood.')

        return "success"

    def encode_post_response(self, response):
        encoded = {'result': response}
        return encoded



class AlertDetails(base.headless_post):

    # ------------------- GET ---------------------

    def decode_get_request(self, data):
        try:
            request = {'id': int(data.get('id'))}
        except:
            raise errors.RequiredKey('alert id', 'id')
        return request

    def perform_get_command(self, request):
        response = {}
        m_alerts = alerts.Alerts(common.db, self.page.user.viewing)

        response['for'] = request['id']
        response['details'] = m_alerts.get_details(request['id'])

        return response

    def encode_get_response(self, response):
        details = response['details']
        raw_metadata = details['details']
        metadata = {}
        if isinstance(raw_metadata, (str, unicode)):
            metadata['data'] = raw_metadata
        elif isinstance(raw_metadata, dict):
            metadata.update(raw_metadata)
        elif isinstance(raw_metadata, list):
            for i, value in enumerate(raw_metadata):
                metadata['Value {}'.format(i + 1)] = value
        else:
            metadata['data'] = str(raw_metadata)


        # prettify some values
        if 'timestamp' in metadata:
            metadata['timestamp'] = metadata['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
        if 'src' in metadata:
            metadata['src'] = common.IPtoString(metadata['src'])
        if 'dst' in metadata:
            metadata['dst'] = common.IPtoString(metadata['dst'])
        if 'duration' in metadata:
            metadata['duration'] = fuzzy_time(metadata['duration'])


        host = iprange_to_string(details['ipstart'], details['ipend'])
        encoded = {
            'for': response['for'],
            'time': datetime.fromtimestamp(details['report_time']).strftime('%Y-%m-%d %H:%M:%S'),
            'host': host,
            'severity': details['severity'],
            'label': details['label'],
            'rule_name': details['rule_name'],
            'details': metadata,
            'description': 'Rule "{}" triggered on {}'.format(details['rule_name'], host)
        }
        return encoded

    # ------------------- POST ---------------------

    def decode_post_request(self, data):
        # Queries include updating alert label (and adding notes?)

        method = data.get('method', None)
        if method != 'update_label':
            raise errors.RequiredKey("method (must be 'update_label')", "method")

        request = {
            'method': method
        }
        if method == "update_status":
            try:
                request['id'] = int(data.get('id'))
            except:
                raise errors.RequiredKey('alert id', 'id')
            try:
                request['label'] = data.get('label')
            except:
                raise errors.RequiredKey('label', 'label')

        return request

    def perform_post_command(self, request):
        if request['method'] == 'update_status':
            a_model = alerts.Alerts(common.db, self.page.user.viewing)
            a_model.set_label(request['id'], request['label'])
        return "success"

    def encode_post_response(self, response):
        encoded = {'result': response}
        return encoded
