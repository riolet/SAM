from spec.python import db_connection

import pages.map
import common
import constants


def test_render():
    with db_connection.env(mock_input=True, login_active=False, mock_session=True, mock_render=True):
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
