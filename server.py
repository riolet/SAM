import sys
import os
sys.path.append(os.path.dirname(__file__))  # could be executed from any directory
import constants
import web
web.config.debug = constants.debug  # must preceed import common
import common
import integrity
import models.livekeys
import models.settings
import subprocess
import shlex
import signal

app = web.application(constants.urls, globals())
application = app.wsgifunc()  # for wsgi deployment

live_server = None
live_collector = None
p_tcpdump = None
p_netcat = None

def check_database():
    # Validate the database format
    if not integrity.check_and_fix_integrity():
        exit(1)


def create_session(app):
    # Create the session object
    if web.config.get('_session') is None:
        common.session = web.session.Session(app, common.session_store)
        web.config._session = common.session
    else:
        common.session = web.config._session


def create_upload_key():
    # create 1 key if none exist
    sub_id = constants.demo['id']
    m_set = models.settings.Settings(common.db, common.session, sub_id)
    ds_id = m_set['datasource']
    m_livekeys = models.livekeys.LiveKeys(common.db, sub_id)
    keys = m_livekeys.read()
    if len(keys) == 0:
        m_livekeys.create(ds_id)


def start_live_server():
    global live_server
    args = shlex.split('python live_wsgiserver.py -local 8081')
    try:
        live_server = subprocess.Popen(args, bufsize=-1)
    except OSError as e:
        sys.stderr.write("Error launching live_wsgiserver")
        raise e


def start_live_collector():
    global live_collector
    args = shlex.split('python live_collector.py -local')
    try:
        live_collector = subprocess.Popen(args, bufsize=-1)
    except OSError as e:
        sys.stderr.write("Error launching live_collector")
        raise e


def start_tcpdump():
    # -f (foreign ips are numeric instead of looked up)
    # --list-interfaces  (query for which interface)
    # -i interface
    # --interface=eth0
    # --immediate-mode   (to avoid buffering packets before reporting)
    # -l  (line buffered stdout)
    # -n (do not convert addresses to names)
    # -Q inout   (direction to capture. in|out|inout)
    # -tt  (print unix timestamp on each line)

    # test:
    # sudo tcpdump -i eno1 -f --immediate-mode -l -n -Q inout -tt
    # 1491525737.317942 IP 192.168.10.254.55943 > 239.255.255.250.1900: UDP, length 449
    # 1491525947.515414 STP 802.1d, Config, Flags [none], bridge-id 8000.f8:32:e4:af:0a:a8.8001, length 43
    # 1491525947.915376 ARP, Request who-has 192.168.10.106 tell 192.168.10.254, length 46
    # 1491525948.268015 IP 192.168.10.113.33060 > 172.217.3.196.443: Flags [P.], seq 256:730, ack 116, win 3818, options [nop,nop,TS val 71847613 ecr 4161606244], length 474
    #
    global p_tcpdump
    global p_netcat
    # args = shlex.split('tcpdump -i eno1 -f --immediate-mode -l -n -Q inout -tt > /dev/udp/localhost/8082')
    args_tcpdump = shlex.split('tcpdump -i eno1 -f --immediate-mode -l -n -Q inout -tt')
    args_nc = shlex.split('nc -u localhost 8082')
    try:
        p_tcpdump = subprocess.Popen(args_tcpdump, bufsize=-1, stdout=subprocess.PIPE)
        p_netcat = subprocess.Popen(args_nc, bufsize=-1, stdin=p_tcpdump.stdout)
    except OSError as e:
        sys.stderr.write("Error launching tcpdump. Is it installed?\n\tapt-get install tcpdump")
        raise e


def start_local():
    # setup environment to use sqlite
    constants.enable_local_mode()
    reload(common)
    check_database()
    create_session(app)
    # also: need access key for local
    create_upload_key()
    try:
        # Need running programs:
        #   live_wsgiserver application to import data into the database
        start_live_server()
        #   live_collector application to translate the data (using import_tcpdump
        start_live_collector()
        #   tcpdump to collect data and feed it through a pipe.
        start_tcpdump()
        #   server.py (this file) to deliver the webserver
        if len(sys.argv) >= 3:
            sys.argv[1] = sys.argv[2]
        else:
            sys.argv[1] = '8080'
        app.run()
    finally:
        print("{} shutting down.".format(sys.argv[0]))
        if p_tcpdump is not None:
            os.kill(p_tcpdump.pid, signal.SIGINT)
            p_tcpdump.wait()
            os.kill(p_netcat.pid, signal.SIGINT)
            p_tcpdump.wait()
        if live_collector is not None:
            os.kill(live_collector.pid, signal.SIGINT)
            live_collector.wait()
        if live_server is not None:
            os.kill(live_server.pid, signal.SIGINT)
            live_server.wait()


def start_server():
    check_database()
    create_session(app)
    app.run()


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == '-local':
        print('Starting local server')
        start_local()
    else:
        print('Starting dev server')
        start_server()
