import numbers
import requests


def IPtoString(ip_number):
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
            self.query = IPtoString(self.url)
        else:
            self.query = self.url
        print('WHOIS: checking "{}"'.format(self.query))

    def query_ARIN(self):
        url = Whois.BASE_ARIN_URL.format(query=self.query)
        headers = {'Accept': 'application/json'}
        name = ''
        try:
            r = requests.get(url, headers=headers)
            network = r.json()['net']
            if 'orgRef' in network:
                org = network['orgRef']
                if org['@handle'] == 'RIPE':
                    name = 'RIPE'
                elif org['@handle'] == 'APNIC':
                    name = 'APNIC'
                else:
                    name = org['@name']
            elif 'customerRef' in network:
                cust = network['customerRef']
                name = cust['@name']
            # return org['@handle']
        except Exception as e:
            print("Error on {}".format(self.query))
            raise e
        return name

    def query_RIPE(self):
        url = Whois.BASE_RIPE_URL.format(query=self.query)
        headers = {'Accept': 'application/json'}
        r = requests.get(url, headers=headers)
        results = r.json()['objects']['object']
        inetnum = None
        organisation = None
        name = ''
        for i in results:
            if i['type'] == 'inetnum':
                inetnum = i
            if i['type'] == 'organisation':
                organisation = i

        if not inetnum and not organisation:
            return None

        if organisation:
            for attr in organisation['attributes']['attribute']:
                if attr.get('name') == 'org-name':
                    name = attr['value']
        elif inetnum:
            for attr in inetnum['attributes']['attribute']:
                if attr.get('name') == 'descr':
                    name = attr['value']
        return name

    def query_APNIC(self):
        url = Whois.BASE_APNIC_URL.format(query=self.query)
        headers = {'Accept': 'application/json'}
        r = requests.get(url, headers=headers)

        # try for an organization
        # try for inetnum
        objects = r.json()
        role = org = inet = None
        name = ''
        for obj in objects:
            if obj['type'] == 'object':
                if obj['objectType'] == 'role':
                    role = obj['attributes']
                if obj['objectType'] == 'organisation':
                    org = obj['attributes']
                if obj['objectType'] == 'inetnum':
                    inet = obj['attributes']
        if org is not None:
            for attr in org:
                if attr['name'] == 'org-name':
                    name = attr['values'][0]
                    break
        #if role is not None and name == '':
        #    for attr in role:
        #        if attr['name'] == 'role':
        #            name = attr['values'][0]
        #            break
        if inet is not None and name == '':
            for attr in inet:
                if attr['name'] == 'netname':
                    name = attr['values'][0]
                if attr['name'] == 'descr':
                    name = attr['values'][0]
                    break
        return name

    def ip_to_org(self):
        org = self.query_ARIN()
        if org == 'RIPE':
            org = self.query_RIPE()
        elif org == 'APNIC':
            org = self.query_APNIC()
        elif org == 'AFRINIC':
            print('retrying on AFRINIC')
        elif org == 'LACNIC':
            print('retrying on LACNIC')
        if org == 'Internet Assigned Numbers Authority':
            org = 'IANA'
        return org
