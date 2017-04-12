import sys
import os
sys.path.append(os.path.dirname(__file__))  # this could be executed from any directory
import getopt
import constants

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
        print("launching wsgi webserver")
        global application
        application = server_webserver.start_wsgi()
    else:
        port = args['port']
        if port is None:
            port = constants.webserver['listen_port']
        print('launching dev webserver on {}'.format(port))
        server_webserver.start_server(port=port)


def launch_collector(args):
    import server_collector
    port = args['port']
    if port is None:
        port = constants.collector['listen_port']
    print('launching collector on {}'.format(args['port']))
    collector = server_collector.Collector()
    collector.run(port=args['port'], format=args['format'])


def launch_aggregator(args):
    import server_aggregator
    if args['wsgi']:
        print("launching wsgi aggregator")
        global application
        application = server_aggregator.start_wsgi()
    else:
        port = args['port']
        if port is None:
            port = constants.aggregator['listen_port']
        print('launching dev aggregator on {}'.format(port))
        server_aggregator.start_server(port=port)


def launch_localmode(args):
    pass

if __name__ == '__main__':
    launcher(sys.argv)