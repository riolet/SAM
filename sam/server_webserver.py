import sys
import os
import operator
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


def localization_hook():
    default_lang = 'en'  # default language
    lang = None
    path_info = web.ctx.env['PATH_INFO']
    cookie = web.cookies().get("lang")

    # try reading language from URL path
    if not lang and path_info[1:3] in constants.supported_languages:
        web.ctx['fullpath'] = web.ctx['fullpath'][3:]
        web.ctx['path'] = web.ctx['path'][3:]
        web.ctx.env['REQUEST_URI'] = web.ctx.env['REQUEST_URI'][3:]
        web.ctx.env['PATH_INFO'] = path_info[3:]
        lang = path_info[1:3]
    # try reading language from cookie
    if not lang and cookie:
        if cookie in constants.supported_languages:
            lang = cookie
    # try reading language from browser
    if not lang and 'HTTP_ACCEPT_LANGUAGE' in web.ctx.env:
        lang_accept = web.ctx.env['HTTP_ACCEPT_LANGUAGE']
        items = [i.partition(';q=') for i in lang_accept.split(",") if i]
        decoded = {k.strip(): (float(v) if len(v) > 0 else 1.0) for k, _, v in items}
        langs = {k: decoded[k] for k in decoded.iterkeys() if k[:2] in constants.supported_languages}
        best = max(langs.iteritems(), key=operator.itemgetter(1))[0]
        if best:
            lang = best[:2]
    # use default language
    if not lang:
        lang = default_lang

    web.setcookie("lang", lang, 31536000, common.get_domain(), False, False, '/')
    common.session['lang'] = lang


def start_server(port):
    # some of the following lines are commented out because start_wsgi()
    # is run already when this module is loaded
    # TODO: make the above excuse removable
    # common.load_plugins()
    web.httpserver.StaticApp = httpserver.StaticApp
    # constants.init_urls()
    app = web.application(constants.urls, globals())
    #check_database()
    #create_session(app)
    #for hook in constants.plugin_hooks_server_start:
    #    hook()
    app.add_processor(web.loadhook(localization_hook))
    httpserver.runwsgi(app.wsgifunc(httpserver.PluginStaticMiddleware), port)


def start_wsgi():
    common.load_plugins()
    constants.init_urls()
    app = web.application(constants.urls, globals())
    check_database()
    create_session(app)
    for hook in constants.plugin_hooks_server_start:
        hook()
    app.add_processor(web.loadhook(localization_hook))
    return app.wsgifunc(httpserver.PluginStaticMiddleware)


# This line must be present for use on wsgi-based servers.
application = start_wsgi()
