import common
import web
import filters
import dbaccess


class Table(object):
    def __init__(self):
        self.pageTitle = "Host List"
        # self.columns = ["Address", "Hostname", "Role", "Environment", "Tags"]
        self.columns = ["Address", "Alias", "Connections in", "Connections out"]

    def GET(self):
        print("="*50)
        fs = None
        get_data = web.input()
        if "filters" in get_data:
            print "filters: ", get_data["filters"], "\n"
            fs = filters.readEncoded(get_data["filters"])
            for i in fs:
                print i.testString()
        print("="*50)

        data = []
        if fs:
            data = dbaccess.get_table_info(fs)
            for i in range(len(data)):
                data[i] = [data[i].address, data[i].alias, data[i].conn_in, data[i].conn_out]


        return str(common.render._head(self.pageTitle,
                                       stylesheets=["/static/css/table.css"],
                                       scripts=["/static/js/table.js",
                                                "/static/js/table_filters.js"])) \
               + str(common.render._header(common.navbar, self.pageTitle)) \
               + str(common.render.table(self.columns, data)) \
               + str(common.render._tail())
