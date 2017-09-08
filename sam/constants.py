import importlib
import logging
import os
base_path = os.path.dirname(__file__)
from sam.ConfigEnvy import ConfigEnvy
logger = logging.getLogger(__name__)

supported_languages = ['en', 'fr', 'rv']
default_lang = 'en'

shared_tables = ['Settings', 'Ports', 'Datasources', 'LiveKeys', 'Subscriptions']
subscription_tables = ['Nodes', 'Tags', 'PortAliases', 'Alerts', 'Rules', 'ADWarnings']
datasource_tables = ['StagingLinks', 'Links', 'LinksIn', 'LinksOut', 'Syslog']

templates_folder = 'rule_templates'
rule_templates_path = os.path.join(base_path, templates_folder)

log_level = logging.INFO
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
    'default_name':  config.get('subscription', 'name'),
    'default_email': config.get('subscription', 'email')
}

LDAP = {
    'connection_string': config.get('LDAP', 'connection_string', default='')
}

security = dict(config.items('security'))
smtp = dict(config.items('smtp'))

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
plugin_models = []
plugin_rules = []
plugin_navbar_edits = []  # format to append is (link, dict) and each is applied with a dict.update() call.

plugin_hooks_traffic_import = []
plugin_hooks_server_start = []
plugin_hooks_server_stop = []

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
    '/sec_dashboard', 'sam.pages.sec_dashboard.Dashboard',
    '/sec_alerts', 'sam.pages.alerts.Alerts',
    '/sec_alerts/details', 'sam.pages.alerts.AlertDetails',
    '/sec_rules', 'sam.pages.rules.Rules',
    '/sec_rules/new', 'sam.pages.rules.RulesNew',
    '/sec_rules/edit', 'sam.pages.rules.RulesEdit',
    '/sec_rules/reapply', 'sam.pages.rules.RulesApply',
    '/ad_plugin', 'sam.pages.anomaly_plugin.ADPlugin',
]
urls = []


def init_urls():
    global urls
    urls = []
    urls.extend(plugin_urls)
    urls.extend([access_control['login_url'], access_control['login_target']])
    urls.extend([access_control['logout_url'], access_control['logout_target']])
    urls.extend(default_urls)


def find_url(target):
    for i in range(len(urls)/2):
        if urls[i*2+1] == target:
            return urls[i*2]
    return None


def get_navbar(lang):
    strings = importlib.import_module("sam.local." + lang)
    navbar = [
        {
            "name": strings.map_title,
            "icon": "sitemap",
            "link": "./map",
            "group": "any"
        },
        {
            "name": strings.table_title,
            "icon": "list layout",
            "link": "./table",
            "group": "any"
        },
        {
            "name": strings.meta_title,
            "icon": "tasks",
            "link": "./metadata",
            "group": "any"
        },
        {
            "name": strings.stats_title,
            "icon": "filter",
            "link": "./stats",
            "group": "any"
        },
        {
            "name": strings.dashboard_title,
            "icon": "dashboard",
            "link": "./sec_dashboard",
            "group": "any"
        },
        {
            "name": strings.settings_title,
            "icon": "settings",
            "link": "./settings_page",
            "group": "any"
        }
    ]
    for edit in plugin_navbar_edits:
        try:
            for link in navbar:
                if link['link'] == edit[0]:
                    link.update(edit[1])
                    break
        except:
            logger.warning("Unable to update navbar: {}".format(edit))

    return navbar