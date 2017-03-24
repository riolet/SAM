import errors
import models.datasources
import web
import base


class Map(base.Headed):
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
        datasources = models.datasources.Datasources(self.session, self.user.viewing)
        dses = [(k, v['name']) for k, v in datasources.datasources.iteritems()]

        return self.render('map', dses)
