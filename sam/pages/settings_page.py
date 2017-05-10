import os
import re
from sam import constants
import base
import sam.models.settings
import sam.models.datasources
import sam.models.livekeys
import sam.models.nodes
from sam import common
import pprint


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
        self.nodes_model = None

    @staticmethod
    def get_available_importers():
        files = os.listdir(os.path.join(constants.base_path, "importers"))
        files = filter(lambda x: x.endswith(".py") and x.startswith("import_") and x != "import_base.py", files)
        # remove .py extension
        files = [(f[:-3], nice_name(f[7:-3])) for f in files]
        return files

    def get_tags_preview(self):
        return self.nodes_model.get_tag_list()

    def get_envs_preview(self):
        envs = self.nodes_model.get_env_list()
        envs.discard("inherit")
        return list(envs)

    def get_hosts_preview(self):
        return self.nodes_model.get_hostnames_preview()

    # handle HTTP GET requests here.  Name gets value from routing rules above.
    def GET(self):
        self.page.require_group('read')
        self.settingsModel = sam.models.settings.Settings(common.db, self.page.session, self.page.user.viewing)
        self.dsModel = sam.models.datasources.Datasources(common.db, self.page.session, self.page.user.viewing)
        self.livekeyModel = sam.models.livekeys.LiveKeys(common.db, self.page.user.viewing)
        self.nodes_model = sam.models.nodes.Nodes(common.db, self.page.user.viewing)

        settings = self.settingsModel.copy()
        datasources = self.dsModel.sorted_list()
        importers = self.get_available_importers()
        livekeys = self.livekeyModel.read()
        tags_preview = self.get_tags_preview()
        envs_preview = self.get_envs_preview()
        hosts_preview = self.get_hosts_preview()


        return self.render('settings', self.page.user, settings, datasources, livekeys, importers, tags_preview, envs_preview, hosts_preview)