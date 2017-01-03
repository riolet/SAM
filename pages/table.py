import common
import web
import filters
import dbaccess


def role_text(ratio):
    if ratio <= 0:
        desc = "client"
    elif ratio < 0.35:
        desc = "mostly client"
    elif ratio < 0.65:
        desc = "mixed client/server"
    elif ratio < 1:
        desc = "mostly server"
    else:
        desc = "server"

    return "{0:.2f} ({1})".format(ratio, desc)


def bytes_text(bytes):
    if bytes < 10000:
        return "{0} B".format(int(bytes))
    bytes /= 1024
    if bytes < 10000:
        return "{0} KB".format(int(bytes))
    bytes /= 1024
    if bytes < 10000:
        return "{0} MB".format(int(bytes))
    bytes /= 1024
    if bytes < 10000:
        return "{0} GB".format(int(bytes))
    bytes /= 1024
    return "{0} TB".format(int(bytes))


def byte_rate_text(bytes, time):
    bytes = bytes / time
    if bytes < 2000:
        return "{0} B/s".format(int(bytes))
    bytes /= 1024
    if bytes < 2000:
        return "{0} KB/s".format(int(bytes))
    bytes /= 1024
    if bytes < 2000:
        return "{0} MB/s".format(int(bytes))
    bytes /= 1024
    if bytes < 2000:
        return "{0} GB/s".format(int(bytes))
    bytes /= 1024
    return "{0} TB/s".format(int(bytes))


def packet_rate_text(bytes, time):
    bytes = bytes / time
    if bytes < 10000:
        return "{0} p/s".format(int(bytes))
    bytes /= 1000
    if bytes < 10000:
        return "{0} Kp/s".format(int(bytes))
    bytes /= 1000
    if bytes < 10000:
        return "{0} Mp/s".format(int(bytes))
    bytes /= 1000
    if bytes < 10000:
        return "{0} Gp/s".format(int(bytes))
    bytes /= 1000
    return "{0} Tp/s".format(int(bytes))


def nice_protocol(p_in, p_out):
    pin = p_in.split(",")
    pout = p_out.split(",")
    protocols = set(pin).union(set(pout))
    if '' in protocols:
        protocols.remove('')
    directional_protocols = []
    for p in protocols:
        if p in pin and p in pout:
            directional_protocols.append(p + " (i/o)")
        elif p in pin:
            directional_protocols.append(p + " (in)")
        else:
            directional_protocols.append(p + " (out)")
    return u', '.join(directional_protocols)


def csv_escape(datum, escape):
    escaped = datum.replace('"', escape + '"')
    if escaped.find(",") != -1:
        return '"{0}"'.format(escaped)
    return escaped


def csv_encode_row(ary, colsep, escape):
    if len(ary) == 0:
        return ""
    first = csv_escape(ary.pop(0), escape)
    if len(ary) == 0:
        return first

    return reduce(lambda accum, current: accum + colsep + csv_escape(current, escape), ary, first)


def csv_encode(data, colsep, rowsep, escape):
    if len(data) == 0:
        return ""

    first = csv_encode_row(data.pop(0), colsep, escape)

    if len(data) == 0:
        return first

    return reduce(lambda accum, current: accum + rowsep + csv_encode_row(current, colsep, escape), data, first)


class Columns(object):
    def __init__(self, **kwargs):
        # manually specified here to give them an order
        self.all = ['address', 'alias', 'conn_in', 'conn_out', 'role', 'environment', 'tags', 'bytes', 'packets',
                    'protocols']

        self.columns = {
            'address': {
                'nice_name': "Address",
                'active': 'address' in kwargs,
                'get': lambda x: x.address},
            'alias': {
                'nice_name': "Hostname",
                'active': 'alias' in kwargs,
                'get': lambda x: '' if not x.alias else x.alias},
            'conn_in': {
                'nice_name': "Total inbound connections",
                'active': 'conn_in' in kwargs,
                'get': lambda x: x.conn_in},
            'conn_out': {
                'nice_name': "Total outbound connections",
                'active': 'conn_out' in kwargs,
                'get': lambda x: x.conn_out},
            'role': {
                'nice_name': "Role (0 = client, 1 = server)",
                'active': 'role' in kwargs,
                'get': lambda x: role_text(float(x.conn_in) / max(1.0, float(x.conn_in + x.conn_out)))},
            'environment': {
                'nice_name': "Environment",
                'active': 'environment' in kwargs,
                'get': lambda x: x.env},
            'tags': {
                'nice_name': "Tags",
                'active': 'tags' in kwargs,
                'get': lambda x: [
                    x.tags.split(", ") if x.tags else [], x.parent_tags.split(", ") if x.parent_tags else []]},
            'bytes': {
                'nice_name': "Bytes Handled",
                'active': 'bytes' in kwargs,
                'get': lambda x: byte_rate_text(x.bytes_in + x.bytes_out, x.seconds)},
            'packets': {
                'nice_name': "Packets Handled",
                'active': 'packets' in kwargs,
                'get': lambda x: packet_rate_text(x.packets_in + x.packets_out, x.seconds)},
            'protocols': {
                'nice_name': "Protocols used",
                'active': 'packets' in kwargs,
                'get': lambda x: nice_protocol(x.proto_in, x.proto_out)},
        }

    def translate_row(self, data):
        row = []
        for c in self.all:
            if self.columns[c]['active']:
                row.append((c, self.columns[c]['get'](data)))
        return row

    def headers(self):
        headers = [(c, self.columns[c]['nice_name']) for c in self.all if self.columns[c]['active']]
        return headers


