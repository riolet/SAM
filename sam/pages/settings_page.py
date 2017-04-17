import os
import re
import constants
import base
import models.settings
import models.datasources
import models.livekeys
import common


def nice_name(s):
    s = re.sub("([a-z])([A-Z]+)", lambda x: "{0} {1}".format(x.group(1), x.group(2)), s)
    s = s.replace("_", " ")
    s = re.sub("\s+", ' ', s)
    return s.title()


class SettingsPage(base.Headed):
    def __init__(self):
        super(SettingsPage, self).__init__("Settings", True, True)
        self.styles = ["/static/css/general.css"]
        self.scripts = ["/static/js/settings.js"]
        self.settingsModel = None
        self.dsModel = None
        self.livekeyModel = None

    @staticmethod
    def get_available_importers():
        files = os.listdir(os.path.join(constants.base_path, "importers"))
        files = filter(lambda x: x.endswith(".py") and x.startswith("import_") and x != "import_base.py", files)
        # remove .py extension
        files = [(f[:-3], nice_name(f[7:-3])) for f in files]
        return files

    # handle HTTP GET requests here.  Name gets value from routing rules above.
    def GET(self):
        self.require_group('read')
        self.settingsModel = models.settings.Settings(common.db, self.session, self.user.viewing)
        self.dsModel = models.datasources.Datasources(common.db, self.session, self.user.viewing)
        self.livekeyModel = models.livekeys.LiveKeys(common.db, self.user.viewing)

        settings = self.settingsModel.copy()
        datasources = self.dsModel.sorted_list()
        importers = self.get_available_importers()
        livekeys = self.livekeyModel.read()

        return self.render('settings', self.user, settings, datasources, livekeys, importers)