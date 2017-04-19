import numbers
import requests


def ip_itos(ip_number):
    """
    :type ip_number: numbers.Integral
    :rtype: str
    Converts an IP address from an integer to dotted decimal notation.
    Args:
        ip_number: an unsigned 32-bit integer representing an IP address

    Returns: The IP address as a dotted-decimal string.

    """
    return "{0}.{1}.{2}.{3}".format(
        (ip_number & 0xFF000000) >> 24,
        (ip_number & 0xFF0000) >> 16,
        (ip_number & 0xFF00) >> 8,
        ip_number & 0xFF)

def ip_stoi(ip):
    """
    Converts a number from a dotted decimal string into a single unsigned int.
    Args:
        ip: dotted decimal ip address, like 12.34.56.78

    Returns: The IP address as a simple 32-bit unsigned integer

    """
    address_mask = ip.split("/")
    parts = address_mask[0].split(".")
    ip_int = 0
    for i in range(4):
        ip_int <<= 8
        if len(parts) > i:
            ip_int += int(parts[i])
    return ip_int


class WrongAuthorityError(Exception):
    def __init__(self, auth):
        self.authority = auth


class Whois(object):
    """
    Translates IP addresses to names
    Implementation of a small subset of this: https://www.arin.net/resources/whoisrws/whois_api.html
    """
    BASE_ARIN_URL = 'https://whois.arin.net/rest/ip/{query}'
    BASE_RIPE_URL = 'http://rest.db.ripe.net/search.json?query-string={query}'
    BASE_APNIC_URL = 'https://wq.apnic.net/whois-search/query?searchtext={query}'
    BASE_AFRINIC_URL = 'https://?'
    BASE_LACNIC = 'https://?'

    def __init__(self, url):
        self.url = url
        self.query = self.url
        if isinstance(self.url, numbers.Integral):
            self.query = ip_itos(self.url)
        else:
            self.query = self.url

        self.downloaded = False
        self.info = None
        self.source = 'ARIN'
        self.name = ''
        self.netname = ''
        self.netstart = url
        self.netend = url
        self.netlength = 32

    def decode_inetnum(self, inetnum):
        try:
            start, end = inetnum.split("-")
            self.netstart = ip_stoi(start)
            self.netend = ip_stoi(end)
            self.netlength = 32 - (self.netend - self.netstart).bit_length()
        except:
            print('Whois decode error: could not split "{}"'.format(inetnum))

    def query_ARIN(self):
        url = Whois.BASE_ARIN_URL.format(query=self.query)
        headers = {'Accept': 'application/json'}
        info = None

        r = requests.get(url, headers=headers)
        network = r.json()['net']
        if 'orgRef' in network:
            org = network['orgRef']
            if org['@handle'] == 'RIPE':
                raise WrongAuthorityError('RIPE')
            elif org['@handle'] == 'APNIC':
                raise WrongAuthorityError('APNIC')

        return network

    def query_RIPE(self):
        url = Whois.BASE_RIPE_URL.format(query=self.query)
        headers = {'Accept': 'application/json'}
        r = requests.get(url, headers=headers)
        results = r.json()['objects']['object']
        return results

    def query_APNIC(self):
        url = Whois.BASE_APNIC_URL.format(query=self.query)
        headers = {'Accept': 'application/json'}
        r = requests.get(url, headers=headers)

        objects = r.json()
        return objects

    def decode_ARIN(self):
        if 'orgRef' in self.info:
            org = self.info['orgRef']
            self.name = org['@name']
        if self.name == '' and 'customerRef' in self.info:
            cust = self.info['customerRef']
            self.name = cust['@name']
        if 'name' in self.info:
            self.netname = self.info['name']['$']
            self.netstart = ip_stoi(self.info['startAddress']['$'])
            self.netend = ip_stoi(self.info['endAddress']['$'])
            self.netlength = 32 - (self.netend - self.netstart).bit_length()

    def decode_RIPE(self):
        inetnum = None
        organisation = None
        name = ''
        for i in self.info:
            if i['type'] == 'inetnum':
                inetnum = i
            if i['type'] == 'organisation':
                organisation = i

        if not inetnum and not organisation:
            return

        if organisation:
            for attr in organisation['attributes']['attribute']:
                if attr.get('name') == 'org-name':
                    self.name = attr['value']
        if inetnum:
            for attr in inetnum['attributes']['attribute']:
                attrname = attr.get('name')
                if attrname == 'descr' and self.name == '':
                    self.name = attr['value']
                if attrname == 'inetnum':
                    self.decode_inetnum(attr['value'])
                if attrname == 'netname':
                    self.netname = attr['value']

    def decode_APNIC(self):
        org = inet = None
        for obj in self.info:
            if obj['type'] == 'object':
                if obj['objectType'] == 'organisation':
                    org = obj['attributes']
                if obj['objectType'] == 'inetnum':
                    inet = obj['attributes']
        if org is not None:
            for attr in org:
                if attr['name'] == 'org-name':
                    self.name = attr['values'][0]
                    break
        if inet is not None:
            for attr in inet:
                if attr['name'] == 'netname':
                    self.netname = attr['values'][0]
                if attr['name'] == 'descr':
                    if self.name == '':
                        self.name = attr['values'][0]
                if attr['name'] == 'inetnum':
                    self.decode_inetnum(attr['values'][0])
        if self.name == '':
            self.name = self.netname

    def retrieve_info(self):
        try:
            self.info = self.query_ARIN()
        except WrongAuthorityError as e:
            if e.authority == 'RIPE':
                try:
                    self.source = 'RIPE'
                    self.info = self.query_RIPE()
                except:
                    pass
            elif e.authority == 'APNIC':
                try:
                    self.source = 'APNIC'
                    self.info = self.query_APNIC()
                except:
                    pass
        except:
            pass

        if self.source == 'ARIN':
            self.decode_ARIN()
        elif self.source == 'RIPE':
            self.decode_RIPE()
        elif self.source == 'APNIC':
            self.decode_APNIC()
        self.downloaded = True

    def get_name(self):
        if self.downloaded == False:
            self.retrieve_info()

        if self.name == 'Internet Assigned Numbers Authority':
            self.name = 'IANA'
        return self.name

    def get_network(self):
        if self.downloaded == False:
            self.retrieve_info()
        return self.netname, self.netstart, self.netend, self.netlength
