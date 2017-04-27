import os
import re
from sam import constants
import base
import sam.models.settings
import sam.models.datasources
import sam.models.livekeys
from sam import common


def nice_name(s):
    s = re.sub("([a-z])([A-Z]+)", lambda x: "{0} {1}".format(x.group(1), x.group(2)), s)
    s = s.replace("_", " ")
    s = re.sub("\s+", ' ', s)
    return s.title()


class SettingsPage(base.headed):
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
        self.settingsModel = sam.models.settings.Settings(common.db, self.session, self.user.viewing)
        self.dsModel = sam.models.datasources.Datasources(common.db, self.session, self.user.viewing)
        self.livekeyModel = sam.models.livekeys.LiveKeys(common.db, self.user.viewing)

        settings = self.settingsModel.copy()
        datasources = self.dsModel.sorted_list()
        importers = self.get_available_importers()
        livekeys = self.livekeyModel.read()

        return self.render('settings', self.user, settings, datasources, livekeys, importers)