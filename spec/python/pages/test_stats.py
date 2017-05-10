from spec.python import db_connection
import web
import sam.pages.stats
from sam import common
from sam import constants
import web
import json
import time
from datetime import datetime

ds_full = db_connection.dsid_default
ds_empty = db_connection.dsid_live


def test_render():
    with db_connection.env(mock_input=True, login_active=False, mock_session=True, mock_render=True):
        p = sam.pages.stats.Stats()
        page_title = 'Stats'
        web.ctx.path = "/sam/testpage"
        dummy = p.GET()
        calls = common.renderer.calls
        assert calls[0] == ('render', ('_head', page_title,), {'stylesheets': p.styles, 'scripts': p.scripts})
        assert calls[1] == ('render', ('_header', constants.navbar, page_title, p.page.user, constants.debug, "/sam/testpage", constants.access_control), {})
        assert calls[2][1][0] == 'stats'
        segments = calls[2][1][1]
        section_headers = [x[0] for x in segments]
        assert section_headers == ['Overall', 'Datasource: default', 'Datasource: short', 'Datasource: live']
        assert calls[2][2] == {}
        assert calls[3] == ('render', ('_footer', ), {})
        assert calls[4] == ('render', ('_tail', ), {})
        assert dummy == "NoneNoneNoneNoneNone"


def test_timerange():
    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        web.input = lambda: {'q': 'timerange', 'ds': 'ds{}'.format(ds_full)}
        web.ctx['headers'] = []
        p = sam.pages.stats.Stats()
        response = p.GET()
        timerange = json.loads(response)
        assert timerange == {"max": 1521498300, "min": 1453065600}

        web.input = lambda: {'q': 'timerange', 'ds': 'ds{}'.format(ds_empty)}
        web.ctx['headers'] = []
        p = sam.pages.stats.Stats()
        response = p.GET()
        timerange = json.loads(response)
        now = int(time.mktime(datetime.now().timetuple()))
        assert timerange == {"max": now, "min": now}


def test_protocols():
    with db_connection.env(mock_input=True, login_active=False, mock_session=True):
        web.input = lambda: {'q': 'protocols', 'ds': 'ds{}'.format(ds_full)}
        web.ctx['headers'] = []
        p = sam.pages.stats.Stats()
        response = p.GET()
        protocols = json.loads(response)
        assert set(protocols) == {u'TCP', u'UDP', u'ICMP'}

        web.input = lambda: {'q': 'protocols', 'ds': 'ds{}'.format(ds_empty)}
        web.ctx['headers'] = []
        p = sam.pages.stats.Stats()
        response = p.GET()
        protocols = json.loads(response)
        assert set(protocols) == set()
