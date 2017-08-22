# coding=utf-8
from spec.python import db_connection
import web
import sam.pages.settings_page
from sam import common
from sam import constants


def test_get_importers():
    importers = sam.pages.settings_page.SettingsPage.get_available_importers()
    for importer in importers:
        assert len(importer) == 2
        assert isinstance(importer[0], basestring)
        assert isinstance(importer[1], basestring)


def test_render():
    with db_connection.env(mock_input=True, login_active=False, mock_session=True, mock_render=True):
        p = sam.pages.settings_page.SettingsPage()
        page_title = 'Settings'
        web.ctx.path = "/sam/testpage"
        dummy = p.GET()
        calls = common.renderer.calls
        assert calls[0] == ('render', ('_head', page_title,), {'lang': 'en', 'stylesheets': p.styles, 'scripts': p.scripts})
        assert calls[1] == ('render', ('en/_header', constants.get_navbar('en'), page_title, p.page.user, constants.debug, "/sam/testpage", constants.access_control, ('version française', '/fr/sam/testpage')), {})
        assert calls[2][1][0] == 'en/settings'
        assert len(calls[2][1]) == 9
        assert calls[2][2] == {}
        assert calls[3] == ('render', ('en/_footer', {'English': '/en/sam/testpage', 'Française': '/fr/sam/testpage'}), {})
        assert calls[4] == ('render', ('_tail', ), {})
        assert dummy == "NoneNoneNoneNoneNone"
