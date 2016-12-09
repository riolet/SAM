import os
import common
import dbaccess
import re
import web
import json


def niceName(s):
    s = re.sub("([a-z])([A-Z]+)", lambda x: "{0} {1}".format(x.group(1), x.group(2)), s)
    s = s.replace("_", " ")
    s = re.sub("\s+", ' ', s)
    return s.title()


class Settings:
    pageTitle = "Settings"
    def __init__(self):
        self.recognized_commands = ["ds_name", "ds_live", "ds_interval", "ds_new", "ds_rm", "ds_select", "rm_hosts" ,"rm_tags", "rm_envs", "rm_conns", "upload"]
        self.two_param_cmds = ['ds_name', 'ds_live', 'ds_interval']

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
        upload lg	"upload"		(ds)

        see also: self.recognized_commands
        """
        response = {"code": 0, "message": "Success"}
        if command not in self.recognized_commands:
            return {"code": 3, "message": "Unrecognized command"}

        # translate ds argument
        ds = 0
        if command not in ["ds_new", 'rm_hosts', 'rm_tags', 'rm_envs']:
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
        return response

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

    def POST(self):
        web.header("Content-Type", "application/json")
        get_data = web.input()
        command = get_data.get('name', '')
        if command:
            paramKeys = filter(lambda x: x.startswith("param"), get_data.keys())
            params = map(get_data.get, paramKeys)
            result = self.run_command(command, params)
            return json.dumps(result)
        else:
            return json.dumps({"code": 1, "message": "Command name missing"})

