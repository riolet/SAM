import os
import common
import dbaccess
import re


def niceName(s):
    s = re.sub("([a-z])([A-Z]+)", lambda x: "{0} {1}".format(x.group(1), x.group(2)), s)
    s = s.replace("_", " ")
    s = re.sub("\s+", ' ', s)
    return s.title()


class Settings:
    pageTitle = "Settings"

    def read_settings(self):
        settings = dbaccess.get_settings(all=True)
        return settings

    def get_available_importers(self):
        files = os.listdir(common.base_path)
        files = filter(lambda x: x.endswith(".py") and x.startswith("import_") and x != "import_base.py", files)
        #remove .py extension
        files = [x[7:-3] for x in files]
        files = map(niceName, files)
        return files

    # handle HTTP GET requests here.  Name gets value from routing rules above.
    def GET(self):
        settings = self.read_settings()
        datasources = settings.pop('datasources')
        importers = self.get_available_importers()

        return str(common.render._head(self.pageTitle,
                                       stylesheets=["/static/css/general.css"],
                                       scripts=["/static/js/settings.js"])) \
               + str(common.render._header(common.navbar, self.pageTitle)) \
               + str(common.render.settings(settings, datasources, importers)) \
               + str(common.render._tail())
