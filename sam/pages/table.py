from sam import errors
from sam import common
import web
import base
import sam.models.filters
import sam.models.settings
import sam.models.tables
import sam.models.datasources
import sam.models.nodes


def role_text(ratio):
    if ratio <= 0:
        desc = u"client"
    elif ratio < 0.35:
        desc = u"mostly client"
    elif ratio < 0.65:
        desc = u"mixed client/server"
    elif ratio < 1:
        desc = u"mostly server"
    else:
        desc = u"server"

    return u"{0:.2f} ({1})".format(ratio, desc)


def bytes_text(bytes):
    if bytes < 10000:
        return u"{0} B".format(int(bytes))
    bytes /= 1024
    if bytes < 10000:
        return u"{0} KB".format(int(bytes))
    bytes /= 1024
    if bytes < 10000:
        return u"{0} MB".format(int(bytes))
    bytes /= 1024
    if bytes < 10000:
        return u"{0} GB".format(int(bytes))
    bytes /= 1024
    return u"{0} TB".format(int(bytes))


def byte_rate_text(bytes, time):
    bytes = bytes / time
    if bytes < 2000:
        return u"{0} B/s".format(int(bytes))
    bytes /= 1024
    if bytes < 2000:
        return u"{0} KB/s".format(int(bytes))
    bytes /= 1024
    if bytes < 2000:
        return u"{0} MB/s".format(int(bytes))
    bytes /= 1024
    if bytes < 2000:
        return u"{0} GB/s".format(int(bytes))
    bytes /= 1024
    return u"{0} TB/s".format(int(bytes))


def packet_rate_text(bytes, time):
    bytes = bytes / time
    if bytes < 10000:
        return u"{0} p/s".format(int(bytes))
    bytes /= 1000
    if bytes < 10000:
        return u"{0} Kp/s".format(int(bytes))
    bytes /= 1000
    if bytes < 10000:
        return u"{0} Mp/s".format(int(bytes))
    bytes /= 1000
    if bytes < 10000:
        return u"{0} Gp/s".format(int(bytes))
    bytes /= 1000
    return u"{0} Tp/s".format(int(bytes))


def nice_protocol(p_in, p_out):
    """
    :param p_in: comma-seperated protocol list for inbound connections
     :type p_in: unicode
    :param p_out: comma-seperated protocol list for outbound connections
     :type p_out: unicode
    :return: user-friendly string describing in-/outbound connections
     :rtype: unicode
    """
    pin = p_in.split(u',') if p_in else []
    pout = p_out.split(u',') if p_out else []
    protocols = set(pin) | set(pout)
    protocols.discard(u'')
    ins = []
    outs = []
    both = []
    for p in protocols:
        if p in pin and p in pout:
            both.append(u'{} (i/o)'.format(p))
        elif p in pin:
            ins.append(u'{} (in)'.format(p))
        else:
            outs.append(u'{} (out)'.format(p))
    return u', '.join(ins + both + outs)


def csv_escape(datum, escape):
    """
    Escapes double quotation marks, and iff there's a comma in the datum, 
    encloses the whole thing in quotation marks. 
    :param datum: the string to escape
    :type datum: unicode
    :param escape: escape character 
    :type escape: unicode
    :return: escaped string
    :rtype: unicode
    """
    escaped = datum.replace(u'"', escape + u'"')
    if escaped.find(u",") != -1:
        return u'"{0}"'.format(escaped)
    return escaped


def csv_encode_row(ary, colsep, escape):
    """
    Encode a row(list) as a string
    :param ary: the list to encode
     :type ary: list[ unicode ]
    :param colsep: item separator. usually ','
     :type colsep: unicode
    :param escape: escape char. usually backslash. '\\'
     :type escape: unicode
    :return: string encoded list
    :rtype: unicode
    """
    if len(ary) == 0:
        return u""
    first = csv_escape(ary.pop(0), escape)
    if len(ary) == 0:
        return first

    return reduce(lambda accum, current: accum + colsep + csv_escape(current, escape), ary, first)


