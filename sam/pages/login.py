from sam import constants
import base
from sam import errors
try:
    import ldap3
    import ldap3.core.exceptions
    ldap_loaded = True
except:
    ldap_loaded = False
import web


class Login_LDAP(base.headed):
    def __init__(self):
        super(Login_LDAP, self).__init__(False, True)
        self.set_title(self.page.strings.login_title)
        self.styles = ["/static/css/general.css"]
        self.errors = []
        self.server_address, self.namespace = self.decode_connection_string(constants.LDAP['connection_string'])

    # ======== Get

    def GET(self):
        if self.page.user.logged_in:
            raise web.seeother('./map')
        if not ldap_loaded:
            print("ERROR: ldap3 library not installed.")
            print("       install ldap3 with pip:")
            print("       `pip install ldap3`")
            return self.render('login', constants.access_control['login_url'], [self.page.strings.login_LDAP_missing])

        return self.render('login', constants.access_control['login_url'])

    # ======== Post

    def decode_post_request(self, data):
        # read provided user and password
        password = data.get('password', None)
        user = data.get('user', None)
        # validate they exist
        if password is None or len(password) == 0:
            self.errors.append(self.page.strings.login_blank_pass)
        if user is None or len(user) == 0:
            self.errors.append(self.page.strings.login_blank_user)

        if self.errors:
            raise errors.MalformedRequest("Invalid Login information.")
        return {
            'user': user,
            'password': password
        }

    @staticmethod
    def decode_connection_string(cstring):
        server_address, _, namespace = cstring.rpartition('/')
        return server_address, namespace

    def perform_post_command(self, request):
        # submit credentials to LDAP server.
        if not ldap_loaded:
            self.errors.append(self.page.strings.login_LDAP_missing)
            raise errors.AuthenticationError('LDAP module not installed. Install by `pip install ldap3`.')
        user = "UID={user},{namespace}".format(user=request['user'], namespace=self.namespace)  # 'uid=admin,cn=users,cn=accounts,dc=demo1,dc=freeipa,dc=org'
        password = request['password']  # 'Secret123'
        server = ldap3.Server(self.server_address)

        try:
            conn = ldap3.Connection(server, user, password, auto_bind=True)
            conn.unbind()
        except ldap3.core.exceptions.LDAPSocketOpenError as e:
            self.errors.append(self.page.strings.login_LDAP_error.format(e.message))
            raise errors.AuthenticationError("Invalid Server information.")
        except ldap3.core.exceptions.LDAPBindError as e:
            self.errors.append(self.page.strings.login_invalid)
            raise errors.AuthenticationError("Invalid credentials.")

        # Assume authenticated at this point.
        self.page.user.login_simple(user)
        return True

    def encode_post_response(self, response):
        # redirect to home page / map
        return None

    def POST(self):
        """
        Entry point for POST requests to this endpoint.  Should not need to be overridden
        except to handle exceptions differently.
        :return: HTTP response data
        """

        try:
            self.request = self.decode_post_request(self.page.inbound)
            self.response = self.perform_post_command(self.request)
            self.outbound = self.encode_post_response(self.response)
        except Exception as e:
            print("Error logging in: {}".format(e.message))
            if not self.errors:
                self.errors.append(self.page.strings.login_failed)
            return self.render('login', constants.access_control['login_url'], self.errors)

        raise web.seeother('./map')