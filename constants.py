import os
base_path = os.path.dirname(__file__)
from ConfigEnvy import ConfigEnvy

config = ConfigEnvy('SAM')
debug = config.get('debug', 'debug', default='False').lower() == 'true'

shared_tables = ['Settings', 'Ports', 'Datasources', 'LiveKeys', 'Subscriptions']
subscription_tables = ['Nodes', 'Tags', 'PortAliases']
datasource_tables = ['StagingLinks', 'Links', 'LinksIn', 'LinksOut', 'Syslog']

demo = {
    'id': 1,
    'email': 'sam@example.com',
    'name': 'SAM',
}

dbconfig = {
    'dbn': config.get('database', 'dbn'),
    'host': config.get('database', 'host'),
    'user': config.get('database', 'user'),
    'pw': config.get('database', 'pw'),
    'db': config.get('database', 'db'),
    'port': int(config.get('database', 'port'))
}

urls = [
    '/', 'pages.map.Map',  # Omit the overview page and go straight to map (no content in overview anyway)
    '/map', 'pages.map.Map',
    '/stats', 'pages.stats.Stats',
    '/nodes', 'pages.nodes.Nodes',
    '/links', 'pages.links.Links',
    '/details', 'pages.details.Details',
    '/portinfo', 'pages.portinfo.Portinfo',
    '/nodeinfo', 'pages.nodeinfo.Nodeinfo',
    '/metadata', 'pages.metadata.Metadata',
    '/settings', 'pages.settings.Settings',
    '/settings_page', 'pages.settings_page.SettingsPage',
    '/table', 'pages.table.Table',
    '/about', 'pages.about.About',
    '/starting', 'pages.getting_started.GettingStarted'
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
