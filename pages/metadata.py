import common
import web
import dbaccess


class Metadata(object):
    def __init__(self):
        self.pageTitle = "Host Details"

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
                                                "/static/js/map_data.js"])) \
               + str(common.render._header(common.navbar, self.pageTitle)) \
               + str(common.render.metadata(ip, dbaccess.get_tag_list(), dbaccess.get_env_list())) \
               + str(common.render._tail())
