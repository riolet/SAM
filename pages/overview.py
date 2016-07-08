import web
import common

class Overview:
    pageTitle = "Overview"

    # handle HTTP GET requests here.  Name gets value from routing rules above.
    def GET(self):
        return str(common.render._head(self.pageTitle)) \
             + str(common.render._header(common.navbar, self.pageTitle)) \
             + str(common.render.overview()) \
             + str(common.render._tail())