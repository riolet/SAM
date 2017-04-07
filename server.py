import sys
import os
sys.path.append(os.path.dirname(__file__))
import constants
import web
web.config.debug = constants.debug
import common
import integrity

# Validate the database format
if not integrity.check_and_fix_integrity():
    exit(1)

# Create the session object
app = web.application(constants.urls, globals())
if web.config.get('_session') is None:
    common.session = web.session.Session(app, common.session_store)
    web.config._session = common.session
else:
    common.session = web.config._session


def spawn_tcpdump():
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
    # 1491525947.515414 STP 802.1d, Config, Flags [none], bridge-id 8000.f8:32:e4:af:0a:a8.8001, length 43
    # 1491525947.915376 ARP, Request who-has 192.168.10.106 tell 192.168.10.254, length 46
    # 1491525948.268015 IP 192.168.10.113.33060 > 172.217.3.196.443: Flags [P.], seq 256:730, ack 116, win 3818, options [nop,nop,TS val 71847613 ecr 4161606244], length 474
    #



    pass


if __name__ == "__main__":
    # setup environment to use sqlite
    # also: need access key for local 
    # Need running programs:
    #   tcpdump to collect data and feed it through a pipe.
    #   live_collector application to translate the data (using import_tcpdump
    #   live_wsgiserver application to import data into the database
    #   server.py (this file) to deliver the webserver
    app.run()
