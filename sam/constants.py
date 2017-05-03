import os
base_path = os.path.dirname(__file__)
from sam.ConfigEnvy import ConfigEnvy

shared_tables = ['Settings', 'Ports', 'Datasources', 'LiveKeys', 'Subscriptions']
subscription_tables = ['Nodes', 'Tags', 'PortAliases']
datasource_tables = ['StagingLinks', 'Links', 'LinksIn', 'LinksOut', 'Syslog']

config = ConfigEnvy('SAM')
debug = config.get('debug', 'debug', default='False').lower() == 'true'

plugins = {
    'root': config.get('plugins', 'root'),
    'enabled': [p.strip() for p in config.get('plugins', 'enabled').split(',') if p.strip()],
    'loaded': []
}

access_control = {
    'active':          config.get('access_control', 'active', default='False').lower() == 'true',
    'login_url':       config.get('access_control', 'login_url'),
    'login_target':    config.get('access_control', 'login_target'),
    'login_redirect':  config.get('access_control', 'login_redirect'),
    'logout_url':      config.get('access_control', 'logout_url'),
    'logout_target':   config.get('access_control', 'logout_target'),
    'logout_redirect': config.get('access_control', 'logout_redirect'),
    'local_tls':       config.get('access_control', 'local_tls', default='False').lower() == 'true',
    'local_tls_cert':  config.get('access_control', 'local_tls_cert'),
    'local_tls_key':   config.get('access_control', 'local_tls_key')
}

subscription = {
    'default-name':  config.get('subscription', 'name'),
    'default-email': config.get('subscription', 'email')
}

LDAP = {
    'connection_string': config.get('LDAP', 'connection_string', default='')
}

collector = dict(config.items('collector'))
aggregator = dict(config.items('aggregator'))
webserver = dict(config.items('webserver'))
dbconfig = dict(config.items('database'))
if 'port' in dbconfig:
    dbconfig['port'] = int(dbconfig['port'])

use_whois = False
localmode = False
local = {
    'dbn': config.get('local', 'dbn'),
    'db': config.get('local', 'db'),
    'collector_host':   config.get('local', 'collector_host'),
    'collector_port':   config.get('local', 'collector_port'),
    'collector_format': config.get('local', 'collector_format'),
    'liveserver_host':  config.get('local', 'aggregator_host'),
    'liveserver_port':  config.get('local', 'aggregator_port'),
    'server_host':      config.get('local', 'webserver_host'),
    'server_port':      config.get('local', 'webserver_port'),
}


def enable_local_mode():
    access_control['active'] = False
    dbconfig['db'] = local['db']
    dbconfig['dbn'] = local['dbn']
    collector['listen_host'] = local['collector_host']
    collector['listen_port'] = local['collector_port']
    collector['target_host'] = local['liveserver_host']
    collector['target_port'] = local['liveserver_port']
    collector['format'] = local['collector_format']
    global localmode
    localmode = True

plugin_templates = []
plugin_static = []
plugin_importers = []
plugin_urls = []

default_urls = [
    '/', 'sam.pages.map.Map',  # Omit the overview page and go straight to map (no content in overview anyway)
    '/map', 'sam.pages.map.Map',
    '/stats', 'sam.pages.stats.Stats',
    '/nodes', 'sam.pages.nodes.Nodes',
    '/links', 'sam.pages.links.Links',
    '/details', 'sam.pages.details.Details',
    '/portinfo', 'sam.pages.portinfo.Portinfo',
    '/metadata', 'sam.pages.metadata.Metadata',
    '/settings', 'sam.pages.settings.Settings',
    '/settings_page', 'sam.pages.settings_page.SettingsPage',
    '/table', 'sam.pages.table.Table',
]
urls = []


def find_url(target):
    for i in range(len(urls)/2):
        if urls[i*2+1] == target:
            return urls[i*2]
    return None

navbar = [
    {
        "name": "Map",
        "icon": "sitemap",
        "link": "./map",
        "group": "any"
    },
    {
        "name": "Table View",
        "icon": "table",
        "link": "./table",
        "group": "any"
    },
    {
        "name": "Host Details",
        "icon": "tasks",
        "link": "./metadata",
        "group": "any"
    },
    {
        "name": "Stats",
        "icon": "filter",
        "link": "./stats",
        "group": "any"
    },
    {
        "name": "Settings",
        "icon": "settings",
        "link": "./settings_page",
        "group": "any"
    }
]
