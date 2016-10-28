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
            rows = []
            for i in range(len(data)):
                row = [data[i].address]
                if data[i].alias:
                    row.append(data[i].alias)
                else:
                    row.append("-")

                if data[i].conn_in:
                    row.append(data[i].conn_in)
                else:
                    row.append(0)

                if data[i].conn_out:
                    row.append(data[i].conn_out)
                else:
                    row.append(0)

                rows.append(row)


        return str(common.render._head(self.pageTitle,
                                       stylesheets=["/static/css/table.css"],
                                       scripts=["/static/js/table.js",
                                                "/static/js/table_filters.js"])) \
               + str(common.render._header(common.navbar, self.pageTitle)) \
               + str(common.render.table(self.columns, rows)) \
               + str(common.render._tail())
