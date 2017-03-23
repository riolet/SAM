import constants
import base
import ldap3
import errors


class Login_LDAP(base.Headed):
    def __init__(self):
        super(Login_LDAP, self).__init__('Login', False, True)
        self.styles = ["/static/css/general.css"]
        self.errors = []

    # ======== Get
    def GET(self):
        return self.render('login', constants.access_control['login_url'])

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


    def decode_connection_string(self):
        cstring = constants.config.get('LDAP', 'connection_string')
        server_address, _, namespace = cstring.rpartition('/')
        return server_address, namespace

    def perform_post_command(self, request):
        # prepare server information
        server_address, namespace = self.decode_connection_string()
        server = ldap3.Server(server_address)

        # submit credentials to LDAP server.
        user = "UID={user},{namespace}".format(user=request['user'], namespace=namespace)  # 'uid=admin,cn=users,cn=accounts,dc=demo1,dc=freeipa,dc=org'
        password = request['password']  # 'Secret123'
        conn = ldap3.Connection(server, user, password, auto_bind=True)

        # do login()
        #    or save errors in session and do redirect
        pass

    def encode_post_response(self, response):
        # redirect to home page / map
        return "This is a test"

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
            self.errors.append("Login failed.")
            return self.render('login', constants.access_control['login_url'], self.errors)

        return "<h1>Success</h1>\n<p>{}</p>".format(self.outbound)