import os
import web
import constants


def parse_sql_string(script, replacements):
    # break into lines
    lines = script.splitlines(True)
    # remove comment lines
    lines = [i for i in lines if not i.startswith("--")]
    # join into one long string
    script = " ".join(lines)
    # do any necessary string replacements
    if replacements:
        script = script.format(**replacements)
    # split string into a list of commands
    commands = script.split(";")
    # ignore empty statements (like trailing newlines)
    commands = filter(lambda x: bool(x.strip()), commands)
    return commands


def parse_sql_file(path, replacements):
    with open(path, 'r') as f:
        sql = f.read()
    return parse_sql_string(sql, replacements)


def exec_sql(connection, path, replacements=None):
    if not replacements:
        commands = parse_sql_file(path, {})
    else:
        commands = parse_sql_file(path, replacements)
    for command in commands:
        connection.query(command)


def IPtoString(ip_number):
    # type: (int) -> str
    """
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


def determine_range_string(ip=u"0/0"):
    """
    :type ip: unicode
    :param ip: ip address string in dotted decimal notation with optional trailing subnet mask
    :return: tuple of ip address range start and end as 32-bit unsigned integer
    :rtype: tuple[int, int]
    """
    # type: ( str ) -> (int, int)
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


def get_db(config):
    db = None
    db_quiet = None
    if config['dbn'] == 'mysql':
        db = web.database(**config)
        old = web.config.debug
        web.config.debug = False
        db_quiet = web.database(**config)
        web.config.debug = old
    elif config['dbn'] == 'sqlite':
        config.pop('host', None)
        config.pop('port', None)
        config.pop('user', None)
        config.pop('pw', None)

        db = web.database(**config)
        old = web.config.debug
        web.config.debug = False
        db_quiet = web.database(**config)
        web.config.debug = old
    return db, db_quiet


# tell renderer where to look for templates
render = web.template.render(os.path.join(constants.base_path, 'templates/'))
db, db_quiet = get_db(constants.dbconfig.copy())

# Configure session storage. Session variable is filled in from server.py
web.config.session_parameters['cookie_path'] = "/"
session_store = web.session.DBStore(db_quiet, 'sessions')
session = None
