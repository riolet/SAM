import os
import sys
import importlib
import logging
import web
import smtplib
from sam import constants
logger = logging.getLogger(__name__)


def load_plugins():
    newly_loaded = []
    plugin_path = os.path.abspath(constants.plugins['root'])
    if not os.path.isdir(plugin_path):
        return newly_loaded
    sys.path.append(plugin_path)

    plugin_names = constants.plugins['enabled']
    loaded = constants.plugins['loaded']
    if plugin_names == ['ALL']:
        plugin_names = os.listdir(plugin_path)
        plugin_names = filter(lambda x: os.path.isdir(os.path.join(plugin_path, x)), plugin_names)
    for plugin in plugin_names:
        # don't install plugins multiple times. They may not be idempotent.
        if plugin in loaded:
            continue
        try:
            mod = importlib.import_module(plugin)
            mod.sam_installer.install()
            loaded.append(plugin)
            newly_loaded.append(plugin)
        except:
            logger.error("Failed to load {}".format(plugin))
            raise

    constants.plugins['loaded'] = loaded
    # Globals in sam.common get initialized based on data in constants.
    # Plugins change the initialization data, prompting this re-init:

    init_globals()
    return newly_loaded


def init_globals():
    # This function reinitializes the globals that common.py provides.
    # it is needed if the configuration changes after this module has been loaded. (i.e. a plugin loads.)
    global renderer
    global session_store
    global db
    global db_quiet

    renderer = MultiRender('templates/')
    for extra in constants.plugin_templates:
        renderer.install_plugin_template_path(extra)

    web.config.debug = constants.debug
    web.config._session = None  # erase any erroneous session creation.
    web.config.session_parameters['cookie_path'] = "/"
    web.config.smtp_server = constants.smtp['server']
    web.config.smtp_port = int(constants.smtp.get('port', '587'))
    web.config.smtp_username = constants.smtp['username']
    web.config.smtp_password = constants.smtp['password']
    web.config.smtp_starttls = constants.smtp['starttls'].lower() == 'true'

    db, db_quiet = get_db(constants.dbconfig.copy())

    session_store = web.session.DBStore(db_quiet, 'sessions')
    constants.init_urls()


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
            try:
                ip_int += int(parts[i])
            except:
                pass
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


def get_domain(path):
    domain = path
    prefix = domain.find("//")
    if prefix != -1:
        domain = domain[prefix + 2:]
    prefix = domain.find('@')
    if prefix != -1:
        domain = domain[prefix + 1:]
    suffix = domain.find(":")
    if suffix != -1:
        domain = domain[:suffix]
    suffix = domain.find("/")
    if suffix != -1:
        domain = domain[:suffix]
    return domain


def sqlite_udf(db):
    db._db_cursor().connection.create_function("decodeIP", 1,
                                               lambda ip: "{}.{}.{}.{}".format(ip >> 24,
                                                                               ip >> 16 & 0xff,
                                                                               ip >> 8 & 0xff,
                                                                               ip & 0xff))
    db._db_cursor().connection.create_function("encodeIP", 4,
                                               lambda a, b, c, d: a << 24 | b << 16 | c << 8 | d)


def sendmail(to_address, subject, body, from_address=constants.smtp['from'], headers=None, **kw):
    try:
        web.sendmail(from_address, to_address, subject, body, headers=headers, **kw)
    except OSError:
        logger.exception("Could not send mail.")
    except smtplib.SMTPServerDisconnected:
        logger.exception("Server Disconnected.")
    except:
        logger.exception("Other email error:")


class MultiRender(object):
    def __init__(self, default):
        default_path = os.path.join(constants.base_path, default)
        # plugin_paths = [os.path.join(constants.plugins['root'], path) for path in plugins]
        self.default_renderer = web.template.render(default_path)
        self.bare_paths = []
        self.plugin_renderers = []

    def render(self, page, *args, **kwargs):
        for renderer in self.plugin_renderers:
            try:
                return getattr(renderer, page)(*args, **kwargs)
            except:
                continue
        return getattr(self.default_renderer, page)(*args, **kwargs)

    def install_plugin_template_path(self, path):
        if path in self.bare_paths:
            return
        self.bare_paths.append(path)
        plugin_path = os.path.join(constants.plugins['root'], path, "templates")
        self.plugin_renderers.append(web.template.render(plugin_path))


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
        db.query('PRAGMA journal_mode=WAL')
        sqlite_udf(db)
        old = web.config.debug
        web.config.debug = False
        db_quiet = web.database(**config)
        sqlite_udf(db_quiet)
        web.config.debug = old
    return db, db_quiet


def db_concat(db, *args):
    if not args:
        raise ValueError("Must supply arguments to concatenate")
    if db.dbname == 'mysql':
        return 'CONCAT({})'.format(','.join(map(repr,args)))
    elif db.dbname == 'sqlite':
        return '||'.join(map(repr,args))


# tell renderer where to look for templates
renderer = None
# database connections
db = None
db_quiet = None
# session storage. Session variable is filled in from server.py
session_store = None
session = None

init_globals()