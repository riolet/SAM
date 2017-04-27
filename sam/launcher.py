import sys
import os
import getopt
import multiprocessing
import importlib
import traceback
sys.path.append(os.path.dirname(__file__))  # this could be executed from any directory
from sam import constants

application = None

# targets:
#   webserver
#     --target=webserver
#   wsgi webserver
#     --target=webserver --wsgi
#   aggregator
#     --target=aggregator
#   wsgi aggregator
#     --target=aggregator --wsgi
#   collector
#     --target=collector
#   localmode combo
#     --local --scanner=tcpdump
#   import
#     --target=import  --format=palo_alto


# suggested demo invocation:
# sudo tcpdump -i any -f --immediate-mode -l -n -Q inout -tt | python launcher.py --local --whois --format=tcpdump


def main(argv=None):
    if argv == None:
        argv = sys.argv

    kwargs, args = getopt.getopt(argv[1:], '', ['format=', 'port=', 'target=', 'dest=', 'sub=', 'local', 'whois', 'wsgi'])

    defaults = {
        'format': 'tcpdump',
        'port': None,
        'target': 'webserver',
        'local': False,
        'whois': False,
        'wsgi': False,
        'dest': 'default',
        'sub': constants.demo['id']
    }
    valid_formats = ['tcpdump', 'nfdump', 'paloalto', 'tshark', 'asa', 'aws', 'none']
    valid_targets = ['aggregator', 'collector', 'webserver', 'import']

    parsed_args = defaults.copy()
    for key, val in kwargs:
        if key == '--local':
            parsed_args['local'] = True
        if key == '--wsgi':
            parsed_args['wsgi'] = True
        if key == '--whois':
            parsed_args['whois'] = True
        if key == '--format':
            parsed_args['format'] = val
        if key == '--target':
            parsed_args['target'] = val
        if key == '--port':
            parsed_args['port'] = val
        if key == '--dest':
            parsed_args['dest'] = val
        if key == '--sub':
            parsed_args['sub'] = val

    if parsed_args['format'] not in valid_formats:
        print("Invalid format")
        sys.exit(1)
    if parsed_args['target'] not in valid_targets:
        print("Invalid target")
        sys.exit(1)
    if parsed_args['whois']:
        constants.use_whois = True
    if parsed_args['local']:
        launch_localmode(parsed_args)
    elif parsed_args['target'] == 'webserver':
        launch_webserver(parsed_args)
    elif parsed_args['target'] == 'collector':
        launch_collector(parsed_args)
    elif parsed_args['target'] == 'aggregator':
        launch_aggregator(parsed_args)
    elif parsed_args['target'] == 'import':
        launch_importer(parsed_args, args)
    else:
        print("Error determining what to launch.")


def load_plugins():
    plugin_path = os.path.abspath(constants.plugins['root'])
    if not os.path.isdir(plugin_path):
        return
    sys.path.append(plugin_path)
    plugin_names = constants.plugins['enabled']
    if plugin_names == ['ALL']:
        plugin_names = os.listdir(plugin_path)
        plugin_names = filter(lambda x: os.path.isdir(os.path.join(plugin_path, x)), plugin_names)
    for plugin in plugin_names:
        try:
            mod = importlib.import_module(plugin)
            mod.sam_installer.install()
        except:
            print("Failed to load {}".format(plugin))
            raise

    # Much of sam.common gets initialized the first time it's loaded.
    # Plugins change the initialization data, prompting this reload.
    import web
    import sam.common
    web.config.debug = constants.debug
    reload(sam.common)


def launch_webserver(args):
    load_plugins()
    import sam.server_webserver
    if args['wsgi']:
        print('launching wsgi webserver')
        global application
        application = sam.server_webserver.start_wsgi()
    else:
        port = args['port']
        if port is None:
            port = constants.webserver['listen_port']
        print('launching dev webserver on {}'.format(port))
        sam.server_webserver.start_server(port=port)
        print('webserver shut down.')


def launch_collector(args):
    import server_collector
    port = args.get('port', None)
    if port is None:
        port = constants.collector['listen_port']
    print('launching collector on {}'.format(args['port']))
    collector = server_collector.Collector()
    collector.run(port=args['port'], format=args['format'])
    print('collector shut down.')


