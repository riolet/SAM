from spec.python import db_connection

import pages.settings_page
import common
import constants


def test_get_importers():
    importers = pages.settings_page.SettingsPage.get_available_importers()
    for importer in importers:
        assert len(importer) == 2
        assert isinstance(importer[0], basestring)
        assert isinstance(importer[1], basestring)


def test_render():
    with db_connection.env(mock_input=True, login_active=False, mock_session=True, mock_render=True):
        p = pages.settings_page.SettingsPage()
        dummy = p.GET()
        calls = common.render.calls
        page_title = 'Settings'
        assert calls[0] == ('_head', (page_title,), {'stylesheets': p.styles, 'scripts': p.scripts})
        assert calls[1] == ('_header', (constants.navbar, page_title, p.user, constants.debug), {})
        assert calls[2][0] == 'settings'
        assert len(calls[2][1]) == 5
        assert calls[2][2] == {}
        assert calls[3] == ('_footer', (), {})
        assert calls[4] == ('_tail', (), {})
        assert dummy == "NoneNoneNoneNoneNone"
