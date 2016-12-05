import common


class Settings:
    pageTitle = "Settings"

    # handle HTTP GET requests here.  Name gets value from routing rules above.
    def GET(self):
        return str(common.render._head(self.pageTitle,
                                       stylesheets=[],
                                       scripts=[])) \
               + str(common.render._header(common.navbar, self.pageTitle)) \
               + str(common.render.settings()) \
               + str(common.render._tail())
