import common
import dbaccess


class Settings:
    pageTitle = "Settings"

    def read_settings(self):
        settings = dbaccess.get_settings(all=True)
        return settings

    # handle HTTP GET requests here.  Name gets value from routing rules above.
    def GET(self):
        settings = self.read_settings()
        datasources = settings.pop('datasources')

        return str(common.render._head(self.pageTitle,
                                       stylesheets=["/static/css/general.css"],
                                       scripts=["/static/js/settings.js"])) \
               + str(common.render._header(common.navbar, self.pageTitle)) \
               + str(common.render.settings(settings, datasources)) \
               + str(common.render._tail())
