import sys
import os
sys.path.append(os.path.dirname(__file__))  # this could be executed from any directory
import getopt
import constants
import multiprocessing
import time

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

# args:
#   --target=(webserver|aggregator|collector)
#   --scanner=(tcpdump|tshark|none)
#   --local
#   --wsgi


def launcher(argv):
    kwargs, args = getopt.getopt(argv[1:], '', ['format=', 'port=', 'target=', 'local', 'whois', 'wsgi'])

    defaults = {
        'format': 'tcpdump',
        'port': None,
        'target': 'webserver',
        'local': False,
        'whois': False,
        'wsgi': False,
    }
    valid_formats = ['tcpdump', 'tshark', 'none']
    valid_targets = ['aggregator', 'collector', 'webserver']

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

    if parsed_args['format'] not in valid_formats:
        print("Invalid scanner")
        sys.exit(1)
    if parsed_args['target'] not in valid_targets:
        print("Invalid target")
        sys.exit(1)

    if parsed_args['local']:
        launch_localmode(parsed_args)
    elif parsed_args['target'] == 'webserver':
        launch_webserver(parsed_args)
    elif parsed_args['target'] == 'collector':
        launch_collector(parsed_args)
    elif parsed_args['target'] == 'aggregator':
        launch_aggregator(parsed_args)
    else:
        print("Error determining what to launch.")


def launch_webserver(args):
    import server_webserver
    if args['wsgi']:
        print('launching wsgi webserver')
        global application
        application = server_webserver.start_wsgi()
    else:
        port = args['port']
        if port is None:
            port = constants.webserver['listen_port']
        print('launching dev webserver on {}'.format(port))
        server_webserver.start_server(port=port)
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


def create_upload_key():
    # create 1 key if none exist
    import models.settings
    import models.livekeys
    import common

    sub_id = constants.demo['id']
    m_set = models.settings.Settings(common.db_quiet, {}, sub_id)
    ds_id = m_set['datasource']
    m_livekeys = models.livekeys.LiveKeys(common.db_quiet, sub_id)
    keys = m_livekeys.read()
    if len(keys) == 0:
        m_livekeys.create(ds_id)

    keys = m_livekeys.read()
    key = keys[0]['access_key']
    constants.collector['upload_key'] = key
    return key

def launch_localmode(args):
    import server_collector
    # enable local mode
    constants.enable_local_mode()
    access_key = create_upload_key()
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


    # launch webserver locally.
    launch_webserver(args)

    # pressing ctrl-C sends SIGINT to all child processes. The shutdown order is not guaranteed.
    print("joining collector")
    p_collector.join()
    print("collector joined")

    print("joining aggregator")
    p_aggregator.join()
    print("aggregator joined")


if __name__ == '__main__':
    launcher(sys.argv)