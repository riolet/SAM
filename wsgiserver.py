import sys
import os
import web

sys.path.append(os.path.dirname(__file__))

# web.config.debug = False

# Manage routing from here. Regex matches URL and chooses class by name
urls = (
    # '/', 'pages.overview.Overview',  # matched groups (in parens) are sent as arguments
    '/', 'pages.map.Map',  # Omit the overview page and go straight to map (no content in overview anyway)
    '/overview', 'pages.overview.Overview',
    '/map', 'pages.map.Map',
    '/stats', 'pages.stats.Stats',
    '/nodes', 'pages.nodes.Nodes',
    '/links', 'pages.links.Links',
    '/details', 'pages.details.Details',
    '/portinfo', 'pages.portinfo.Portinfo',
    '/nodeinfo', 'pages.nodeinfo.Nodeinfo',
)

app = web.application(urls, globals(), autoreload=False)
application = app.wsgifunc()
