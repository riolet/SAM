import os
import sys
import logging
import signal
import threading
import time
import subprocess
import shlex
import requests
import cPickle
from sam import constants
import sam.importers.import_base as base_importer
from sam.importers import import_netflow
logger = logging.getLogger(__name__)

"""
Netflow-specific Collector
-----------

* runs client-side.
* spawns a nfcapd process to listen for netflow data on the given port
* watches for complete log files from nfcapd, and spawns nfdump to translate them to text
* periodically opens an SSL connection to the aggregator to send accumulated messages

"""


class Collector(object):
    def __init__(self):
        self.target_address = constants.collector['target_address']
        self.access_key = constants.collector['upload_key']
        self.default_format = constants.collector['format']
        self.port = int(constants.collector['listen_port'])
        self.transmit_buffer = []
        self.transmit_buffer_size = 0
        self.transmit_buffer_threshold = 500  # push the transmit buffer to the database server if it reaches this many entries.
        self.time_between_imports = 1  # seconds. Period for translating lines from SOCKET to TRANSMIT buffers
        self.time_between_transmits = 10  # seconds. Period for transmitting to the database server.
        self.nfcapd_process = None
        self.shutdown_event = threading.Event()
        self.importer = import_netflow.NetFlowImporter()
        self.nfcapd_folder = '/tmp/sam_netflow'

    def form_connection(self, sleep=1.0, max_tries=10):
        attempts = 1
        connected = self.test_connection()
        while not connected and attempts < max_tries:
            time.sleep(sleep)
            connected = self.test_connection()
            attempts += 1
        return connected

    def run(self, port=None, access_key=None):
        """
        Entry point for collector process
        :param port:
        :param access_key:
        :return:
        """
        # set up the importer
        if port is not None:
            try:
                self.port = int(port)
            except (ValueError, TypeError) as e:
                logger.critical('Collector: Invalid port: {}'.format(e))
                return
        if access_key is not None:
            self.access_key = access_key

        # test the connection
        if not self.form_connection():
            logger.critical('Collector: Failed to connect to aggregator; aborting')
            return

        # register signals for safe shut down
        def sig_handler(num, frame):
            logger.debug('\nInterrupt received.')
            self.shutdown()
        signal.signal(signal.SIGINT, sig_handler)

        self.launch_nfcapd(self.port)
        logger.info("Live Collector listening on port {0}.".format(self.port))

        try:
            self.thread_batch_processor()
        except:
            logger.exception("Live_collector server has encountered a critical error.")
            self.shutdown()

        logger.info("Live_collector server shut down successfully.")

    def launch_nfcapd(self, port):
        # a temp directory to write out netflow files to
        if not os.path.exists(self.nfcapd_folder):
            os.makedirs(self.nfcapd_folder)

        # start the nfcapd subprocess to listen to port and write out to a temp directory.
        args = shlex.split('nfcapd -T all -l {0} -p {1}'.format(self.nfcapd_folder, port))
        try:
            self.nfcapd_process = subprocess.Popen(args, bufsize=-1)
        except OSError as e:
            sys.stderr.write("To use this importer, please install nfdump.\n\t`apt-get install nfdump`\n")
            raise e

    def thread_batch_processor(self):
        # loop:
        #    wait for event, with timeout
        #    check bufferSize
        #       conditionally swap buffers and do processing.

        last_processing = time.time()  # time.time() is in floating point seconds
        alive = True
        while alive:
            triggered = self.shutdown_event.wait(self.time_between_imports)
            if triggered:
                alive = False

            deltatime = time.time() - last_processing
            # Buffer full. Processing.
            if self.transmit_buffer_size > self.transmit_buffer_threshold:
                logger.debug("COLLECTOR: process server running batch (due to buffer cap reached)")
                self.transmit_lines()
                last_processing = time.time()
            # Time's up. Processing.
            elif deltatime > self.time_between_transmits and self.transmit_buffer_size > 0:
                logger.debug("COLLECTOR: process server running batch (due to time)")
                self.transmit_lines()
                last_processing = time.time()
            # Stuff is in there, but the buffer's not full and time isn't up. Not processing.
            elif self.transmit_buffer_size > 0:
                logger.debug("COLLECTOR: waiting for time limit or a full buffer. "
                      "Time at {0:.1f}, Size at {1}".format(deltatime, self.transmit_buffer_size))
            # buffer is empty. Waiting...
            else:
                # Don't let time accumulate while the buffer is empty
                last_processing = time.time()

            # import lines in memory buffer:
            if self.new_capture_exists():
                self.decode_captures()

        logger.info("COLLECTOR: process server shutting down")

    def new_capture_exists(self):
        if not os.path.exists(self.nfcapd_folder):
            return False
        files = os.listdir(self.nfcapd_folder)
        return any(["current" not in f for f in files if f.startswith("nfcapd")])

    def decode_captures(self):
        files = os.listdir(self.nfcapd_folder)
        files_to_import = [os.path.join(self.nfcapd_folder, f) for f in files if f.startswith("nfcapd") and "current" not in f]

        for file_path in files_to_import:
            try:
                translated = []
                lines = self.decode_netflow_file(file_path)
                for line in lines:
                    translated_line = {}
                    success = self.importer.translate(line.strip(), 1, translated_line)
                    if success == 0:
                        translated.append(translated_line)

                # insert translations into TRANSMIT_BUFFER
                headers = base_importer.BaseImporter.keys
                for line in translated:
                    list_line = [line[header] for header in headers]
                    self.transmit_buffer.append(list_line)

                # update TRANSMIT_BUFFER size
                self.transmit_buffer_size = len(self.transmit_buffer)

                # delete the completed file
                os.remove(file_path)
            except Exception as e:
                logger.warn("Failed to import file {} -- ({})".format(file_path, e))

    def decode_netflow_file(self, path):
        if not os.path.exists(path):
            raise ValueError("File not found: {}".format(path))

        nf_format = import_netflow.NetFlowImporter.FORMAT
        args = shlex.split('nfdump -r {0} -b -o {1}'.format(path, nf_format))
        try:
            proc = subprocess.Popen(args, bufsize=-1, stdout=subprocess.PIPE)
        except OSError as e:
            sys.stderr.write("To use this importer, please install nfdump.\n\t`apt-get install nfdump`\n")
            raise e

        all_data = proc.stdout.readlines(1000)

        # pass through anything else and close the process
        proc.poll()
        while proc.returncode is None:
            extra = proc.stdout.readline()
            if extra:
                logger.warn("Data was dropped during nfdump")
            proc.poll()
        proc.wait()
        return all_data

    def transmit_lines(self):
        access_key = self.access_key
        version = "1.0"
        headers = base_importer.BaseImporter.keys
        lines = self.transmit_buffer
        self.transmit_buffer = []
        self.transmit_buffer_size = 0
        package = {
            'access_key': access_key,
            'version': version,
            'headers': headers,
            'lines': lines
        }

        logger.info("COLLECTOR: Sending package...")
        try:
            response = requests.request('POST', self.target_address, data=cPickle.dumps(package))
            reply = response.content
            logger.debug("COLLECTOR: Received reply: {0}".format(reply))
        except Exception as e:
            reply = 'error'
            logger.error("COLLECTOR: Error sending package: {0}".format(e))
            # keep the unsent lines around
            self.transmit_buffer.extend(lines)
            self.transmit_buffer_size = len(self.transmit_buffer)
        return reply

    def test_connection(self):
        package = {
            'access_key': self.access_key,
            'version': '1.0',
            'headers': base_importer.BaseImporter.keys,
            'msg': 'handshake',
            'lines': []
        }
        try:
            response = requests.request('POST', self.target_address, data=cPickle.dumps(package))
            reply = response.content
        except Exception as e:
            logger.error("Collector: Testing connection...Failed")
            return False
        if reply == 'handshake':
            logger.info("Collector: Testing connection...Succeeded")
            return True
        else:
            reply.replace('\r', '').replace('\n', '')
            if len(reply) > 50:
                logger.error("Error: {}...".format(reply[:50]))
            else:
                logger.error("Error: {}".format(reply))
            return False

    def shutdown(self):
        logger.info("Collector: Shutting down nfcapd.")
        if (self.nfcapd_process is not None):
            self.nfcapd_process.send_signal(signal.SIGINT)
            self.nfcapd_process.wait()
        logger.info("Collector: Shutting down nfdump.")
        self.shutdown_event.set()


if __name__ == "__main__":
    c = Collector()
    c.run()
