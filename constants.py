import os
base_path = os.path.dirname(__file__)
from ConfigEnvy import ConfigEnvy




config = ConfigEnvy('SAM')
debug = config.get('debug', 'debug', default='False').lower() == 'true'

shared_tables = ['Settings', 'Ports', 'Datasources', 'LiveKeys', 'Subscriptions']
subscription_tables = ['Nodes', 'Tags', 'PortAliases']
datasource_tables = ['StagingLinks', 'Links', 'LinksIn', 'LinksOut', 'Syslog']

access_control = {
    'active': config.get('access_control', 'active', default='False').lower() == 'true',
    'login_url': config.get('access_control', 'login_url', default='/login_LDAP')
}

LDAP = {
    'connection_string': config.get('LDAP', 'connection_string', default='')
}

collector = {
    'hostname': config.get('collector', 'hostname'),
    'port': config.get('collector', 'port'),
    'server': config.get('collector', 'server'),
    'upload_key': config.get('collector', 'upload_key'),
    'format': config.get('collector', 'format'),
}

demo = {
    'id': 1,
    'email': 'sam@example.com',
    'name': 'SAM',
}

dbconfig = dict(config.items('database'))
if 'port' in dbconfig:
    dbconfig['port'] = int(dbconfig['port'])

localmode = False
local = {
    'dbn': config.get('local', 'dbn'),
    'db': config.get('local', 'db'),
    'collector_host': config.get('local', 'collector_host'),
    'collector_port': config.get('local', 'collector_port'),
    'collector_format': config.get('local', 'collector_format'),
    'liveserver_host': config.get('local', 'liveserver_host'),
    'liveserver_port': config.get('local', 'liveserver_port'),
    'server_host':  config.get('local', 'server_host'),
    'server_port':  config.get('local', 'server_port'),
}
def enable_local_mode():
    access_control['active'] = False
    dbconfig['db'] = local['db']
    dbconfig['dbn'] = local['dbn']
    collector['hostname'] = local['collector_host']
    collector['port'] = local['collector_port']
    collector['server'] = 'http://{}:{}'.format(local['liveserver_host'], local['liveserver_port'])
    collector['format'] = local['collector_format']
    global localmode
    localmode = True


# to make sure config is not being read from anymore
del config

urls = [
    '/', 'pages.map.Map',  # Omit the overview page and go straight to map (no content in overview anyway)
    '/map', 'pages.map.Map',
    '/stats', 'pages.stats.Stats',
    '/nodes', 'pages.nodes.Nodes',
    '/links', 'pages.links.Links',
    '/details', 'pages.details.Details',
    '/portinfo', 'pages.portinfo.Portinfo',
    '/metadata', 'pages.metadata.Metadata',
    '/settings', 'pages.settings.Settings',
    '/settings_page', 'pages.settings_page.SettingsPage',
    '/table', 'pages.table.Table',

    '/login_LDAP', 'pages.login.Login_LDAP',
    '/logout', 'pages.logout.Logout',
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
