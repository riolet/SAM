import common


class Table(object):
    def __init__(self):
        self.pageTitle = "Host List"
        self.columns = ["Address", "Hostname", "Role", "Environment", "Tags"]


    def GET(self):
        return str(common.render._head(self.pageTitle,
                                       stylesheets=["/static/css/table.css"],
                                       scripts=[])) \
               + str(common.render._header(common.navbar, self.pageTitle)) \
               + str(common.render.table(self.columns)) \
               + str(common.render._tail())