def launch_aggregator(args):
    import server_aggregator
    if args['wsgi']:
        print("launching wsgi aggregator")
        global application
        application = server_aggregator.start_wsgi()
    else:
        port = args.get('port', None)
        if port is None:
            port = constants.aggregator['listen_port']
        print('launching dev aggregator on {}'.format(port))
        server_aggregator.start_server(port=port)
        print('aggregator shut down.')


def launch_importer(parsed, args):
    import common
    datasource = parsed['dest']
    subscription_id = parsed['sub']
    format = parsed['format']

    if len(args) != 1:
        print("Please specify one source file. Exiting.")
        return

    importer = get_importer(format)
    if importer is None:
        return
    importer.set_subscription(subscription_id)
    from sam.models.datasources import Datasources
    d_model = Datasources(common.db_quiet, {}, subscription_id)
    try:
        dsid = int(datasource)
    except (TypeError, ValueError):
        try:
            dsid = d_model.name_to_id(datasource)
        except:
            print("Could not read datasource. Exiting.")
            return
    importer.set_datasource(dsid)

    if importer.validate_file(args[0]):
        importer.import_file(args[0])
    else:
        print("Could not open source file. Exiting.")
        return

    from sam.preprocess import Preprocessor
    processor = Preprocessor(common.db_quiet, subscription_id, dsid)
    processor.run_all()


def get_importer(importer_name):
    if importer_name.startswith("import_"):
        importer_name = importer_name[7:]
    i = importer_name.rfind(".py")
    if i != -1:
        importer_name = importer_name[:i]

    # attempt to import the module
    fullname = "sam.importers.import_{0}".format(importer_name)
    try:
        module = importlib.import_module(fullname)
        instance = module._class()
    except ImportError:
        print("Cannot find importer {0}".format(importer_name))
        instance = None
    except AttributeError:
        traceback.print_exc()
        print("Cannot instantiate importer. Is _class defined?")
        instance = None
    return instance


def create_local_settings(db, sub):
    # create 1 key if none exist
    from sam.models.settings import Settings
    from sam.models.datasources import Datasources
    from sam.models.livekeys import LiveKeys

    m_set = Settings(db, {}, sub)
    ds_id = m_set['datasource']
    m_livekeys = LiveKeys(db, sub)

    # set useful settings for local viewing.
    m_ds = Datasources(db, {}, sub)
    m_ds.set(ds_id, flat='1', ar_active='1', ar_interval=30)

    # create key for uploading securely
    keys = m_livekeys.read()
    if len(keys) == 0:
        m_livekeys.create(ds_id)

    keys = m_livekeys.read()
    key = keys[0]['access_key']
    constants.collector['upload_key'] = key
    return key


def check_database():
    import integrity
    # Validate the database format
    if not integrity.check_and_fix_integrity():
        exit(1)


def launch_whois_service(db, sub):
    import models.nodes
    whois = models.nodes.WhoisService(db, sub)
    whois.start()
    return whois


def launch_localmode(args):
    import server_collector

    # enable local mode
    constants.enable_local_mode()
    import common
    db = common.db_quiet
    sub_id = constants.demo['id']
    check_database()
    access_key = create_local_settings(db, sub_id)

    # launch aggregator process
    aggArgs = args.copy()
    aggArgs.pop('port')
    p_aggregator = multiprocessing.Process(target=launch_aggregator, args=(aggArgs,))
    p_aggregator.start()

    # launch collector process
    #    pipe stdin into the collector
    def spawn_coll(stdin):
        collector = server_collector.Collector()
        collector.run_streamreader(stdin, format=args['format'], access_key=access_key)
    newstdin = os.fdopen(os.dup(sys.stdin.fileno()))
    try:
        p_collector = multiprocessing.Process(target=spawn_coll, args=(newstdin,))
        p_collector.start()
    finally:
        newstdin.close()  # close in the parent

    # launch whois service (if requested)
    if args['whois']:
        print("Starting whois service")
        import models.nodes
        whois_thread = models.nodes.WhoisService(db, sub_id)
        whois_thread.start()
    else:
        whois_thread = None

    # launch webserver locally.
    launch_webserver(args)

    # pressing ctrl-C sends SIGINT to all child processes. The shutdown order is not guaranteed.
    print("joining collector")
    p_collector.join()
    print("collector joined")

    print("joining aggregator")
    p_aggregator.join()
    print("aggregator joined")

    if args['whois']:
        print('joining whois')
        if whois_thread and whois_thread.is_alive():
            whois_thread.shutdown()
            whois_thread.join()
        print('whois joined')


if __name__ == '__main__':
    main(sys.argv)