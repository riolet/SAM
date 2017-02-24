import os
base_path = os.path.dirname(__file__)
from ConfigEnvy import ConfigEnvy

config = ConfigEnvy('SAM')
debug = config.get('debug', 'debug', default='False').lower() == 'true'
use_tls = config.get('ssl', 'use_ssl', default='False').lower() == 'true'

dbconfig = {
    'dbn': config.get('database', 'dbn'),
    'host': config.get('database', 'host'),
    'user': config.get('database', 'user'),
    'pw': config.get('database', 'pw'),
    'db': config.get('database', 'db'),
    'port': int(config.get('database', 'port'))
}

urls = (
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
    '/table', 'pages.table.Table',
)

navbar = [
    {
        "name": "Map",
        "icon": "sitemap",
        "link": "/map"
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
        "name": "Stats",
        "icon": "filter",
        "link": "/stats"
    },
    {
        "name": "Settings",
        "icon": "settings",
        "link": "/settings"
    }
]
