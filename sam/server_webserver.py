import sys
import os
import posixpath
import urllib
sys.path.append(os.path.dirname(__file__))  # could be executed from any directory
from sam import constants
import web
web.config.debug = constants.debug  # must preceed import common
from sam import common
from sam import integrity


class StaticApp(web.httpserver.StaticApp):
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
        path = constants.base_path

        for word in words:
            if os.path.dirname(word) or word in (os.curdir, os.pardir):
                # Ignore components that are not a simple file/directory name
                continue
            path = os.path.join(path, word)
        if trailing_slash:
            path += '/'
        return path


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
    global application
    app = web.application(constants.urls, globals())
    check_database()
    create_session(app)
    return app.wsgifunc()


if __name__ == "__main__":
    application = start_wsgi()