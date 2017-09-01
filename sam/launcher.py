import sys
import os
import getopt
import multiprocessing
import logging
sys.path.append(os.path.join(os.path.dirname(__file__), os.path.pardir))  # this could be executed from any directory
from sam import constants

logger = logging.getLogger(__name__)
logging.basicConfig(level=constants.log_level)
application = None

VALID_ARGS = ['format=', 'port=', 'target=', 'dest=', 'sub=', 'local', 'whois', 'wsgi']
VALID_TARGETS = ['local', 'aggregator', 'collector', 'collector_stream',
                 'webserver', 'import', 'test_dummy']

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
#     --local --format=tcpdump
#   import
#     --target=import  --format=palo_alto

# suggested demo invocation:
# sudo tcpdump -i any -f --immediate-mode -l -n -Q inout -tt | python launcher.py --local --whois --format=tcpdump


def main(argv=None):
    if argv is None:
        argv = sys.argv

    try:
        parsed_args, args = parse_args(argv)
    except getopt.GetoptError as e:
        logger.critical("Invalid option specified.")
        logger.critical(e)
        return 1

    constants.use_whois = parsed_args['whois']
    target = parsed_args['target']

    if target not in VALID_TARGETS:
        logger.critical("Invalid target")
        return 2
    try:
        {'local': launch_localmode,
         'webserver': launch_webserver,
         'collector': launch_collector,
         'collector_stream': launch_collector_stream,
         'aggregator': launch_aggregator,
         'import': launch_importer
         }[target](parsed_args, args)
    except:
        return 3
    return 0


def parse_args(argv):
    kwargs, args = getopt.getopt(argv[1:], '', VALID_ARGS)

    parsed_args = {
        'format': None,
        'port': None,
        'target': 'webserver',
        'whois': False,
        'wsgi': False,
        'dest': 'default',
        'sub': None
    }

    for key, val in kwargs:
        if key == '--local':
            parsed_args['target'] = 'local'
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
    return parsed_args, args


def launch_webserver(parsed, args):
    import sam.server_webserver
    if parsed.get('wsgi', False):
        logger.info('launching wsgi webserver')
        global application
        application = sam.server_webserver.start_wsgi()
    else:
        if constants.access_control['local_tls']:
            from web.wsgiserver import CherryPyWSGIServer
            CherryPyWSGIServer.ssl_certificate = constants.access_control['local_tls_cert']
            CherryPyWSGIServer.ssl_private_key = constants.access_control['local_tls_key']

        port = parsed.get('port', None)
        if port is None:
            port = constants.webserver['listen_port']
        logger.info('launching dev webserver on {}'.format(port))
        sam.server_webserver.start_server(port=port)
        logger.info('webserver shut down.')


def launch_collector(parsed, args):
    import server_collector
    port = parsed.get('port', None)
    if port is None:
        port = constants.collector['listen_port']
    logger.info('launching collector on {}'.format(port))
    collector = server_collector.Collector()
    if parsed['format'] is None:
        parsed['format'] = constants.collector['format']
    collector.run(port=port, format=parsed['format'])
    logger.info('collector shut down.')
    return collector


def launch_collector_stream(parsed, args):
    import server_collector
    logger.info('launching stdin collector')
    collector = server_collector.Collector()
    if parsed['format'] is None:
        parsed['format'] = constants.collector['format']
    collector.run_streamreader(sys.stdin, format=parsed['format'])
    logger.info('collector shut down.')
    return collector


def launch_aggregator(parsed, args):
    import server_aggregator
    global application
    if parsed['wsgi']:
        logger.info("launching wsgi aggregator")
        application = server_aggregator.start_wsgi()
    else:
        port = parsed.get('port', None)
        if port is None:
            port = constants.aggregator['listen_port']
        logger.info('launching dev aggregator on {}'.format(port))
        server_aggregator.start_server(port=port)
        logger.info('aggregator shut down.')


def launch_importer(parsed, args):
    import common
    import sam.importers.import_base
    import sam.models.subscriptions
    common.load_plugins()
    datasource = parsed['dest']

    sub_model = sam.models.subscriptions.Subscriptions(common.db_quiet)
    subscription_id = sub_model.decode_sub(parsed['sub'])
    log_format = parsed['format']

    if len(args) != 1:
        logger.error("Please specify one source file. Exiting.")
        return 4

    try:
        ds_id = int(datasource)
    except (TypeError, ValueError):
        try:
            from sam.models.datasources import Datasources
            d_model = Datasources(common.db_quiet, {}, subscription_id)
            ds_id = d_model.name_to_id(datasource)
        except:
            logger.error('Please specify a datasource. "--dest=???". Exiting.')
            return 5
    if not ds_id:
        logger.error('Please specify a datasource. "--dest=???". Exiting.')
        return 6
    importer = sam.importers.import_base.get_importer(log_format, subscription_id, ds_id)
    if not importer:
        logger.error("Could not find importer for given format. ({})".format(log_format))
        return 7
    if importer.validate_file(args[0]):
        importer.import_file(args[0])
    else:
        logger.error("Could not open source file. Exiting.")
        return 8

    from sam.preprocess import Preprocessor
    processor = Preprocessor(common.db_quiet, subscription_id, ds_id)
    processor.run_all()
    return processor


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


def launch_localmode(parsed, args):
    import server_collector

    # enable local mode
    constants.enable_local_mode()
    import common
    import sam.models.subscriptions
    db = common.db_quiet
    check_database()
    sub_model = sam.models.subscriptions.Subscriptions(db)
    sub_id = sub_model.decode_sub(parsed['sub'])
    access_key = create_local_settings(db, sub_id)

    # launch aggregator process
    agg_args = parsed.copy()
    agg_args.pop('port', None)
    p_aggregator = multiprocessing.Process(target=launch_aggregator, args=(agg_args, []))
    p_aggregator.start()

    # launch collector process
    #    pipe stdin into the collector
    def spawn_coll(stdin):
        collector = server_collector.Collector()
        if parsed['format'] is None:
            parsed['format'] = constants.collector['format']
        collector.run_streamreader(stdin, format=parsed['format'], access_key=access_key)

    new_stdin = os.fdopen(os.dup(sys.stdin.fileno()))
    try:
        p_collector = multiprocessing.Process(target=spawn_coll, args=(new_stdin,))
        p_collector.start()
    finally:
        new_stdin.close()  # close in the parent (still open in child proc)

    # launch whois service (if requested)
    if parsed['whois']:
        logger.info("Starting whois service")
        import models.nodes
        whois_thread = models.nodes.WhoisService(db, sub_id)
        whois_thread.start()
    else:
        whois_thread = None

    # launch webserver locally.
    launch_webserver(parsed, args)

    # pressing ctrl-C sends SIGINT to all child processes. The shutdown order is not guaranteed.
    logger.debug("joining collector")
    p_collector.join()
    logger.debug("collector joined")

    logger.debug("joining aggregator")
    p_aggregator.join()
    logger.debug("aggregator joined")

    if parsed['whois']:
        logger.debug('joining whois')
        if whois_thread:
            if whois_thread.is_alive():
                whois_thread.shutdown()
            whois_thread.join()
        logger.debug('whois joined')
    logger.info("SAM can be safely shut down.")


def testing_entrypoint(environment, argv):
    os.environ.update(environment)
    # Reloading constants rereads the environment variables again.
    # Otherwise stale values would be used.
    reload(constants)
    constants.init_urls()

    main(argv=argv)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
