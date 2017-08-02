from sam.models.datasources import Datasources
import base
from sam import common


class Map(base.headed):
    def __init__(self):
        super(Map, self).__init__(True, False)
        self.set_title(self.page.strings.map_title)
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
                       '/static/nouislider/nouislider-dark.css',
                       '/static/nouislider/nouislider.pips.css']

    # handle HTTP GET requests here.  Name gets value from routing rules above.
    def GET(self):
        self.page.require_group('read')

        datasources = Datasources(common.db, self.page.session, self.page.user.viewing)
        dses = [(k, v['name']) for k, v in datasources.datasources.iteritems()]

        return self.render('map', dses)
