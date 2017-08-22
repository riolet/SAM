# coding=utf-8
from spec.python import db_connection
import web
import sam.pages.sec_dashboard
from sam import common
from sam import constants


def test_render():
    with db_connection.env(mock_input=True, login_active=False, mock_session=True, mock_render=True):
        p = sam.pages.sec_dashboard.Dashboard()
        page_title = 'Dashboard'
        web.ctx.path = "/sam/testpage"
        dummy = p.GET()
        calls = common.renderer.calls
        assert calls[0] == ('render', ('_head', page_title,), {'lang': 'en', 'stylesheets': p.styles, 'scripts': p.scripts})
        assert calls[1] == ('render', ('en/_header', constants.get_navbar('en'), page_title, p.page.user, constants.debug, "/sam/testpage", constants.access_control, ('version française', '/fr/sam/testpage')), {})
        assert calls[2][1][0] == 'en/dashboard'
        assert calls[2][2] == {}
        assert calls[3] == ('render', ('en/_footer', {'English': '/en/sam/testpage', 'Française': '/fr/sam/testpage'}), {})
        assert calls[4] == ('render', ('_tail', ), {})
        assert dummy == "NoneNoneNoneNoneNone"
