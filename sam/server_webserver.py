import sys
import os
import posixpath
import urllib
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))  # could be executed from any directory
from sam import constants
import web
web.config.debug = constants.debug  # must preceed import common
from sam import common
from sam import integrity


class StaticApp(web.httpserver.StaticApp):

    def set_translate_path_base(self, base):
        self.base_path = base

    def translate_path(self, path):
        """Translate a /-separated PATH to the local filename syntax.

        Components that mean special things to the local file system
        (e.g. drive or directory names) are ignored.  (XXX They should
        probably be diagnosed.)

        """

        # abandon query parameters
        path = path.split('?', 1)[0]
        path = path.split('#', 1)[0]
        # Don't forget explicit trailing slash when normalizing. Issue17324
        trailing_slash = path.rstrip().endswith('/')
        path = posixpath.normpath(urllib.unquote(path))
        words = path.split('/')
        words = filter(None, words)

        ### This is changed because os.getcwd() will give local files instead of package files.
        ### this is the only change:
        # path = os.getcwd()
        path = self.base_path

        for word in words:
            if os.path.dirname(word) or word in (os.curdir, os.pardir):
                # Ignore components that are not a simple file/directory name
                continue
            path = os.path.join(path, word)
        if trailing_slash:
            path += '/'
        return path

    def __iter__(self):
        environ = self.environ

        self.path = environ.get('PATH_INFO', '')
        self.client_address = environ.get('REMOTE_ADDR','-'), \
                              environ.get('REMOTE_PORT','-')
        self.command = environ.get('REQUEST_METHOD', '-')

        from cStringIO import StringIO
        self.wfile = StringIO() # for capturing error

        base_paths = [os.path.join(constants.plugins['root'], pspath) for pspath in constants.plugin_static]
        base_paths.append(constants.base_path)

        for base_path in base_paths:
            self.set_translate_path_base(base_path)
            try:
                path = self.translate_path(self.path)
                etag = '"%s"' % os.path.getmtime(path)
                client_etag = environ.get('HTTP_IF_NONE_MATCH')
                self.send_header('ETag', etag)
                if etag == client_etag:
                    self.send_response(304, "Not Modified")
                    self.start_response(self.status, self.headers)
                    raise StopIteration
            except OSError:
                continue # Probably a 404. Check the next path.
            break # Didn't error; must have found the file. stop looping.

        f = self.send_head()
        self.start_response(self.status, self.headers)

        if f:
            block_size = 16 * 1024
            while True:
                buf = f.read(block_size)
                if not buf:
                    break
                yield buf
            f.close()
        else:
            value = self.wfile.getvalue()
            yield value


def check_database():
    # Validate the database format
    if not integrity.check_and_fix_integrity():
        exit(1)


def create_session(app):
    # Create the session object
    if web.config.get('_session') is None:
        common.session = web.session.Session(app, common.session_store)
        web.config._session = common.session
    else:
        common.session = web.config._session


def start_server(port):
    web.httpserver.StaticApp = StaticApp
    app = web.application(constants.urls, globals())
    check_database()
    create_session(app)
    runwsgi(app.wsgifunc(), port)


def runwsgi(func, port):
    server_addr = web.validip(port)
    return web.httpserver.runsimple(func, server_addr)


def start_wsgi():
    app = web.application(constants.urls, globals())
    check_database()
    create_session(app)
    return app.wsgifunc()


if __name__ == "__main__":
    application = start_wsgi()
