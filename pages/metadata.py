import common


class Metadata(object):
    def __init__(self):
        self.pageTitle = "Metadata Test"

    def GET(self):
        return str(common.render._head(self.pageTitle,
                                       stylesheets=[],
                                       scripts=["/static/js/metadata.js",
                                                "/static/js/map_ports.js",
                                                "/static/js/map_selection.js",
                                                "/static/js/map_data.js",
                                                "/static/js/tablesort.js"])) \
               + str(common.render._header(common.navbar, self.pageTitle)) \
               + str(common.render.metadata()) \
               + str(common.render._tail())
