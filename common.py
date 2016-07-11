import sys
import web

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
    }
]

# tell renderer where to look for templates
render = web.template.render('templates/')

try:
    sys.dont_write_bytecode = True
    import dbconfig_local as dbconfig
    sys.dont_write_bytecode = False
except Exception as e:
    print e
    import dbconfig

db = web.database(dbn='mysql', user=dbconfig.params['user'], pw=dbconfig.params['passwd'], db=dbconfig.params['db'], port=dbconfig.params['port'])

def IPtoString(ipNumber):
    """
    Converts an IP address from an integer to dotted decimal notation.
    Args:
        ipNumber: an unsigned 32-bit integer representing an IP address

    Returns: The IP address as a dotted-decimal string.

    """
    """Takes a given IP address as a 32 bit integer and
    converts it to dotted decimal notation"""
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
    return (int(a)<<24) + (int(b)<<16) + (int(c)<<8) + int(d)
