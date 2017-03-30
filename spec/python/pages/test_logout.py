import pages.logout
import common
import constants
import web

class session(dict):
    def kill(self):
        self.clear()

common.session = session()


def test_logout():
    web.input_real = web.input
    old_active = constants.access_control['active']
    try:
        web.input = lambda: {}
        constants.access_control['active'] = True
        p = pages.logout.Logout()
        assert p.user.logged_in == False
        p.user.login_simple('phony')
        assert p.user.logged_in == True
        p.perform_get_command({})
        assert p.user.logged_in == False
    finally:
        web.input = web.input_real
        constants.access_control['active'] = old_active