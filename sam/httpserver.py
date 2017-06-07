import os
import posixpath
import urllib
import web
from sam import constants

# Overrides and augmentations of classes in web.httpserver
# Used in server_*.py


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

        # This is changed because os.getcwd() will give local files instead of package files.
        # this is the only change:
        path = constants.base_path

        for word in words:
            if os.path.dirname(word) or word in (os.curdir, os.pardir):
                # Ignore components that are not a simple file/directory name
                continue
            path = os.path.join(path, word)
        if trailing_slash:
            path += '/'
        return path


class PluginStaticApp(web.httpserver.StaticApp):
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

        # This is changed because os.getcwd() will give local files instead of package files.
        # this is the only change:
        path = constants.plugins['root']

        for word in words:
            if os.path.dirname(word) or word in (os.curdir, os.pardir):
                # Ignore components that are not a simple file/directory name
                continue
            path = os.path.join(path, word)
        if trailing_slash:
            path += '/'
        return path


class PluginStaticMiddleware:
    """WSGI middleware for serving static files."""

    def __init__(self, app):
        self.app = app
        self.prefixes = ['/{}/static'.format(plugin) for plugin in constants.plugin_static]

    def __call__(self, environ, start_response):
        path = environ.get('PATH_INFO', '')
        path = self.normpath(path)
        for plugin_static_dir in self.prefixes:
            if path.startswith(plugin_static_dir):
                return PluginStaticApp(environ, start_response)
        return self.app(environ, start_response)

    def normpath(self, path):
        path2 = posixpath.normpath(urllib.unquote(path))
        if path.endswith("/"):
            path2 += "/"
        return path2


def runwsgi(func, port):
    server_addr = web.validip(port)
    return web.httpserver.runsimple(func, server_addr)
