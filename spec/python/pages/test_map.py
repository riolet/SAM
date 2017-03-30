from spec.python.db_connection import mocker

import web
import pages.map
import common
import constants

common.session = {}


def test_render():
    web.input_real = web.input
    old_active = constants.access_control['active']
    try:
        web.input = lambda: {}
        constants.access_control['active'] = False
        common.render = mocker()
        p = pages.map.Map()
        common.session.clear()
        dummy = p.GET()
        calls = common.render.calls
        page_title = 'Map'
        assert calls[0] == ('_head', (page_title,), {'stylesheets': p.styles, 'scripts': p.scripts})
        assert calls[1] == ('_header', (constants.navbar, page_title, p.user, constants.debug), {})
        assert calls[2] == ('map', ([(1, u'default'), (2, u'short'), (3, u'live')],), {})
        assert calls[3] == ('_tail', (), {})
        assert dummy == "NoneNoneNoneNone"
    finally:
        web.input = web.input_real
        constants.access_control['active'] = old_active