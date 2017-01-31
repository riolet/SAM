import os
import common
import dbaccess
import re
import web
import json
import base64
import importlib
import base
from models.datasources import Datasources
import models.settings


def niceName(s):
    s = re.sub("([a-z])([A-Z]+)", lambda x: "{0} {1}".format(x.group(1), x.group(2)), s)
    s = s.replace("_", " ")
    s = re.sub("\s+", ' ', s)
    return s.title()


class Uploader(object):

    def __init__(self, ds, log_format):
        self.ds = ds
        self.importer = None
        self.log_format = log_format
        self.get_importer()
        self.preprocessor = None

    def get_importer(self):
        try:
            m_importer = importlib.import_module(self.log_format)
            classes = filter(lambda x: x.endswith("Importer") and x != "BaseImporter", dir(m_importer))
            class_ = getattr(m_importer, classes[0])
            self.importer = class_()
            self.importer.datasource = self.ds
        except:
            self.importer = None

    def run_import(self, data):
        if self.importer == None:
            return

        self.importer.import_string(data)

    def run_prepro(self):
        import preprocess
        print("Running preprocessor..")
        print("ds: " + str(self.ds))

        preprocess.preprocess_log(self.ds)

    def import_log(self, data):
        self.run_import(data)
        self.run_prepro()



class Settings(base.HeadlessPost):
    pageTitle = "Settings"
    recognized_commands = ["ds_name", "ds_live", "ds_interval", "ds_new", "ds_rm", "ds_select", "rm_hosts" ,"rm_tags", "rm_envs", "rm_conns", "upload", "live_dest"]

    def __init__(self):
        base.HeadlessPost.__init__(self)

    def read_settings(self):
        settings = common.settings.copy()
        return settings

    def get_available_importers(self):
        files = os.listdir(os.path.join(common.base_path, "importers"))
        files = filter(lambda x: x.endswith(".py") and x.startswith("import_") and x != "import_base.py", files)
        #remove .py extension
        files = [(x[:-3], niceName(x[7:-3])) for x in files]
        return files

    def validate_ds_name(self, name):
        return re.match(r'^[a-z][a-z0-9_ ]*$', name, re.I)

    def validate_ds_interval(self, interval):
        return 5 <= interval <= 1800

    def run_command(self, command, params):
        """
        Action		Command			Variables
        ------		-------			---------
        rename DS	"ds_name"		(ds, name)
        toggle ar	"ds_live"		(ds, isActive)
        ar interv	"ds_interval"	(ds, interval)
        new datas	"ds_new"		(name)
        remove ds	"ds_rm"			(ds)
        select ds   "ds_select"     (ds)
        delete hn	"rm_hosts"		()
        delete tg	"rm_tags"		()
        delete ev	"rm_envs"		()
        delete cn	"rm_conns"		(ds)
        upload lg	"upload"		(ds, format, file)
        live dest   "live_dest"     (ds)

        see also: self.recognized_commands
        """
        response = {"code": 0, "message": "Success"}
        if command not in self.recognized_commands:
            return {"code": 3, "message": "Unrecognized command"}

        # translate ds argument
        ds = 0
        if command not in ["ds_new", 'rm_hosts', 'rm_tags', 'rm_envs', 'live_dest']:
            ds_s = params[0]
            ds_match = re.search("(\d+)", ds_s)
            if not ds_match:
                return {"code": 4, "message": "DS not determinable"}
            ds = int(ds_match.group())


        # process commands:
        #rename data source
        if command == "ds_name":
            name = params[1]
            if self.validate_ds_name(name):
                dbaccess.set_settings(ds=ds, name=name)
            else:
                return {"code": 4, "message": "Invalid name provided"}
        # toggle auto-refresh on data source
        elif command == "ds_live":
            active = params[1] == "true"
            if active:
                db_val = 1
            else:
                db_val = 0
            dbaccess.set_settings(ds=ds, ar_active=db_val)
        # adjust auto-refresh interval on data source
        elif command == "ds_interval":
            try:
                interval = int(params[1])
            except:
                return {"code": 4, "message": "Error interpreting interval"}
            if self.validate_ds_interval(interval):
                dbaccess.set_settings(ds=ds, ar_interval=interval)
            else:
                return {"code": 4, "message": "Invalid name provided"}
        # create new data source
        elif command == "ds_new":
            name = params[0]
            if self.validate_ds_name(name):
                dbaccess.create_datasource(name)
                data = dbaccess.get_settings(all=True)
                response['settings'] = dict(data)
            else:
                return {"code": 4, "message": "Invalid name provided"}
        # remove a data source
        elif command == "ds_rm":
            dbaccess.remove_datasource(ds)
            data = dbaccess.get_settings(all=True)
            response['settings'] = dict(data)
        # select a data source
        elif command == "ds_select":
            try:
                dbaccess.set_settings(datasource=ds)
            except:
                return {"code": 4, "message": "Invalid data source"}
        # remove custom tags
        elif command == "rm_tags":
            dbaccess.delete_custom_tags()
        # remove custom environments
        elif command == "rm_envs":
            dbaccess.delete_custom_envs()
        # remove custom host names
        elif command == "rm_hosts":
            dbaccess.delete_custom_hostnames()
        # remove all links/connections
        elif command == "rm_conns":
            dbaccess.delete_connections(ds)
        # update live data destination
        elif command == "live_dest":
            ds_match = re.search("(\d+)", params[0])
            if ds_match:
                ds = int(ds_match.group())
            else:
                ds = common.web.SQLLiteral("NULL")
            try:
                dbaccess.set_settings(live_dest=ds)
            except:
                return {"code": 4, "message": "Invalid data source"}
        # upload a log to the database
        elif command == "upload":
            ds = ds
            format = params[1]
            data = params[2]
            b64start = data.find(",")
            if b64start == -1:
                return {"code": 4, "message": "Unable to decode file"}
            file = base64.b64decode(data[b64start + 1:])

            uploader = Uploader(ds, format)
            uploader.import_log(file)

        return response

    # handle HTTP GET requests here.  Name gets value from routing rules above.
    def GET(self):
        if "headless" in web.input():
            web.header("Content-Type", "application/json")
            settings = models.settings.Settings()
            datasources = Datasources()

            setting = settings.copy()
            setting['datasources'] = datasources.datasources
            return json.dumps(setting)

        settings = self.read_settings()
        datasources = settings.pop('datasources')
        importers = self.get_available_importers()

        return str(common.render._head(self.pageTitle,
                                       stylesheets=["/static/css/general.css"],
                                       scripts=["/static/js/settings.js"])) \
               + str(common.render._header(common.navbar, self.pageTitle)) \
               + str(common.render.settings(settings, datasources, importers)) \
               + str(common.render._tail())

    def POST(self):
        web.header("Content-Type", "application/json")
        get_data = web.input()
        command = get_data.get('name', '')
        if command:
            paramKeys = filter(lambda x: x.startswith("param"), get_data.keys())
            paramKeys.sort()  # ensure param1,2,3 are in order (dict was unordered)
            params = map(get_data.get, paramKeys)
            result = self.run_command(command, params)
            return json.dumps(result)
        else:
            return json.dumps({"code": 1, "message": "Command name missing"})

