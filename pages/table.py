import common
import web
import filters
import dbaccess
import re
import base
import models.tables
import models.nodes
import models.datasources
import models.settings


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
    default_page = 1
    default_page_size = 10
    default_sort_column = 0
    default_sort_direction = 'asc'
    sort_directions = ['asc', 'desc']
    download_max = 1000000


    def __init__(self):
        self.pageTitle = "Table View"
        self.inbound = web.input()
        self.request = None
        self.response = None
        self.outbound = None
        self.tableModel = None
        self.nodesModel = models.nodes.Nodes()
        self.columns = Columns(address=1, alias=1, protocol=1, role=1, bytes=1, packets=1, environment=1, tags=1)

    def decode_filters(self, data):
        fs = []
        ds = None
        if "filters" in data:
            ds, fs = filters.readEncoded(data["filters"])
        return ds, fs

    def decode_order(self, data):
        if 'sort' not in data:
            return self.default_sort_column, self.default_sort_direction

        sort = data['sort'].split(",")
        try:
            column = int(sort[0])
        except ValueError:
            column = self.default_sort_column
        if len(sort) == 2 and sort[1] in self.sort_directions:
            direction = sort[1]
        else:
            direction = self.default_sort_direction
        return column, direction

    def decode_get_request(self, data):
        ds, filters = self.decode_filters(data)

        # fall back to default data source if not provided in query string.
        if not ds:
            settingsModel = models.settings.Settings()
            ds = settingsModel['datasource']

        try:
            page = int(data.get('page', self.default_page))
        except (ValueError, TypeError):
            raise base.MalformedRequest("Page number ('{0}') not understood.".format(data.get('page')))

        try:
            page_size = int(data.get('page_size', self.default_page_size))
        except (ValueError, TypeError):
            raise base.MalformedRequest("Page size ('{0}') not understood.".format(data.get('page')))

        order_by, order_dir = self.decode_order(data)

        download = data.get('download', '0') == 1
        if download:
            page = 1
            page_size = self.download_max

        request = {
            'download': download,
            'ds': ds,
            'filters': filters,
            'page': page - 1,  # The page-1 is because page 1 should start with result 0
            'page_size': page_size,
            'order_by': order_by,
            'order_dir': order_dir,
        }

        return request

    def perform_get_command(self, request):
        """
        :param request: has members:
         'download'
         'ds'
         'filters'
         'page'
         'page_size'
         'order'
        :return: a list of lists of tuples.
            return is a list of [rows]
            row is a list of [columns]
            column is a tuple of (name, value)
        """
        self.tableModel = models.tables.Table(self.request['ds'])
        data = self.tableModel.get_table_info(request['filters'],
                                              request['page'],
                                              request['page_size'],
                                              request['order_by'],
                                              request['order_dir'])
        rows = []
        for tr in data:
            rows.append(self.columns.translate_row(tr))
        return rows

    def encode_get_response(self, response):
        headers = self.columns.headers()
        if self.request['download']:
            headers = [h[1] for h in headers]
            for row in response:
                for icol in range(len(row)):
                    if row[icol][0] == 'tags':
                        row[icol] = " ".join([" ".join(row[icol][1][0]), " ".join(row[icol][1][1])])
                    else:
                        row[icol] = str(row[icol][1])
            outbound = [headers] + response
        else:
            outbound = {
                'rows': response,
                'headers': headers,
                'tags': self.nodesModel.get_tag_list(),
                'envs': self.nodesModel.get_env_list(),
                'nextPage': self.next_page(response, self.request['page'], self.request['page_size']),
                'prevPage': self.prev_page(self.request['page']),
                'spread': self.spread(response, self.request['page'], self.request['page_size']),
            }
        return outbound

    def get_dses(self):
        datasourcesModel = models.datasources.Datasources()
        ds = self.request['ds']
        return datasourcesModel.priority_list(ds)

    def next_page(self, rows, page, page_size):
        if len(rows) > page_size:
            path = web.ctx.fullpath
            page_i = path.find("page=")
            if page_i != -1:
                ampPos = path.find('&', page_i)
                if ampPos != -1:
                    nextPage = "{0}page={1}{2}".format(path[:page_i], page + 2, path[ampPos:])
                else:
                    nextPage = "{0}page={1}".format(path[:page_i], page + 2)
            else:
                if "?" in path:
                    nextPage = path + "&page={0}".format(page + 2)
                else:
                    nextPage = path + "?page={0}".format(page + 2)
        else:
            nextPage = False
        return nextPage

    def prev_page(self, page):
        if page >= 1:
            path = web.ctx.fullpath
            page_i = path.find("page=")
            if page_i != -1:
                ampPos = path.find('&', page_i)
                if ampPos != -1:
                    prevPage = "{0}page={1}{2}".format(path[:page_i], page, path[ampPos:])
                else:
                    prevPage = "{0}page={1}".format(path[:page_i], page)
            else:
                if "?" in path:
                    prevPage = path + "&page={0}".format(page)
                else:
                    prevPage = path + "?page={0}".format(page)
        else:
            prevPage = False
        return prevPage

    def spread(self, rows, page, page_size):
        if rows:
            start = (page) * page_size + 1
            end = start + len(rows[:page_size]) - 1
            spread = "Results: {0} to {1}".format(start, end)
        else:
            spread = "No matching results."
        return spread

    def GET(self):
        self.request = self.decode_get_request(self.inbound)
        self.response = self.perform_get_command(self.request)
        self.outbound = self.encode_get_response(self.response)

        if self.request['download']:
            web.header("Content-Type", "application/csv")
            return csv_encode(self.outbound, ',', '\r\n', '\\')

        html = str(common.render._head(self.pageTitle,
                                       stylesheets=["/static/css/table.css"],
                                       scripts=["/static/js/table.js",
                                                "/static/js/table_filters.js"]))
        html += str(common.render._header(common.navbar, self.pageTitle))
        html += str(common.render.table(
            self.outbound['tags'],
            self.outbound['envs'],
            self.get_dses(),
            self.outbound['headers'],
            (self.request['order_by'], self.request['order_dir']),
            self.outbound['rows'][:self.request['page_size']],
            self.outbound['spread'],
            self.outbound['prevPage'],
            self.outbound['nextPage']))
        html += str(common.render._tail())
        return html
