import sam.models.nodes
import sam.models.settings
import sam.models.datasources
import base
from sam import common


class Metadata(base.headed):
    def __init__(self):
        super(Metadata, self).__init__(True, False)
        self.set_title(self.page.strings.meta_title)
        self.scripts = ["/static/js/metadata.js",
                        "/static/js/map_ports.js",
                        "/static/js/map_selection.js",
                        "/static/js/map_data.js"]
        self.styles = ["/static/css/general.css"]
        self.datasources = None

    def require_dses(self):
        datasourceModel = sam.models.datasources.Datasources(common.db, self.page.session, self.page.user.viewing)
        settingsModel = sam.models.settings.Settings(common.db, self.page.session, self.page.user.viewing)
        datasources = datasourceModel.datasources.copy()
        default_ds = datasources.pop(settingsModel['datasource'])

        # a list of data sources, with the default at the head
        self.datasources = [default_ds] + datasources.values()

    def GET(self):
        self.page.require_group('read')
        nodesModel = sam.models.nodes.Nodes(common.db, self.page.user.viewing)
        tag_list = nodesModel.get_tag_list()
        env_list = nodesModel.get_env_list()

        self.require_dses()

        return self.render('metadata', tag_list, env_list, self.datasources)
