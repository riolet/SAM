import os
import constants
import errors
import re
import base64
import base
import models.datasources
import models.settings
import models.nodes
import models.links
import models.livekeys
import models.upload
import models.subscriptions


def nice_name(s):
    s = re.sub("([a-z])([A-Z]+)", lambda x: "{0} {1}".format(x.group(1), x.group(2)), s)
    s = s.replace("_", " ")
    s = re.sub("\s+", ' ', s)
    return s.title()


class Settings(base.HeadlessPost):
    recognized_commands = ["ds_name", "ds_live", "ds_interval", "ds_new",
                           "ds_rm", "ds_select", "rm_hosts", "rm_tags",
                           "rm_envs", "rm_conns", "upload", "del_live_key",
                           "add_live_key"]

    def __init__(self):
        super(Settings, self).__init__()
        self.settingsModel = models.settings.Settings(self.session, self.user.viewing)
        self.dsModel = models.datasources.Datasources(self.session, self.user.viewing)
        self.livekeyModel = models.livekeys.LiveKeys(self.user.viewing)

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
        files = os.listdir(os.path.join(constants.base_path, "importers"))
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
            raise errors.RequiredKey('command', 'command')
        request['command'] = command

        if command not in self.recognized_commands:
            raise errors.MalformedRequest("Unrecognized command: '{0}'".format(command))

        if command in ('ds_rm', 'ds_select', 'rm_conns', 'ds_name', 'ds_live', 'ds_interval', 'upload', 'add_live_key'):
            ds = self.decode_datasource(data.get('ds'))
            if not ds:
                raise errors.RequiredKey('datasource', 'param1')
            request['ds'] = ds

        if command == 'ds_name':
            request['name'] = data.get('name')

        elif command == 'ds_live':
            request['is_active'] = data.get('is_active') == 'true'

        elif command == 'ds_interval':
            try:
                request['interval'] = int(data.get('interval', 'e'))
            except ValueError:
                raise errors.MalformedRequest("Could not interpret auto-refresh interval from '{0}'"
                                            .format(repr(data.get('interval'))))

        elif command == 'ds_new':
            request['name'] = data.get('name')

        elif command == 'upload':
            request['format'] = data.get('format')
            request['file'] = data.get('file')

        elif command == "del_live_key":
            request['key'] = data.get('key')

        if None in request.values():
            raise errors.MalformedRequest("Could not parse arguments for command.")

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
        upload lg	"upload"		(ds, format, file)
        add_liveK   "add_live_key"  (ds)
        del_liveK   "del_live_key"  (key)
        sub_plan    "sub_plan"      (plan)

        see also: self.recognized_commands
        """
        self.require_group('write')
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
            nodesModel = models.nodes.Nodes(self.user.viewing)
            nodesModel.delete_custom_hostnames()
        elif command == 'rm_tags':
            nodesModel = models.nodes.Nodes(self.user.viewing)
            nodesModel.delete_custom_tags()
        elif command == 'rm_envs':
            nodesModel = models.nodes.Nodes(self.user.viewing)
            nodesModel.delete_custom_envs()
        elif command == 'rm_conns':
            linksModel = models.links.Links(self.user.viewing, request['ds'])
            linksModel.delete_connections()
        elif command == 'upload':
            b64start = request['file'].find(",")
            if b64start == -1:
                raise errors.MalformedRequest("Could not decode file")
            log_file = base64.b64decode(request['file'][b64start + 1:])
            uploader = models.upload.Uploader(self.user.viewing, request['ds'], request['format'])
            uploader.import_log(log_file)
        elif command == 'add_live_key':
            self.livekeyModel.create(request['ds'])
        elif command == 'del_live_key':
            self.livekeyModel.delete(request['key'])

        return "success"

    def encode_post_response(self, response):
        encoded = {'result': response,
                'settings': self.settingsModel.copy(),
                'datasources': self.dsModel.sorted_list(),
                'livekeys': self.livekeyModel.read()}
        print(encoded)
        return encoded
