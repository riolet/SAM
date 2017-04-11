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
    BASE_ARIN_URL = 'https://whois.arin.net/rest'
    BASE_RIPE_URL = 'http://rest.db.ripe.net/search.json?query-string='
    BASE_APNIC_URL = 'https://?'
    BASE_AFRINIC_URL = 'https://?'
    BASE_LACNIC = 'https://?'

    def __init__(self, url):
        self.url = url
        self.query = self.url
        if isinstance(self.url, numbers.Integral):
            self.query = IPtoString(self.url)
        else:
            self.query = self.url

    def query_ARIN(self):
        url = '{0}/ip/{1}'.format(Whois.BASE_ARIN_URL, self.query)
        headers = {'Accept': 'application/json'}
        name = ''
        try:
            r = requests.get(url, headers=headers)
            network = r.json()['net']
            if 'orgRef' in network:
                org = network['orgRef']
                if org['@handle'] == 'RIPE':
                    name = 'RIPE'
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
        headers = {'Accept': 'application/json'}
        url = '{0}{1}'.format(Whois.BASE_RIPE_URL, self.query)
        r = requests.get(url, headers=headers)
        results = r.json()['objects']['object']
        inetnum = None
        org = ''
        for i in results:
            if i['type'] == 'inetnum':
                inetnum = i
        if not inetnum:
            return None

        for attr in inetnum['attributes']['attribute']:
            if attr.get('name') == 'descr':
                org = attr['value']
                print('Found name: {}'.format(org))
        return org

    def query_APNIC(self):
        assert False

    def ip_to_org(self):
        org = self.query_ARIN()
        if org == 'RIPE':
            print('retrying on RIPE')
            org = self.query_RIPE()
        elif org == 'APNIC':
            print('retrying on APNIC')
            org = self.query_APNIC()
        elif org == 'AFRINIC':
            print('retrying on AFRINIC')
        elif org == 'LACNIC':
            print('retrying on LACNIC')
        return org


# goal IP: 104.31.70.170

# ips = ['0.0.0.0', '23.49.139.27', '23.60.72.157', '23.60.139.27', '23.203.197.81', '23.239.6.76', '31.13.71.7', '31.13.76.68', '31.13.77.12', '34.193.179.48', '34.194.115.142', '45.33.84.208', '45.79.111.114', '50.18.44.198', '52.35.153.7', '52.84.22.143', '52.84.239.167', '54.70.76.77', '54.174.14.76', '54.230.141.79', '54.231.114.132', '69.89.207.199', '70.42.160.59', '72.21.91.29', '72.21.91.66', '72.167.18.239', '74.125.28.154', '74.125.28.189', '91.189.88.152', '91.189.88.161', '91.189.92.150', '91.189.95.83', '94.31.29.55', '104.16.125.175', '104.20.59.194', '104.20.59.241', '104.25.8.112', '104.25.56.32', '104.31.70.170', '104.80.88.81', '104.113.52.104', '104.113.53.7', '104.118.104.17', '104.125.233.92', '104.131.53.252', '107.20.238.103', '108.61.56.35', '108.168.185.170', '108.177.98.155', '136.147.96.32', '151.101.0.67', '151.101.0.68', '151.101.0.133', '151.101.52.193', '151.101.53.140', '151.101.56.193', '151.101.193.140', '157.240.11.52', '172.217.3.161', '172.217.3.163', '172.217.3.164', '172.217.3.165', '172.217.3.170', '172.217.3.174', '172.217.3.176', '172.217.3.202', '172.217.3.206', '172.217.18.131', '173.194.202.154', '173.194.203.189', '178.255.83.1', '192.168.200.27', '192.168.200.38', '192.168.200.45', '192.168.200.92', '192.168.200.107', '192.168.200.119', '192.168.200.124', '192.168.200.148', '192.168.200.164', '192.168.200.254', '192.168.200.255', '193.0.6.142', '198.232.124.196', '198.232.125.123', '199.5.26.46', '199.59.148.85', '199.71.0.46', '202.12.29.205', '202.12.29.250', '203.119.101.24', '203.119.101.34', '203.133.248.2', '205.251.215.111', '208.81.1.244', '209.68.12.174', '216.6.2.70', '216.58.193.66', '216.58.193.67', '216.58.193.68', '216.58.193.69', '216.58.193.72', '216.58.193.74', '216.58.193.77', '216.58.193.78', '216.58.193.83', '216.58.193.98', '216.58.193.99', '216.58.193.101', '216.58.193.106', '216.58.193.110', '216.58.212.131', '216.58.214.99', '216.58.216.130', '216.58.216.142', '216.58.216.161', '216.58.216.162', '216.58.216.168', '216.229.4.69', '224.0.0.1', '224.0.0.251', '224.0.0.252', '239.255.255.250', '255.255.255.255']
# ips = ips[1:-1]

def run_test(ips):
   for ip in ips:
     w = models.whois.Whois(ip)
     org = w.ip_to_org()
     print("{}: {}".format(ip, org))

# ip = '91.189.88.152'
# url = '{}/ip/{}'.format(models.whois.Whois.BASE_ARIN_URL, ip)
# headers = {'Accept': 'application/json'}
# r = requests.get(url, headers=headers)