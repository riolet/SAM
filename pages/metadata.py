import common
import web
import dbaccess


class Metadata(object):
    def __init__(self):
        self.pageTitle = "Host Details"
        self.dses = None

    def require_dses(self):
        settings = dbaccess.get_settings(all=True)

        default_ds = settings['datasource']['id']
        # put default datasource at the head of the list
        self.dses = [datasource for datasource in settings['datasources']]
        for i in range(len(self.dses)):
            if self.dses[i]['id'] == default_ds:
                self.dses.insert(0, self.dses.pop(i))
                break

    def GET(self):
        get_data = web.input()

        self.require_dses()

        return str(common.render._head(self.pageTitle,
                                       stylesheets=[],
                                       scripts=["/static/js/metadata.js",
                                                "/static/js/map_ports.js",
                                                "/static/js/map_selection.js",
                                                "/static/js/map_data.js"])) \
               + str(common.render._header(common.navbar, self.pageTitle)) \
               + str(common.render.metadata(dbaccess.get_tag_list(), dbaccess.get_env_list(), self.dses)) \
               + str(common.render._tail())
