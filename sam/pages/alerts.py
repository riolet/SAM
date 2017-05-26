import re
from datetime import datetime
from sam import errors, common
from sam.pages import base
from sam.models import alerts


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


def encode_status(status, default="unclassified"):
    """
    translate alert status from pretty string to key. default is "Unclassified"
    :param status: 
    :return: 
    """
    if status in ('new', 'unclassified', 'false', 'uncertain',
                  'suspicous', 'verysuspicious', 'confirmed'):
        return status
    return {
        'New': 'new',
        'Unclassified': 'unclassified',
        'False Positive': 'false',
        'Uncertain': 'uncertain',
        'Suspicious': 'suspicious',
        'Very Suspicious': 'verysuspicious',
        'Confirmed Bad': 'confirmed'
    }.get(status, default)


def decode_status(status, default="Unclassified"):
    """
    translate alert status from key to pretty string
    :param status: 
    :return: 
    """
    if status in ('New', 'Unclassified', 'False Positive', 'Uncertain',
                  'Suspicous', 'Very Suspicious', 'Confirmed Bad'):
        return status
    return {
        'new': 'New',
        'unclassified': 'Unclassified',
        'false': 'False Positive',
        'uncertain': 'Uncertain',
        'suspicious': 'Suspicious',
        'verysuspicious': 'Very Suspicious',
        'confirmed': 'Confirmed Bad'
    }.get(status, default)

class Alerts(base.HeadlessPost):
    REGEX = re.compile(r'(\d+)\s?([ywdhms])', re.I)

    def get_description(self, details):
        e_type = details['event_type']
        if e_type == "Compromised Traffic":
            msg = "Connection detected from host {} to a known compromised server.".format(iprange_to_string(details['ipstart'], details['ipend']))
        elif e_type == "Custom Rule":
            msg = "Custom rule matched traffic at {}.".format(iprange_to_string(details['ipstart'], details['ipend']))
        else:
            msg = "Traffic flagged for host {}.".format(iprange_to_string(details['ipstart'], details['ipend']))
        return msg

    # ------------------- GET ---------------------

    def decode_get_request(self, data):
        # queries include: GET latest alerts, GET alert details
        # request must include: 'type'
        # if type is 'alerts', request should include: 'subnet', 'severity', 'time', 'sort', 'sort_dir'
        # if type is 'details', request must include: 'id'
        type = data.get('type', None)
        if type not in ('alerts', 'details'):
            raise errors.RequiredKey("type ('alerts' or 'details')", "type")

        request = {
            'type': type,
        }

        if type == 'alerts':
            request['subnet'] = data.get('subnet', None)

            try:
                request['severity'] = int(data.get('severity', 1))
            except:
                request['severity'] = 1

            request['time'] = time_to_seconds(data.get('time', '1 week'))
            request['sort'] = data.get('sort', 'id')
            request['sort_dir'] = 'ASC' if data.get('sort_dir', 'DESC').upper() == 'ASC' else 'DESC'
        elif type == 'details':
            try:
                request['id'] = int(data.get('id'))
            except:
                raise errors.RequiredKey('alert id', 'id')
        else:
            raise errors.MalformedRequest()
        return request

    def perform_get_command(self, request):
        response = {}
        m_alerts = alerts.Alerts(common.db, self.page.user.viewing)

        if request['type'] == 'alerts':
            alert_filters = alerts.AlertFilter(min_severity=request['severity'], sort=request['sort'], order=request['sort_dir'], age_limit=request['time'])
            if request['subnet'] is None:
                response['alerts'] = m_alerts.get_recent(alert_filters)
            else:
                ipstart, ipend = common.determine_range_string(request['subnet'])
                response['alerts'] = m_alerts.get_by_host(alert_filters, ipstart, ipend)
        if request['type'] == 'details':
            response['for'] = request['id']
            response['details'] = m_alerts.get_details(request['id'])

        return response

    def encode_get_response(self, response):
        encoded = {}
        if self.request['type'] == 'alerts':
            alerts = []
            for alert in response['alerts']:
                alerts.append({
                    'id': str(alert['id']),
                    'host': iprange_to_string(alert['ipstart'], alert['ipend']),
                    'timestamp': datetime.fromtimestamp(alert['timestamp']).strftime('%Y-%m-%d %H:%M:%S'),
                    'severity': "sev{}".format(alert['severity']),
                    'status': decode_status(alert['status']),
                    'type': alert['event_type']
                })
            encoded['alerts'] = alerts
        elif self.request['type'] == 'details':
            details = response['details']

            raw_metadata = details['details']
            metadata = {}
            if isinstance(raw_metadata, (str, unicode)):
                metadata['data'] = raw_metadata
            elif isinstance(raw_metadata, dict):
                metadata.update(raw_metadata)
            elif isinstance(raw_metadata, list):
                for i, value in enumerate(raw_metadata):
                    metadata['Value {}'.format(i+1)] = value
            else:
                metadata['data'] = str(raw_metadata)

            encoded = {
                'for': response['for'],
                'type': response['details']['event_type'],
                'time': datetime.fromtimestamp(details['timestamp']).strftime('%Y-%m-%d %H:%M:%S'),
                'host': iprange_to_string(details['ipstart'], details['ipend']),
                'severity': details['severity'],
                'status': details['status'],
                'description': self.get_description(details),
                'details': metadata
            }
        return encoded

    # ------------------- POST ---------------------

    def decode_post_request(self, data):
        # Queries include updating alert status (and adding notes?)

        method = data.get('method', None)
        if method not in ('update_status'):
            raise errors.RequiredKey("method (must be 'update_status')", "method")

        request = {
            'method': method
        }
        if method == "update_status":
            try:
                request['id'] = int(data.get('id'))
            except:
                raise errors.RequiredKey('alert id', 'id')
            try:
                request['status'] = data.get('status')
            except:
                raise errors.RequiredKey('status', 'status')

        return request

    def perform_post_command(self, request):
        if request['method'] == 'update_status':
            a_model = alerts.Alerts(common.db, self.page.user.viewing)
            a_model.set_status(request['id'], encode_status(request['status']))
        return "success"

    def encode_post_response(self, response):
        encoded = {'result': response}
        return encoded
