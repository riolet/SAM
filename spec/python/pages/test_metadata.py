# coding=utf-8
from spec.python import db_connection
import web
import sam.pages.metadata
from sam import common
from sam import constants


def test_render():
    with db_connection.env(mock_input=True, login_active=False, mock_session=True, mock_render=True):
        common.session.clear()
        p = sam.pages.metadata.Metadata()
        page_title = 'Host Details'
        web.ctx.path = "/sam/testpage"
        dummy = p.GET()
        calls = common.renderer.calls
        tags = []
        envs = {'dev', 'inherit', 'production'}
        dses = [{'flat': 0, 'subscription': 1L, 'ar_active': 0, 'ar_interval': 300L, 'id': 1L, 'name': u'default'},
                {'flat': 0, 'subscription': 1L, 'ar_active': 0, 'ar_interval': 300L, 'id': 2L, 'name': u'short'},
                {'flat': 0, 'subscription': 1L, 'ar_active': 0, 'ar_interval': 300L, 'id': 3L, 'name': u'live'}]
        assert calls[0] == ('render', ('_head', page_title,), {'lang': 'en', 'stylesheets': p.styles, 'scripts': p.scripts})
        assert calls[1] == ('render', ('en/_header', constants.get_navbar('en'), page_title, p.page.user, constants.debug, "/sam/testpage", constants.access_control, ('version française', '/fr/sam/testpage')), {})
        assert calls[2] == ('render', ('en/metadata', tags, envs, dses), {})
        assert calls[3] == ('render', ('_tail', ), {})
        assert dummy == "NoneNoneNoneNone"
