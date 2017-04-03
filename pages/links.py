import re
import base
import models.links
import errors


class Links(base.Headless):
    def __init__(self):
        base.Headless.__init__(self)
        self.default_tstart = 1
        self.default_tend = 2**31-1
        self.duration = 1

    def decode_get_request(self, data):
        try:
            addresses = data['address'].split(",")
        except KeyError:
            raise errors.RequiredKey('address', 'address')

        if 'filter' in data:
            try:
                port = data.get('filter')
                if port == '' or port == None:
                    port = None
                else:
                    port = int()
            except:
                raise errors.MalformedRequest('Could not read filter "{}"'.format(data.get('filter')))
        else:
            port = None

        try:
            tstart = int(data.get('tstart', self.default_tstart))
            tend = int(data.get('tend', self.default_tend))
        except ValueError:
            raise errors.MalformedRequest("Could not read time range ('tstart', 'tend')")

        protocol = data.get('protocol', 'ALL')
        if protocol == 'ALL' or protocol == '':
            protocol = None

        if 'ds' in data:
            ds_match = re.search('(\d+)', data['ds'])
            if ds_match:
                ds = int(ds_match.group())
            else:
                raise errors.MalformedRequest("Could not read data source ('ds')")
        else:
            raise errors.RequiredKey('data source', 'ds')

        return {'ds': ds,
                'addresses': addresses,
                'tstart': tstart,
                'tend': tend,
                'port': port,
                'protocol': protocol}

    def perform_get_command(self, request):
        self.require_group('read')
        timerange = (request['tstart'], request['tend'])
        self.duration = int(timerange[1] - timerange[0])
        links = models.links.Links(self.user.viewing, request['ds'])
        return links.get_links(request['addresses'], timerange, request['port'], request['protocol'])

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
