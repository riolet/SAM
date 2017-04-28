from spec.python import db_connection

import sam.pages.table
import sam.models.filters
import web
from sam import common
from sam import constants

sub_id = db_connection.default_sub
ds_full = db_connection.dsid_default
ds_empty = db_connection.dsid_short
ds_other = db_connection.dsid_live


def test_role_text():
    assert sam.pages.table.role_text(0.0) == '0.00 (client)'
    assert sam.pages.table.role_text(0.2) == '0.20 (mostly client)'
    assert sam.pages.table.role_text(0.4) == '0.40 (mixed client/server)'
    assert sam.pages.table.role_text(0.6) == '0.60 (mixed client/server)'
    assert sam.pages.table.role_text(0.8) == '0.80 (mostly server)'
    assert sam.pages.table.role_text(1.0) == '1.00 (server)'


def test_bytes_text():
    assert sam.pages.table.bytes_text(int(1e2)) == "100 B"
    assert sam.pages.table.bytes_text(int(1e3)) == "1000 B"
    assert sam.pages.table.bytes_text(int(1e4)) == "9 KB"
    assert sam.pages.table.bytes_text(int(1e5)) == "97 KB"
    assert sam.pages.table.bytes_text(int(1e6)) == "976 KB"
    assert sam.pages.table.bytes_text(int(1e7)) == "9765 KB"
    assert sam.pages.table.bytes_text(int(1e8)) == "95 MB"
    assert sam.pages.table.bytes_text(int(1e9)) == "953 MB"
    assert sam.pages.table.bytes_text(int(1e10)) == "9536 MB"
    assert sam.pages.table.bytes_text(int(1e11)) == "93 GB"
    assert sam.pages.table.bytes_text(int(1e12)) == "931 GB"
    assert sam.pages.table.bytes_text(int(1e13)) == "9313 GB"
    assert sam.pages.table.bytes_text(int(1e14)) == "90 TB"


def test_rate_text():
    assert sam.pages.table.byte_rate_text(int(1e2), 15) == "6 B/s"
    assert sam.pages.table.byte_rate_text(int(1e4), 15) == "666 B/s"
    assert sam.pages.table.byte_rate_text(int(1e6), 15) == "65 KB/s"
    assert sam.pages.table.byte_rate_text(int(1e8), 15) == "6 MB/s"
    assert sam.pages.table.byte_rate_text(int(1e10), 15) == "635 MB/s"
    assert sam.pages.table.byte_rate_text(int(1e12), 15) == "62 GB/s"
    assert sam.pages.table.byte_rate_text(int(1e14), 15) == "6 TB/s"


def test_packet_rate_text():
    assert sam.pages.table.packet_rate_text(int(1e2), 15) == "6 p/s"
    assert sam.pages.table.packet_rate_text(int(1e4), 15) == "666 p/s"
    assert sam.pages.table.packet_rate_text(int(1e6), 15) == "66 Kp/s"
    assert sam.pages.table.packet_rate_text(int(1e8), 15) == "6666 Kp/s"
    assert sam.pages.table.packet_rate_text(int(1e10), 15) == "666 Mp/s"
    assert sam.pages.table.packet_rate_text(int(1e12), 15) == "66 Gp/s"
    assert sam.pages.table.packet_rate_text(int(1e14), 15) == "6666 Gp/s"
    assert sam.pages.table.packet_rate_text(int(1e15), 15) == "66 Tp/s"


def test_nice_protocol():
    res = sam.pages.table.nice_protocol(u'tcp', u'udp')
    assert res == u'tcp (in), udp (out)'

    res = sam.pages.table.nice_protocol(u'tcp', u'')
    assert res == u'tcp (in)'
    res = sam.pages.table.nice_protocol(u'tcp', None)
    assert res == u'tcp (in)'

    res = sam.pages.table.nice_protocol(u'', u'udp')
    assert res == u'udp (out)'
    res = sam.pages.table.nice_protocol(None, u'udp')
    assert res == u'udp (out)'

    res = sam.pages.table.nice_protocol(u'abc,def', u'def,ghi,jkl')
    assert res == u'abc (in), def (i/o), jkl (out), ghi (out)'


