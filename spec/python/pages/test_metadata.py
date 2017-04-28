from spec.python import db_connection

import sam.pages.metadata
from sam import common
from sam import constants


def test_render():
    with db_connection.env(mock_input=True, login_active=False, mock_session=True, mock_render=True):
        p = sam.pages.metadata.Metadata()
        common.session.clear()
        dummy = p.GET()
        calls = common.renderer.calls
        page_title = 'Host Details'
        tags = []
        envs = {'dev', 'inherit', 'production'}
        dses = [{'flat': 0, 'subscription': 1L, 'ar_active': 0, 'ar_interval': 300L, 'id': 1L, 'name': u'default'},
                {'flat': 0, 'subscription': 1L, 'ar_active': 0, 'ar_interval': 300L, 'id': 2L, 'name': u'short'},
                {'flat': 0, 'subscription': 1L, 'ar_active': 0, 'ar_interval': 300L, 'id': 3L, 'name': u'live'}]
        assert calls[0] == ('render', ('_head', page_title,), {'stylesheets': p.styles, 'scripts': p.scripts})
        assert calls[1] == ('render', ('_header', constants.navbar, page_title, p.user, constants.debug, False), {})
        assert calls[2] == ('render', ('metadata', tags, envs, dses), {})
        assert calls[3] == ('render', ('_tail', ), {})
        assert dummy == "NoneNoneNoneNone"
