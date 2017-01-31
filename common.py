import sys
import os
import web
base_path = os.path.dirname(__file__)

from models.links import Links
from models.nodes import Nodes
from models.ports import Ports
from models.settings import Settings
from models.datasources import Datasources



def IPtoString(ipNumber):
    # type: (int) -> str
    """
    Converts an IP address from an integer to dotted decimal notation.
    Args:
        ipNumber: an unsigned 32-bit integer representing an IP address

    Returns: The IP address as a dotted-decimal string.

    """
    return "{0}.{1}.{2}.{3}".format(
        (ipNumber & 0xFF000000) >> 24,
        (ipNumber & 0xFF0000) >> 16,
        (ipNumber & 0xFF00) >> 8,
        ipNumber & 0xFF)


def IPtoInt(a, b, c, d):
    """
    Converts a number from a sequence of dotted decimals into a single unsigned int.
    Args:
        a: IP address segment 1 ###.0.0.0
        b: IP address segment 2 0.###.0.0
        c: IP address segment 3 0.0.###.0
        d: IP address segment 4 0.0.0.###

    Returns: The IP address as a simple 32-bit unsigned integer

    """
    return (int(a) << 24) + (int(b) << 16) + (int(c) << 8) + int(d)


def IPStringtoInt(ip):
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


def determine_range(ip8=-1, ip16=-1, ip24=-1, ip32=-1):
    low = 0x00000000
    high = 0xFFFFFFFF
    quot = 1
    if 0 <= ip8 <= 255:
        low = (ip8 << 24)  # 172.0.0.0
        if 0 <= ip16 <= 255:
            low |= (ip16 << 16)  # 172.19.0.0
            if 0 <= ip24 <= 255:
                low |= (ip24 << 8)
                if 0 <= ip32 <= 255:
                    low |= ip32
                    high = low
                else:
                    high = low | 0xFF
                    quot = 0x1
            else:
                high = low | 0xFFFF
                quot = 0x100
        else:
            high = low | 0xFFFFFF
            quot = 0x10000
    else:
        quot = 0x1000000
    return low, high, quot


def determine_range_string(ip="0/0"):
    parts = ip.split("/")
    address = IPStringtoInt(parts[0])
    if len(parts) == 2:
        subnet = int(parts[1])
    else:
        subnet = min(parts[0].count("."), 3) * 8 + 8
    mask = ((1 << 32) - 1) ^ ((1 << (32 - subnet)) - 1)
    low = address & mask
    high = address | (0xffffffff ^ mask)
    return low, high


navbar = [
    {
        "name": "Map",
        "icon": "sitemap",
        "link": "/map"
    },
    {
        "name": "Stats",
        "icon": "filter",
        "link": "/stats"
    },
    {
        "name": "Table View",
        "icon": "table",
        "link": "/table"
    },
    {
        "name": "Host Details",
        "icon": "tasks",
        "link": "/metadata"
    },
    {
        "name": "Settings",
        "icon": "settings",
        "link": "/settings"
    }
]

# tell renderer where to look for templates
render = web.template.render(os.path.join(base_path, 'templates/'))

try:
    sys.dont_write_bytecode = True
    import dbconfig_local as dbconfig
except Exception as e:
    print e
    import dbconfig
finally:
    sys.dont_write_bytecode = False

db = web.database(**dbconfig.params)
old = web.config.debug
web.config.debug = False
db_quiet = web.database(**dbconfig.params)
web.config.debug = old
del old

links = Links()
nodes = Nodes()
ports = Ports()
settings = Settings()
datasources = Datasources()