def test_csv_escape():
    escaped = sam.pages.table.csv_escape('one "two" "can\'t" \'three\' four', '\\')
    assert escaped == r"""one \"two\" \"can't\" 'three' four"""

    escaped = sam.pages.table.csv_escape('one "two, five" "can\'t, not" \'three, and\' four', '\\')
    assert escaped == """\"one \\"two, five\\" \\"can't, not\\" 'three, and' four\""""

    escaped = sam.pages.table.csv_escape('inescapable', '\\')
    assert escaped == 'inescapable'


def test_csv_encode_row():
    colsep = '|'
    escape = '\\'
    ary = ['123', 'abc', 'one, two, three', 'use \'single\' or "double" quotes', 'end']
    encoded = sam.pages.table.csv_encode_row(ary, colsep, escape)
    expected = '123|abc|"one, two, three"|use \'single\' or \\"double\\" quotes|end'
    assert encoded == expected

    ary = ['this,is|one|other', 'abc', 'end']
    encoded = sam.pages.table.csv_encode_row(ary, colsep, escape)
    expected = '"this,is|one|other"|abc|end'
    assert encoded == expected

    ary = ['end']
    encoded = sam.pages.table.csv_encode_row(ary, colsep, escape)
    expected = 'end'
    assert encoded == expected


def test_csv_encode():
    colsep = '|'
    rowsep = '_'
    escape = '\\'
    table = [
        ['one', 'two', 'three'],
        ['four', 'five', 'six'],
        ['seven', 'eight', 'nine']
    ]
    encoded = sam.pages.table.csv_encode(table, colsep, rowsep, escape)
    expected = 'one|two|three_four|five|six_seven|eight|nine'
    assert encoded == expected

    table = [
        ['one', 'two', 'three']
    ]
    encoded = sam.pages.table.csv_encode(table, colsep, rowsep, escape)
    expected = 'one|two|three'
    assert encoded == expected

    table = [['one']]
    encoded = sam.pages.table.csv_encode(table, colsep, rowsep, escape)
    expected = 'one'
    assert encoded == expected


def test_columns_init():
    c = sam.pages.table.Columns(address=1)
    active = set([k for k, v in c.columns.iteritems() if v['active'] is True])
    assert active == {'address'}

    c = sam.pages.table.Columns(protocols=1)
    active = set([k for k, v in c.columns.iteritems() if v['active'] is True])
    assert active == {'protocols'}

    c = sam.pages.table.Columns(address=1, alias=1, conn_in=1, conn_out=1, role=1,
                            environment=1, tags=1, bytes=1, packets=1, protocols=1)
    active = set([k for k, v in c.columns.iteritems() if v['active'] is True])
    assert active == {'address', 'alias', 'conn_in', 'conn_out', 'role',
                      'environment', 'tags', 'bytes', 'packets', 'protocols'}

    c = sam.pages.table.Columns(empty=1, fake=1, flicker=1, tags=1)
    active = set([k for k, v in c.columns.iteritems() if v['active'] is True])
    assert active == {'tags'}

    c = sam.pages.table.Columns()
    active = set([k for k, v in c.columns.iteritems() if v['active'] is True])
    assert active == set()


def test_columns_translate():
    c = sam.pages.table.Columns(address=1, alias=1, conn_in=1, conn_out=1, role=1,
                            environment=1, tags=1, bytes=1, packets=1, protocols=1)
    data = {
        'address': u'12.34.56.78',
        'alias': u'pseudonym',
        'conn_in': 56,
        'conn_out': 80,
        'env': u'production',
        'tags': u'tag1,tag2',
        'parent_tags': u'ptag3,ptag4',
        'bytes_in': 86773,
        'bytes_out': 973,
        'seconds': 13,
        'packets_in': 85,
        'packets_out': 42,
        'proto_in': u'TCP,UDP,SMTP',
        'proto_out': u'UDP,ICMP'
    }
    row = c.translate_row(data)
    expected = [
        ('address', u'12.34.56.78'),
        ('alias', u'pseudonym'),
        ('conn_in', 56),
        ('conn_out', 80),
        ('role', u'0.41 (mixed client/server)'),
        ('environment', u'production'),
        ('tags', [[u'tag1', u'tag2'], [u'ptag3', u'ptag4']]),
        ('bytes', u'6 KB/s'),
        ('packets', u'9 p/s'),
        ('protocols', u'SMTP (in), TCP (in), UDP (i/o), ICMP (out)')]

    assert row == expected


