from spec.python import db_connection
import web
import sam.pages.map
from sam import common
from sam import constants


def test_render():
    with db_connection.env(mock_input=True, login_active=False, mock_session=True, mock_render=True):
        common.session.clear()
        p = sam.pages.map.Map()
        page_title = 'Map'
        web.ctx.path = "/sam/testpage"
        dummy = p.GET()
        calls = common.renderer.calls
        assert calls[0] == ('render', ('_head', page_title,), {'stylesheets': p.styles, 'scripts': p.scripts})
        assert calls[1] == ('render', ('_header', constants.navbar, page_title, p.page.user, constants.debug, "/sam/testpage", constants.access_control), {})
        assert calls[2] == ('render', ('map', [(1, u'default'), (2, u'short'), (3, u'live')],), {})
        assert calls[3] == ('render', ('_tail', ), {})
        assert dummy == "NoneNoneNoneNone"
