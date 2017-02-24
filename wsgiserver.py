import sys
import os
sys.path.append(os.path.dirname(__file__))
import web
import constants



app = web.application(constants.urls, globals(), autoreload=False)
application = app.wsgifunc()
