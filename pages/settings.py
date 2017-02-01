import os
import common
import re
import base64
import importlib
import base
import models.datasources
import models.settings
import models.nodes
import models.links


def nice_name(s):
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
        if self.importer is None:
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
    recognized_commands = ["ds_name", "ds_live", "ds_interval", "ds_new",
                           "ds_rm", "ds_select", "rm_hosts", "rm_tags",
                           "rm_envs", "rm_conns", "upload", "live_dest"]

    def __init__(self):
        base.HeadlessPost.__init__(self)
        self.settingsModel = models.settings.Settings()
        self.dsModel = models.datasources.Datasources()

    def decode_get_request(self, data):
        return None

    def perform_get_command(self, request):
        settings = self.settingsModel.copy()
        datasources = self.dsModel.datasources
        response = {'settings': settings,
                    'datasources': datasources}
        return response

    def encode_get_response(self, response):
        result = response['settings']
        result['datasources'] = response['datasources']
        return result

    @staticmethod
    def get_available_importers():
        files = os.listdir(os.path.join(common.base_path, "importers"))
        files = filter(lambda x: x.endswith(".py") and x.startswith("import_") and x != "import_base.py", files)
        # remove .py extension
        files = [(f[:-3], nice_name(f[7:-3])) for f in files]
        return files

    @staticmethod
    def decode_datasource(param):
        ds = None
        ds_match = re.search("(\d+)", param)
        if ds_match:
            try:
                ds = int(ds_match.group())
            except (ValueError, TypeError):
                pass
        return ds

    def decode_post_request(self, data):
        request = {}
        command = data.get('command')
        if not command:
            raise base.RequiredKey('command', 'command')
        request['command'] = command

        if command not in self.recognized_commands:
            raise base.MalformedRequest("Unrecognized command: '{0}'".format(command))

        if command in ('ds_rm', 'ds_select', 'rm_conns', 'live_dest', 'ds_name', 'ds_live', 'ds_interval'):
            ds = self.decode_datasource(data.get('ds'))
            if not ds:
                raise base.RequiredKey('datasource', 'param1')
            request['ds'] = ds

        if command == 'ds_name':
            request['name'] = data.get('name')

        elif command == 'ds_live':
            request['is_active'] = data.get('is_active') == 'true'

        elif command == 'ds_interval':
            try:
                request['interval'] = int(data.get('interval', 'e'))
            except ValueError:
                raise base.MalformedRequest("Could not interpret auto-refresh interval from '{0}'"
                                            .format(repr(data.get('interval'))))

        elif command == 'ds_new':
            request['name'] = data.get('name')

        elif command == 'upload':
            request['format'] = data.get('format')
            request['file'] = data.get('file')

        if None in request.values():
            raise base.MalformedRequest("Could not parse arguments for command.")

        return request

    def perform_post_command(self, request):
        """
        Action		Command			Variables
        ------		-------			---------
        rename DS	"ds_name"		(ds, name)
        toggle ar	"ds_live"		(ds, is_active)
        ar interv	"ds_interval"	(ds, interval)
        new datas	"ds_new"		(name)
        remove ds	"ds_rm"			(ds)
        select ds   "ds_select"     (ds)
        delete hn	"rm_hosts"		()
        delete tg	"rm_tags"		()
        delete ev	"rm_envs"		()
        delete cn	"rm_conns"		(ds)
        live dest   "live_dest"     (ds)
        upload lg	"upload"		(ds, format, file)

        see also: self.recognized_commands
        """

        command = request['command']
        if command == 'ds_name':
            self.dsModel.set(request['ds'], name=request['name'])
        elif command == 'ds_live':
            db_active = 1 if request['is_active'] else 0
            self.dsModel.set(request['ds'], ar_active=db_active)
        elif command == 'ds_interval':
            self.dsModel.set(request['ds'], ar_interval=request['interval'])
        elif command == 'ds_new':
            self.dsModel.create_datasource(request['name'])
        elif command == 'ds_rm':
            self.dsModel.remove_datasource(request['ds'])
        elif command == 'ds_select':
            self.settingsModel['datasource'] = request['ds']
        elif command == 'rm_hosts':
            nodesModel = models.nodes.Nodes()
            nodesModel.delete_custom_hostnames()
        elif command == 'rm_tags':
            nodesModel = models.nodes.Nodes()
            nodesModel.delete_custom_tags()
        elif command == 'rm_envs':
            nodesModel = models.nodes.Nodes()
            nodesModel.delete_custom_envs()
        elif command == 'rm_conns':
            linksModel = models.links.Links()
            linksModel.delete_connections(request['ds'])
        elif command == 'live_dest':
            self.settingsModel['live_dest'] = request['live_dest']
        elif command == 'upload':
            b64start = request['file'].find(",")
            if b64start == -1:
                raise base.MalformedRequest("Could not decode file")
            log_file = base64.b64decode(request['file'][b64start + 1:])
            uploader = Uploader(request['ds'], request['format'])
            uploader.import_log(log_file)

        return "success"

    def encode_post_response(self, response):
        return {'result': response,
                'settings': self.settingsModel.copy(),
                'datasources': self.dsModel.sorted_list()}

    # handle HTTP GET requests here.  Name gets value from routing rules above.
    def GET(self):
        if "headless" in self.inbound:
            return base.HeadlessPost.GET(self)

        settings = self.settingsModel.copy()
        datasources = self.dsModel.sorted_list()
        importers = self.get_available_importers()

        page = str(common.render._head(self.pageTitle,
                                       stylesheets=["/static/css/general.css"],
                                       scripts=["/static/js/settings.js"]))
        page += str(common.render._header(common.navbar, self.pageTitle))
        page += str(common.render.settings(settings, datasources, importers))
        page += str(common.render._tail())
        return page