def csv_encode(data, colsep, rowsep, escape):
    """
    Encode a table (list of lists) as a string
    :param data: 
    :type data: list[ list[ unicode ] ]
    :param colsep: column data separator
    :type colsep: unicode
    :param rowsep: row data separator
    :type rowsep: unicode
    :param escape: 
    :type escape: unicode
    :return: data encoded as a csv string
    :rtype: unicode
    """
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
                'get': lambda x: x['address']},
            'alias': {
                'nice_name': "Hostname",
                'active': 'alias' in kwargs,
                'get': lambda x: '' if not x['alias'] else x['alias']},
            'conn_in': {
                'nice_name': "Total inbound connections",
                'active': 'conn_in' in kwargs,
                'get': lambda x: x['conn_in']},
            'conn_out': {
                'nice_name': "Total outbound connections",
                'active': 'conn_out' in kwargs,
                'get': lambda x: x['conn_out']},
            'role': {
                'nice_name': "Role (0 = client, 1 = server)",
                'active': 'role' in kwargs,
                'get': lambda x: role_text(float(x['conn_in']) / max(1.0, float(x['conn_in'] + x['conn_out'])))},
            'environment': {
                'nice_name': "Environment",
                'active': 'environment' in kwargs,
                'get': lambda x: x['env']},
            'tags': {
                'nice_name': "Tags",
                'active': 'tags' in kwargs,
                'get': lambda x: [
                    x['tags'].split(",") if x['tags'] else [], x['parent_tags'].split(",") if x['parent_tags'] else []]},
            'bytes': {
                'nice_name': "Bytes Handled",
                'active': 'bytes' in kwargs,
                'get': lambda x: byte_rate_text(x['bytes_in'] + x['bytes_out'], x['seconds'])},
            'packets': {
                'nice_name': "Packets Handled",
                'active': 'packets' in kwargs,
                'get': lambda x: packet_rate_text(x['packets_in'] + x['packets_out'], x['seconds'])},
            'protocols': {
                'nice_name': "Protocols used",
                'active': 'protocols' in kwargs,
                'get': lambda x: nice_protocol(x['proto_in'], x['proto_out'])},
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


