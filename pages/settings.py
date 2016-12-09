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
        self.recognized_commands = ["ds_name", "ds_live", "ds_interval", "ds_new", "ds_rm", "rm_hosts" ,"rm_tags", "rm_envs", "rm_conns", "upload"]
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
        delete ho	"rm_hosts"		(ds)
        delete ta	"rm_tags"		(ds)
        delete en	"rm_envs"		(ds)
        delete cn	"rm_conns"		(ds)
        upload lg	"upload"		(ds)
        """
        response = {"code": 0, "message": "Success"}
        if command not in self.recognized_commands:
            return {"code": 3, "message": "Unrecognized command"}

        ds = 0
        if command != "ds_new":
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
            dbaccess.set_settings(ds=ds, ar_active=active)
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

                out_id = {'dsid': 0}
                dbaccess.create_datasource(name, out_id)
                ds = out_id['dsid']
                data = dbaccess.get_datasource(ds)
                if data:
                    response['new_ds'] = dict(data)
                else:
                    return {"code": 5, "message": "Could not read what was written. Serious error. Try refreshing the pag."}
            else:
                return {"code": 4, "message": "Invalid name provided"}


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
            params = []
            params.append(get_data.get('param1', None))
            if command in self.two_param_cmds:
                params.append(get_data.get('param2', None))
            if all(params):
                result = self.run_command(command, params)
                return json.dumps(result)
            else:
                return json.dumps({"code": 2, "message": "Missing params for '{0}' command".format(command)})
        else:
            return json.dumps({"code": 1, "message": "Command name missing"})

