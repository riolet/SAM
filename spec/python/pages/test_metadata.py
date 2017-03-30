from spec.python.db_connection import mocker

import web
import pages.metadata
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
        p = pages.metadata.Metadata()
        common.session.clear()
        dummy = p.GET()
        calls = common.render.calls
        page_title = 'Host Details'
        tags = []
        envs = {'dev', 'inherit', 'production'}
        dses = [{'subscription': 1L, 'ar_active': 0, 'ar_interval': 300L, 'id': 1L, 'name': u'default'},
            {'subscription': 1L, 'ar_active': 0, 'ar_interval': 300L, 'id': 2L, 'name': u'short'},
            {'subscription': 1L, 'ar_active': 0, 'ar_interval': 300L, 'id': 3L, 'name': u'live'}]
        assert calls[0] == ('_head', (page_title,), {'stylesheets': p.styles, 'scripts': p.scripts})
        assert calls[1] == ('_header', (constants.navbar, page_title, p.user, constants.debug), {})
        assert calls[2] == ('metadata', (tags, envs, dses), {})
        assert calls[3] == ('_tail', (), {})
        assert dummy == "NoneNoneNoneNone"
    finally:
        web.input = web.input_real
        constants.access_control['active'] = old_active
