import sys
import os
sys.path.append(os.path.dirname(__file__))  # could be executed from any directory
import constants
import web
web.config.debug = constants.debug  # must preceed import common
import common
import integrity
import models.livekeys
import models.settings
import subprocess
import shlex
import signal
import time


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