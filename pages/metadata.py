import common
import models.nodes
import models.settings
import models.datasources

class Metadata(object):
    def __init__(self):
        self.pageTitle = "Host Details"
        self.dses = None

    def require_dses(self):
        datasourceModel = models.datasources.Datasources()
        settingsModel = models.settings.Settings()
        datasources = datasourceModel.datasources.copy()
        default_ds = datasources.pop(settingsModel['datasource'])

        # a list of data sources, with the default at the head
        self.datasources = [default_ds] + datasources.values()

    def GET(self):
        nodesModel = models.nodes.Nodes()
        tag_list = nodesModel.get_tag_list()
        env_list = nodesModel.get_env_list()

        self.require_dses()

        return str(common.render._head(self.pageTitle,
                                       stylesheets=[],
                                       scripts=["/static/js/metadata.js",
                                                "/static/js/map_ports.js",
                                                "/static/js/map_selection.js",
                                                "/static/js/map_data.js"])) \
               + str(common.render._header(common.navbar, self.pageTitle)) \
               + str(common.render.metadata(tag_list, env_list, self.datasources)) \
               + str(common.render._tail())
