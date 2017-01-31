import common
import re
import base


class Links(base.Headless):
    def __init__(self):
        base.Headless.__init__(self)
        self.default_tstart = 0
        self.default_tend = 2**31-1
        self.duration = 1

    def decode_get_request(self, data):
        try:
            addresses = data['address'].split(",")
        except KeyError:
            raise base.RequiredKey('address', 'address')

        port = data.get('filter')
        try:
            tstart = int(data.get('tstart', self.default_tstart))
            tend = int(data.get('tend', self.default_tstart))
        except ValueError:
            raise base.MalformedRequest("Could not read time range ('tstart', 'tend')")

        protocol = data.get('protocol', 'ALL')
        if protocol == 'ALL':
            protocol = None

        if 'ds' in data:
            ds_match = re.search("(\d+)", data['ds'])
            if ds_match:
                ds = int(ds_match.group())
            else:
                raise base.MalformedRequest("Could not read data source ('ds')")
        else:
            raise base.RequiredKey('data source', 'ds')

        return {'ds': ds,
                'addresses': addresses,
                'tstart': tstart,
                'tend': tend,
                'port': port,
                'protocol': protocol}

    def perform_get_command(self, request):
        timerange = (request['tstart'], request['tend'])
        self.duration = int(timerange[1] - timerange[0])
        return common.links.get_links(request['ds'], request['addresses'], timerange, request['port'], request['protocol'])

    def encode_get_response(self, response):
        seconds = self.duration
        minutes = seconds // 60

        # remove duplicate protocol names, normalize values over time
        for address in response.iterkeys():
            for row in response[address]['inputs']:
                row['protocols'] = ",".join(set(row['protocols'].split(',')))
                row['links'] /= minutes
                row['bytes'] /= seconds
                row['packets'] /= seconds

            for row in response[address]['outputs']:
                row['protocols'] = ",".join(set(row['protocols'].split(',')))
                row['links'] /= minutes
                row['bytes'] /= seconds
                row['packets'] /= seconds
        return response
