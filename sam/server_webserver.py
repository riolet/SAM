import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))  # could be executed from any directory
from sam import constants
import web
from sam import common
from sam import integrity
from sam import httpserver


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
    # some of the following lines are commented out because start_wsgi()
    # is run already when this module is loaded
    # TODO: make the above excuse removable
    # common.load_plugins()
    web.httpserver.StaticApp = httpserver.StaticApp
    app = web.application(constants.urls, globals())
    #check_database()
    #create_session(app)
    #for hook in constants.plugin_hooks_server_start:
    #    hook()
    httpserver.runwsgi(app.wsgifunc(httpserver.PluginStaticMiddleware), port)


def start_wsgi():
    common.load_plugins()
    app = web.application(constants.urls, globals())
    check_database()
    create_session(app)
    for hook in constants.plugin_hooks_server_start:
        hook()
    return app.wsgifunc(httpserver.PluginStaticMiddleware)


# This line must be present for use on wsgi-based servers.
application = start_wsgi()
