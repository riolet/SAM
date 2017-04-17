from spec.python import db_connection
import sam.pages.logout


def test_logout():
    with db_connection.env(mock_input=True, login_active=True, mock_session=True):
        p = sam.pages.logout.Logout()
        assert p.user.logged_in is False
        p.user.login_simple('phony')
        assert p.user.logged_in is True
        p.perform_get_command({})
        assert p.user.logged_in is False
