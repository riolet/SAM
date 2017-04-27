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
        super(Login_LDAP, self).__init__('Login', False, True)
        self.styles = ["/static/css/general.css"]
        self.errors = []
        self.server_address, self.namespace = self.decode_connection_string(constants.LDAP['connection_string'])

    # ======== Get

    def GET(self):
        if self.user.logged_in:
            raise web.seeother('./map')
        if not ldap_loaded:
            print("ERROR: ldap3 library not installed.")
            print("       install ldap3 with pip:")
            print("       `pip install ldap3`")
            return self.render('login', constants.find_url(constants.access_control['login_page']), ['LDAP module not installed. Cannot perform login.'])

        return self.render('login', constants.find_url(constants.access_control['login_page']))

    # ======== Post

    def decode_post_request(self, data):
        # read provided user and password
        password = data.get('password', None)
        user = data.get('user', None)
        # validate they exist
        if password is None or len(password) == 0:
            self.errors.append("Password may not be blank.")
        if user is None or len(user) == 0:
            self.errors.append("User may not be blank.")

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
            self.errors.append('LDAP module not installed. Cannot perform login.')
            raise errors.AuthenticationError('LDAP module not installed. Install by `pip install ldap3`.')
        user = "UID={user},{namespace}".format(user=request['user'], namespace=self.namespace)  # 'uid=admin,cn=users,cn=accounts,dc=demo1,dc=freeipa,dc=org'
        password = request['password']  # 'Secret123'
        server = ldap3.Server(self.server_address)

        try:
            conn = ldap3.Connection(server, user, password, auto_bind=True)
            conn.unbind()
        except ldap3.core.exceptions.LDAPSocketOpenError as e:
            self.errors.append("Could not connect to LDAP server: {}. Check configuration.".format(e.message))
            raise errors.AuthenticationError("Invalid Server information.")
        except ldap3.core.exceptions.LDAPBindError as e:
            self.errors.append("Invalid Credentials")
            raise errors.AuthenticationError("Invalid credentials.")

        # Assume authenticated at this point.
        self.user.login_simple(user)
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
            self.request = self.decode_post_request(self.inbound)
            self.response = self.perform_post_command(self.request)
            self.outbound = self.encode_post_response(self.response)
        except Exception as e:
            print("Error logging in: {}".format(e.message))
            if not self.errors:
                self.errors.append("Login failed.")
            return self.render('login', constants.find_url(constants.access_control['login_page']), self.errors)

        raise web.seeother('./map')