import constants
import base


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
        # read provided username and password
        # validate they exist
        pass

    def perform_post_command(self, request):
        # submit credentials to LDAP server.
        # can bind?
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
            self.errors.append(e.message)
            return self.render('login', constants.access_control['login_url'], self.errors)

        return "<h1>Success</h1>\n<p>{}</p>".format(self.outbound)