def test_columns_headers():
    c = sam.pages.table.Columns(address=1)
    expected = [('address', 'Address')]
    assert c.headers() == expected

    c = sam.pages.table.Columns(protocols=1)
    expected = [('protocols', 'Protocols used')]
    assert c.headers() == expected

    c = sam.pages.table.Columns(address=1, alias=1, conn_in=1, conn_out=1, role=1,
                            environment=1, tags=1, bytes=1, packets=1, protocols=1)
    headers = c.headers()
    assert all(len(x) == 2 for x in headers)
    titles = set(x[0] for x in headers)
    assert titles == {'address', 'alias', 'conn_in', 'conn_out', 'role',
                      'environment', 'tags', 'bytes', 'packets', 'protocols'}

    c = sam.pages.table.Columns(empty=1, fake=1, flicker=1, tags=1)
    assert c.headers() == [('tags', 'Tags')]

    c = sam.pages.table.Columns()
    assert c.headers() == []


def test_decode_filters():
    q = sam.pages.table.Table
    port_f = sam.models.filters.filterTypes.index(sam.models.filters.PortFilter)
    data = {
        'filters': 'ds{ds}|{port};1;2;443'.format(ds=ds_full, port=port_f)
    }
    ds, filters = q.decode_filters(data)
    assert ds == ds_full
    assert len(filters) == 1
    assert isinstance(filters[0], sam.models.filters.PortFilter)

    data = {}
    ds, filters = q.decode_filters(data)
    assert ds is None
    assert len(filters) == 0


def test_next_page():
    q = sam.pages.table.Table
    web.ctx.fullpath = 'http://bob:password@sam.riolet.com:8080/table?ds=1&page=2&page_size=10'
    assert q.next_page(range(10), 1, 10) is False
    assert q.next_page(range(11), 1, 10) == 'http://bob:password@sam.riolet.com:8080/table?ds=1&page=3&page_size=10'
    assert q.next_page(range(10), 1, 9) == 'http://bob:password@sam.riolet.com:8080/table?ds=1&page=3&page_size=10'
    assert q.next_page(range(10), 50, 9) == 'http://bob:password@sam.riolet.com:8080/table?ds=1&page=52&page_size=10'
    assert q.next_page(range(9), 50, 9) is False
    assert q.next_page(range(9), 50, 10) is False

    web.ctx.fullpath = 'http://sam.com/table'
    assert q.next_page(range(6), 1, 5) == 'http://sam.com/table?page=3'

    web.ctx.fullpath = 'http://sam.com/table?page=3'
    assert q.next_page(range(6), 2, 5) == 'http://sam.com/table?page=4'


def test_prev_page():
    q = sam.pages.table.Table
    web.ctx.fullpath = 'http://bob:password@sam.riolet.com:8080/table?ds=1&page=3&page_size=10'
    assert q.prev_page(2) == 'http://bob:password@sam.riolet.com:8080/table?ds=1&page=2&page_size=10'
    assert q.prev_page(1) == 'http://bob:password@sam.riolet.com:8080/table?ds=1&page=1&page_size=10'
    assert q.prev_page(0) is False

    web.ctx.fullpath = 'http://sam.com/table'
    assert q.prev_page(2) == 'http://sam.com/table?page=2'


def test_spread():
    q = sam.pages.table.Table
    assert q.spread(range(0), 0, 10) == 'No matching results.'
    assert q.spread(range(2), 0, 10) == 'Results: 1 to 2'
    assert q.spread(range(11), 0, 10) == 'Results: 1 to 10'
    assert q.spread(range(11), 5, 10) == 'Results: 51 to 60'
    assert q.spread(range(4), 6, 10) == 'Results: 61 to 64'


def test_decode_order():
    q = sam.pages.table.Table
    data = {'sort': '1,asc'}
    assert q.decode_order(data) == (1, 'asc')
    data = {'sort': '1,desc'}
    assert q.decode_order(data) == (1, 'desc')
    data = {'sort': '1,masc'}
    assert q.decode_order(data) == (1, q.default_sort_direction)
    data = {'sort': '1'}
    assert q.decode_order(data) == (1, q.default_sort_direction)
    data = {'sort': 'desc,1'}
    assert q.decode_order(data) == (q.default_sort_column, q.default_sort_direction)
    data = {}
    assert q.decode_order(data) == (q.default_sort_column, q.default_sort_direction)