class Table(object):
    def __init__(self):
        self.pageTitle = "Table View"
        self.columns = Columns(address=1, alias=1, protocol=1, role=1, bytes=1, packets=1, environment=1, tags=1)

    def filters(self, GET_data):
        fs = []
        if "filters" in GET_data:
            fs = filters.readEncoded(GET_data["filters"])
        return fs

    def page(self, GET_data):
        page = 1
        if 'page' in GET_data:
            try:
                page = int(GET_data['page'])
            except:
                page = 1
        return page

    def page_size(self, GET_data):
        page_size = 10
        if 'page_size' in GET_data:
            try:
                page_size = int(GET_data['page_size'])
            except:
                page_size = 10
        return page_size

    def rows(self, filters, page, page_size, order):
        """

        :param filters:  List of filter objects (see filters.py)
        :param page: page to return (1 is first page)
        :param page_size: number of result rows to return
        :param order: tuple of (column, direction) to sort results by.
        :return: a list of lists of tuples.
            return is a list of [rows]
            row is a list of [columns]
            column is a tuple of (name, value)

        """
        # The page-1 is because page 1 should start with result 0;
        # Note: get_table_info returns page_size + 1 results,
        #       so that IF it gets filled I know there's at least 1 more page to display.
        data = dbaccess.get_table_info(filters, page - 1, page_size, order[0], order[1])
        rows = []
        for tr in data:
            rows.append(self.columns.translate_row(tr))
        return rows

    def tags(self):
        return dbaccess.get_tag_list()

    def envs(self):
        return dbaccess.get_env_list()

    def next_page(self, rows, page, page_size):
        if len(rows) > page_size:
            path = web.ctx.fullpath
            page_i = path.find("page=")
            if page_i != -1:
                ampPos = path.find('&', page_i)
                nextPage = "{0}page={1}{2}".format(path[:page_i], page + 1, path[ampPos:])
            else:
                if "?" in path:
                    nextPage = path + "&page={0}".format(page + 1)
                else:
                    nextPage = path + "?page={0}".format(page + 1)
        else:
            nextPage = False
        return nextPage

    def prev_page(self, page):
        if page > 1:
            path = web.ctx.fullpath
            page_i = path.find("page=")
            if page_i != -1:
                ampPos = path.find('&', page_i)
                prevPage = "{0}page={1}{2}".format(path[:page_i], page - 1, path[ampPos:])
            else:
                prevPage = path + "&page={0}".format(page - 1)
        else:
            prevPage = False
        return prevPage

    def spread(self, rows, page, page_size):
        if rows:
            start = (page - 1) * page_size + 1
            end = start + len(rows[:page_size]) - 1
            spread = "Results: {0} to {1}".format(start, end)
        else:
            spread = "No matching results."
        return spread

    def order(self, GET_data):
        if 'sort' not in GET_data:
            return 0, 'asc'

        sort = GET_data['sort'].split(",")
        try:
            i = int(sort[0])
        except ValueError:
            i = 0
        if len(sort) == 2 and sort[1] in ('asc', 'desc'):
            direction = sort[1]
        else:
            direction = 'asc'
        return i, direction

    def get_csv_download(self, GET_data):
        filters = self.filters(GET_data)
        order = self.order(GET_data)
        headers = self.columns.headers()
        rows = self.rows(filters, 1, 1000000, order)
        #stringify rows
        for row in rows:
            for icol in range(len(row)):
                if row[icol][0] == 'tags':
                    row[icol] = " ".join([" ".join(row[icol][1][0]), " ".join(row[icol][1][1])])
                else:
                    row[icol] = str(row[icol][1])
        headers = [h[1] for h in headers]

        table = [headers] + rows
        web.header("Content-Type", "application/csv")
        return csv_encode(table, ',', '\r\n', '\\')

    def GET(self):
        GET_data = web.input()
        download = bool('download' in GET_data and GET_data['download'] == '1')
        if download:
            return self.get_csv_download(GET_data)

        filters = self.filters(GET_data)
        page = self.page(GET_data)
        page_size = self.page_size(GET_data)
        order = self.order(GET_data)
        rows = self.rows(filters, page, page_size, order)
        tags = self.tags()
        envs = self.envs()

        nextPage = self.next_page(rows, page, page_size)
        prevPage = self.prev_page(page)
        spread = self.spread(rows, page, page_size)

        return str(common.render._head(self.pageTitle,
                                       stylesheets=["/static/css/table.css"],
                                       scripts=["/static/js/table.js",
                                                "/static/js/table_filters.js"])) \
               + str(common.render._header(common.navbar, self.pageTitle)) \
               + str(common.render.table(self.columns.headers(), order, rows[:page_size], tags, envs, spread, prevPage, nextPage)) \
               + str(common.render._tail())
