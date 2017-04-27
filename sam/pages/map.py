from sam.models.datasources import Datasources
import base
from sam import common


class Map(base.headed):
    def __init__(self):
        base.Headed.__init__(self, "Map", header=True, footer=False)
        self.scripts = ['/static/js/map.js',
                        '/static/js/map_node.js',
                        '/static/js/map_links.js',
                        '/static/js/map_data.js',
                        '/static/js/map_selection.js',
                        '/static/js/map_ports.js',
                        '/static/js/map_render.js',
                        '/static/js/map_events.js',
                        '/static/js/timerange.js',
                        '/static/js/liveUpdate.js',
                        '/static/nouislider/nouislider.min.js']
        self.styles = ['/static/css/map.css',
                       '/static/css/timerange.css',
                       '/static/nouislider/nouislider.css',
                       '/static/nouislider/nouislider.pips.css']

    # handle HTTP GET requests here.  Name gets value from routing rules above.
    def GET(self):
        self.require_group('read')
        datasources = Datasources(common.db, self.session, self.user.viewing)
        dses = [(k, v['name']) for k, v in datasources.datasources.iteritems()]

        return self.render('map', dses)