class Table(base.headed):
    default_page = 1
    default_page_size = 10
    default_sort_column = 0
    default_sort_direction = 'asc'
    sort_directions = ['asc', 'desc']
    download_max = 1000000

    def __init__(self):
        super(Table, self).__init__("Table View", True, False)
        self.scripts = ["/static/js/table.js",
                        "/static/js/table_filters.js"]
        self.styles = ["/static/css/table.css",
                       "/static/css/general.css"]
        self.isdemo = False
        self.inbound = web.input()
        self.request = None
        self.response = None
        self.outbound = None
        self.tableModel = None
        self.nodesModel = None
        self.dsModel = sam.models.datasources.Datasources(common.db, self.page.session, self.page.user.viewing)
        self.columns = Columns(address=1, alias=1, protocol=1, role=1, bytes=1, packets=1, environment=1, tags=1)

    def decode_filters(self, data):
        fs = []
        ds = None
        if "filters" in data:
            ds, fs = sam.models.filters.readEncoded(common.db, self.page.user.viewing, data["filters"])
        return ds, fs

    @staticmethod
    def decode_order(data):
        """
        decode_order takes a dictionary that may have a 'sort' key
        and determines sort column (number) and direction (asc/desc).
        For use in the Order By sql clause
        :param data: 
        :return: column number and direction of sort
        :rtype: tuple[int, str]
        """
        if 'sort' not in data:
            return Table.default_sort_column, Table.default_sort_direction

        sort = data['sort'].split(",")
        try:
            column = int(sort[0])
        except ValueError:
            column = Table.default_sort_column
        if len(sort) == 2 and sort[1] in Table.sort_directions:
            direction = sort[1]
        else:
            direction = Table.default_sort_direction
        return column, direction

    def decode_get_request(self, data):
        ds, filters = self.decode_filters(data)
        print("ds filter-decoded to {}".format(ds))

        # fall back to default data source if not provided in query string.
        if ds is None:
            settings_model = sam.models.settings.Settings(common.db, self.page.session, self.page.user.viewing)
            ds = settings_model['datasource']
        print("ds is now {} (sub {})".format(ds, self.page.user.viewing))

        try:
            page = int(data.get('page', self.default_page))
        except (ValueError, TypeError):
            raise errors.MalformedRequest("Page number ('{0}') not understood.".format(data.get('page')))

        try:
            page_size = int(data.get('page_size', self.default_page_size))
        except (ValueError, TypeError):
            raise errors.MalformedRequest("Page size ('{0}') not understood.".format(data.get('page')))

        order_by, order_dir = self.decode_order(data)

        download = str(data.get('download', '0')) == '1'
        if download:
            page = 1
            page_size = self.download_max

        print("datasources: {}".format(self.dsModel.datasources))
        print("datasources[ds] is {0} ({0.__class__})".format(self.dsModel.datasources[ds]))
        print("the .get is {}".format(self.dsModel.datasources[ds].get))

        request = {
            'download': download,
            'ds': ds,
            'filters': filters,
            'page': page - 1,  # The page-1 is because page 1 should start with result 0
            'page_size': page_size,
            'order_by': order_by,
            'order_dir': order_dir,
            'flat': str(self.dsModel.datasources[ds].get('flat', 0)) == '1'
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

        # if flat mode, default a /32 subnet filter
        if request['flat']:
            if not any(isinstance(f, sam.models.filters.SubnetFilter) for f in request['filters']):
                request['filters'].append(sam.models.filters.SubnetFilter(True, '32'))

        self.tableModel = sam.models.tables.Table(common.db, self.page.user.viewing, self.request['ds'])
        data = self.tableModel.get_table_info(request['filters'],
                                              request['page'],
                                              request['page_size'],
                                              request['order_by'],
                                              request['order_dir'])
        rows = []
        for tr in data:
            rows.append(self.columns.translate_row(tr))
        return rows

    def encode_get_response_for_download(self, response):
        headers = self.columns.headers()
        headers = [h[1] for h in headers]
        for row in response:
            for icol in range(len(row)):
                if row[icol][0] == 'tags':
                    row[icol] = " ".join([" ".join(row[icol][1][0]), " ".join(row[icol][1][1])])
                else:
                    row[icol] = str(row[icol][1])
        outbound = [headers] + response
        return outbound

    def encode_get_response(self, response):
        headers = self.columns.headers()
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
        ds = self.request['ds']
        return self.dsModel.priority_list(ds)

    @staticmethod
    def next_page(rows, page, page_size):
        """
        
        :param rows: list of results from current page search, 
        used to determine if a next page exists (number of items > page_size)
         :type rows: list[]
        :param page: 0-based page number
         :type page: int
        :param page_size: number of results per page
         :type page_size: int
        :return: url to next page, or False
        :rtype: str or bool
        """
        if len(rows) > page_size:
            path = web.ctx.fullpath
            page_i = path.find("page=")
            if page_i != -1:
                amp_pos = path.find('&', page_i)
                if amp_pos != -1:
                    p_next = "{0}page={1}{2}".format(path[:page_i], page + 2, path[amp_pos:])
                else:
                    p_next = "{0}page={1}".format(path[:page_i], page + 2)
            else:
                if "?" in path:
                    p_next = path + "&page={0}".format(page + 2)
                else:
                    p_next = path + "?page={0}".format(page + 2)
        else:
            p_next = False
        return p_next

    @staticmethod
    def prev_page(page):
        if page >= 1:
            path = web.ctx.fullpath
            page_i = path.find("page=")
            if page_i != -1:
                amp_pos = path.find('&', page_i)
                if amp_pos != -1:
                    p_prev = "{0}page={1}{2}".format(path[:page_i], page, path[amp_pos:])
                else:
                    p_prev = "{0}page={1}".format(path[:page_i], page)
            else:
                if "?" in path:
                    p_prev = path + "&page={0}".format(page)
                else:
                    p_prev = path + "?page={0}".format(page)
        else:
            p_prev = False
        return p_prev

    @staticmethod
    def spread(rows, page, page_size):
        if rows:
            start = page * page_size + 1
            end = start + len(rows[:page_size]) - 1
            spread = "Results: {0} to {1}".format(start, end)
        else:
            spread = "No matching results."
        return spread

    def GET(self):
        self.page.require_group('read')
        self.nodesModel = sam.models.nodes.Nodes(common.db, self.page.user.viewing)

        self.request = self.decode_get_request(self.inbound)
        self.response = self.perform_get_command(self.request)

        if self.request['download']:
            self.outbound = self.encode_get_response_for_download(self.response)
            web.header("Content-Type", "application/csv")
            return csv_encode(self.outbound, ',', '\r\n', '\\')

        self.outbound = self.encode_get_response(self.response)

        html = self.render('table',
                           self.outbound['tags'],
                           self.outbound['envs'],
                           self.get_dses(),
                           self.outbound['headers'],
                           (self.request['order_by'], self.request['order_dir']),
                           self.outbound['rows'][:self.request['page_size']],
                           self.outbound['spread'],
                           self.outbound['prevPage'],
                           self.outbound['nextPage'],
                           self.isdemo)
        return html
