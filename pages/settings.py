import common


class Settings:
    pageTitle = "Settings"

    def read_settings(self):
        settings = {}
        settings['data_source'] = "default"
        settings['all_data_sources'] = ['default', 'live', 'Wednesday']
        settings['colors'] = {}
        settings['colors']['c1'] = "#111111"
        settings['colors']['c2'] = "#222222"
        settings['colors']['c3'] = "#333333"
        settings['colors']['c4'] = "#444444"
        settings['colors']['c5'] = "#555555"
        settings['colors']['c6'] = "#666666"
        settings['autorefresh'] = {}
        settings['autorefresh']['active'] = True
        settings['autorefresh']['interval'] = 5*60


    # handle HTTP GET requests here.  Name gets value from routing rules above.
    def GET(self):
        return str(common.render._head(self.pageTitle,
                                       stylesheets=[],
                                       scripts=[])) \
               + str(common.render._header(common.navbar, self.pageTitle)) \
               + str(common.render.settings()) \
               + str(common.render._tail())
