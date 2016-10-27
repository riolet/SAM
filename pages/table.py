import common
import web
import filters


class Table(object):
    def __init__(self):
        self.pageTitle = "Host List"
        self.columns = ["Address", "Hostname", "Role", "Environment", "Tags"]

    def GET(self):
        print("="*50)

        get_data = web.input()
        if "filters" in get_data:
            print "filters: ", get_data["filters"], "\n"
            filters.readEncoded(get_data["filters"])

        print("="*50)

        return str(common.render._head(self.pageTitle,
                                       stylesheets=["/static/css/table.css"],
                                       scripts=["/static/js/table.js",
                                                "/static/js/table_filters.js"])) \
               + str(common.render._header(common.navbar, self.pageTitle)) \
               + str(common.render.table(self.columns)) \
               + str(common.render._tail())
