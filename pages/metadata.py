import models.nodes
import models.settings
import models.datasources
import base


class Metadata(base.Headed):
    def __init__(self):
        super(Metadata, self).__init__("Host Details", True, False)
        self.scripts = ["/static/js/metadata.js",
                        "/static/js/map_ports.js",
                        "/static/js/map_selection.js",
                        "/static/js/map_data.js"]
        self.styles = ["/static/css/general.css"]
        self.datasources = None

    def require_dses(self):
        datasourceModel = models.datasources.Datasources(self.session, self.user.viewing)
        settingsModel = models.settings.Settings(self.session, self.user.viewing)
        datasources = datasourceModel.datasources.copy()
        default_ds = datasources.pop(settingsModel['datasource'])

        # a list of data sources, with the default at the head
        self.datasources = [default_ds] + datasources.values()

    def GET(self):
        self.require_group('read')
        nodesModel = models.nodes.Nodes(self.user.viewing)
        tag_list = nodesModel.get_tag_list()
        env_list = nodesModel.get_env_list()

        self.require_dses()

        return self.render('metadata', tag_list, env_list, self.datasources)