def test_decode_get():
    port_f = sam.models.filters.filterTypes.index(sam.models.filters.PortFilter)
    with db_connection.env(mock_input=True, mock_session=True, login_active=False):
        table = sam.pages.table.Table()
        data = {
            'filters': 'ds{ds}|{port};1;2;443'.format(ds=ds_full, port=port_f),
            'page': '3',
            'page_size': '20',
            'download': '0',
            'sort': '1,desc'
        }
        request = table.decode_get_request(data)
        expected = {
            'download': False,
            'ds': ds_full,
            'filters': [sam.models.filters.PortFilter(True, '2', '443')],
            'page': 2,
            'page_size': 20,
            'order_by': 1,
            'order_dir': 'desc',
            'flat': False
        }
        assert request == expected

        data = {}
        request = table.decode_get_request(data)
        expected = {
            'download': False,
            'ds': ds_full,
            'filters': [],
            'page': 0,
            'page_size': 10,
            'order_by': 0,
            'order_dir': 'asc',
            'flat': False
        }
        assert request == expected

        data = {
            'download': '1',
            'page': '20',
            'page_size': '2'
        }
        request = table.decode_get_request(data)
        assert request['download'] is True
        assert request['page'] == 0
        assert request['page_size'] == sam.pages.table.Table.download_max


def test_get_dses():
    with db_connection.env(mock_input=True, mock_session=True, login_active=False):
        table = sam.pages.table.Table()
        table.request = {'ds': ds_full}
        dses = table.get_dses()
        dses = [x['id'] for x in dses]
        assert dses == [ds_full, ds_empty, ds_other]

        table.request = {'ds': ds_empty}
        dses = table.get_dses()
        dses = [x['id'] for x in dses]
        assert dses == [ds_empty, ds_full, ds_other]

        table.request = {'ds': ds_other}
        dses = table.get_dses()
        dses = [x['id'] for x in dses]
        assert dses == [ds_other, ds_full, ds_empty]


def test_render():
    with db_connection.env(mock_input=True, mock_session=True, login_active=False, mock_render=True):
        p = sam.pages.table.Table()
        dummy = p.GET()
        calls = common.renderer.calls
        page_title = 'Table View'
        assert calls[0] == ('render', ('_head', page_title,), {'stylesheets': p.styles, 'scripts': p.scripts})
        assert calls[1] == ('render', ('_header', constants.navbar, page_title, p.user, constants.debug, False), {})
        assert calls[2][1][0] == 'table'
        assert len(calls[2][1]) == 11
        assert calls[2][2] == {}
        assert calls[3] == ('render', ('_tail', ), {})
        assert dummy == "NoneNoneNoneNone"


def test_download():
    port_f = sam.models.filters.filterTypes.index(sam.models.filters.PortFilter)
    with db_connection.env(mock_input=True, mock_session=True, login_active=False, mock_render=True):
        web.input = lambda: {'download': '1', 'filters': 'ds{ds}|{port};1;2;80'.format(ds=ds_full, port=port_f)}
        web.ctx['headers'] = []
        p = sam.pages.table.Table()
        csv_data = p.GET()
        lines = csv_data.splitlines()
        headers = lines[0]
        lines = lines[1:]
        addresses = [line.partition(',')[0] for line in lines]
        expected = [u'10.0.0.0/8',
                    u'10.20.0.0/16',
                    u'10.20.32.0/24',
                    u'10.20.32.43/32',
                    u'10.24.0.0/16',
                    u'10.24.34.0/24',
                    u'10.24.34.44/32',
                    u'10.24.34.45/32',
                    u'50.0.0.0/8',
                    u'50.64.0.0/16',
                    u'50.64.76.0/24',
                    u'50.64.76.86/32']
        assert addresses == expected
        assert headers == 'Address,Hostname,"Role (0 = client, 1 = server)",' \
                          'Environment,Tags,Bytes Handled,Packets Handled'

