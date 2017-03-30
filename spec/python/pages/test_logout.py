from spec.python import db_connection
import pages.logout


def test_logout():
    with db_connection.env(mock_input=True, login_active=True, mock_session=True):
        p = pages.logout.Logout()
        assert p.user.logged_in == False
        p.user.login_simple('phony')
        assert p.user.logged_in == True
        p.perform_get_command({})
        assert p.user.logged_in == False
