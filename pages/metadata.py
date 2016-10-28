import common
import web


class Metadata(object):
    def __init__(self):
        self.pageTitle = "Metadata Test"

    def GET(self):
        get_data = web.input()
        ip = ''
        if 'ip' in get_data:
            ip = get_data['ip']
        return str(common.render._head(self.pageTitle,
                                       stylesheets=[],
                                       scripts=["/static/js/metadata.js",
                                                "/static/js/map_ports.js",
                                                "/static/js/map_selection.js",
                                                "/static/js/map_data.js",
                                                "/static/js/tablesort.js"])) \
               + str(common.render._header(common.navbar, self.pageTitle)) \
               + str(common.render.metadata(ip)) \
               + str(common.render._tail())
