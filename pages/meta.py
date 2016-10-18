import common


class Meta(object):
    def __init__(self):
        self.pageTitle = "Metadata Test"

    def GET(self):
        return str(common.render._head(self.pageTitle,
                                       stylesheets=[],
                                       scripts=[])) \
               + str(common.render._header(common.navbar, self.pageTitle)) \
               + str(common.render.metadata()) \
               + str(common.render._tail())
