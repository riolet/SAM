from spec.python import db_connection
import sam.pages.logout

sub = db_connection.default_sub

def test_logout():
    with db_connection.env(mock_input=True, login_active=True, mock_session=True):
        p = sam.pages.logout.Logout()
        assert p.page.user.logged_in is False
        p.page.user.login_simple('phony', sub)
        assert p.page.user.logged_in is True
        p.perform_get_command({})
        assert p.page.user.logged_in is False
