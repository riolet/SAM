import sys
import os
sys.path.append(os.path.dirname(__file__))
import constants
import web
web.config.debug = constants.debug
import common
import integrity

# Validate the database format
if not integrity.check_and_fix_integrity():
    exit(1)

# Create the session object
app = web.application(constants.urls, globals())
if web.config.get('_session') is None:
    common.session = web.session.Session(app, common.session_store)
    web.config._session = common.session
else:
    common.session = web.config._session


if __name__ == "__main__":
    app.run()
