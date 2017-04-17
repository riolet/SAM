import os
base_path = os.path.dirname(__file__)
from sam.ConfigEnvy import ConfigEnvy

ConfigEnvy.default_file_name = '/home/joe/SAM/default.cfg'

shared_tables = ['Settings', 'Ports', 'Datasources', 'LiveKeys', 'Subscriptions']
subscription_tables = ['Nodes', 'Tags', 'PortAliases']
datasource_tables = ['StagingLinks', 'Links', 'LinksIn', 'LinksOut', 'Syslog']

config = ConfigEnvy('SAM')
debug = config.get('debug', 'debug', default='False').lower() == 'true'

access_control = {
    'active': config.get('access_control', 'active', default='False').lower() == 'true',
    'login_url': config.get('access_control', 'login_url', default='/login_LDAP')
}

LDAP = {
    'connection_string': config.get('LDAP', 'connection_string', default='')
}

demo = {
    'id': 1,
    'email': 'sam@example.com',
    'name': 'SAM',
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

# to make sure config is not being read from anymore
del config

urls = [
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

    '/login_LDAP', 'sam.pages.login.Login_LDAP',
    '/logout', 'sam.pages.logout.Logout',
]

navbar = [
    {
        "name": "Map",
        "icon": "sitemap",
        "link": "/map",
        "group": "any"
    },
    {
        "name": "Table View",
        "icon": "table",
        "link": "/table",
        "group": "any"
    },
    {
        "name": "Host Details",
        "icon": "tasks",
        "link": "/metadata",
        "group": "any"
    },
    {
        "name": "Stats",
        "icon": "filter",
        "link": "/stats",
        "group": "any"
    },
    {
        "name": "Settings",
        "icon": "settings",
        "link": "/settings_page",
        "group": "any"
    }
]
