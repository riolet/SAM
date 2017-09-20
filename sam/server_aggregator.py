import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
import logging
import time
import cPickle
import threading
import traceback
from sam import constants
import web
import sam.common
import sam.models.livekeys
import sam.models.nodes
import sam.importers.import_base
import sam.preprocess
import sam.httpserver
logger = logging.getLogger(__name__)

"""
Live Server
-----------

* runs server-side.
* listens for uploaded log lines
* authenticates traffic
* inserts those lines into a database buffer
* periodically processes the buffer into viewable data

"""


class Buffer:
    def __init__(self, sub, ds):
        self.sub = sub
        self.ds = ds
        self.messages = []
        self.last_proc_time = time.time()
        self.expiring = False
        self.lock = threading.Lock()

    def pop_all(self):
        messages = self.messages
        self.messages = []
        return messages

    def add(self, message):
        self.messages.append(message)
        self.expiring = False

    def flag_expired(self):
        self.expiring = True
        self.last_proc_time = time.time()

    def flag_unexpired(self):
        self.expiring = False

    def __len__(self):
        return len(self.messages)

    def __str__(self):
        return "{0}-{1}-{2}".format(self.sub, self.ds, len(self.messages))

    def __repr__(self):
        return str(self)


class MemoryBuffers:
    def __init__(self):
        # each buffer needs a sub, ds, list-of-lines, and last_empty_time
        self.buffers = {}
        """:type buffers: dict[ int, dict[ int, Buffer]]"""

    def create(self, sub, ds):
        sub_buffers = self.buffers.get(sub, {})
        sub_buffers[ds] = Buffer(sub, ds)
        self.buffers[sub] = sub_buffers

    def add(self, sub, ds, message):
        """
        :type sub: int
        :type ds: int
        :type message: any
        :rtype: None
        """
        buff = self.buffers.get(sub, {}).get(ds)
        if buff is None:
            self.create(sub, ds)
            buff = self.buffers.get(sub, {}).get(ds)
        with buff.lock:
            buff.add(message)

    def remove(self, sub, ds):
        """
        :type sub: int
        :type ds: int
        :rtype: None
        """
        sub_buffer = self.buffers.get(sub)
        if sub_buffer is not None:
            if ds in sub_buffer:
                del sub_buffer[ds]
            if len(sub_buffer) == 0:
                del self.buffers[sub]

    def get_all(self):
        """
        :rtype: list [ Buffer ]
        """
        buffers = [self.buffers[subid][dsid] for subid in sorted(self.buffers.keys()) for dsid in sorted(self.buffers[subid].keys())]
        return buffers

    def yank(self, sub, ds):
        """
        :type sub: int
        :type ds: int
        :rtype: list
        """
        buff = self.buffers.get(sub, {}).get(ds)
        if buff:
            with buff.lock:
                lines = buff.pop_all()
            return lines
        else:
            return []


class DatabaseInserter(threading.Thread):
    SIZE_QUOTA = 1000  # log lines.  When the syslog has this many entries, process it.
    TIME_QUOTA = 20  # seconds. Process a partially-filled syslog with this period.
    CYCLE_SLEEP = 1  # seconds. sleep period between buffer-checking cycles

    def __init__(self, buffers):
        """
        :type buffers: MemoryBuffers
        """
        threading.Thread.__init__(self)
        self.buffers = buffers
        self.alive = True
        self.e_shutdown = threading.Event()

    def run(self):
        while self.alive:
            # sleep, but watch for shutdown requests
            triggered = self.e_shutdown.wait(self.CYCLE_SLEEP)
            if triggered:
                self.alive = False

            buffers = self.buffers.get_all()
            for buff in buffers:
                self.buffer_to_syslog(buff)
                self.process_buffer(buff)

    def process_buffer(self, buff):
        """
        :type buff: Buffer
        :rtype: int
        """
        sub_id = buff.sub
        ds_id = buff.ds
        processor = sam.preprocess.Preprocessor(sam.common.db_quiet, sub_id, ds_id)
        rows = processor.count_syslog()
        time_expired = time.time() > buff.last_proc_time + self.TIME_QUOTA
        rcode = 0

        if rows >= self.SIZE_QUOTA:
            # buffer full: process the buffer
            logger.debug("PREPROCESSOR: exceeded size quota")
            self.syslog_to_tables(buff)
            rcode = 1
        elif time_expired and rows > 0:
            # time's up: process the buffer
            logger.debug("PREPROCESSOR: exceeded time quota")
            self.syslog_to_tables(buff)
            rcode = 2
        elif time_expired and buff.expiring:
            # buffer has been flagged for removal. Remove it.
            logger.debug("PREPROCESSOR: removing {0}: {1}".format(buff.sub, buff.ds))
            self.buffers.remove(buff.sub, buff.ds)
            rcode = 3
        elif rows == 0 and time_expired:
            # buffer is empty and time has expired. Flag it for removal next time.
            logger.debug("PREPROCESSOR: flagging for removal {0}: {1}".format(buff.sub, buff.ds))
            buff.flag_expired()
            rcode = 4
        else:
            # time not expired and rows are under quota
            rcode = 5
        return rcode

    def shutdown(self):
        self.e_shutdown.set()

    @staticmethod
    def run_importer(sub_id, ds_id, messages):
        importer = sam.importers.import_base.BaseImporter()
        importer.set_subscription(sub_id)
        importer.set_datasource_id(ds_id)

        for msg in messages:
            lines = msg['lines']
            headers = msg['headers']
            # lines is a list of rows, where each row is a list of values
            # headers is a list of column names
            # rows is a list of dictionaries where each dictionary is the headers applied to that row of data
            rows = [{headers[i]: v for i, v in enumerate(row)} for row in lines]
            importer.insert_data(rows, len(lines))

    @staticmethod
    def run_preprocessor(sub_id, ds):
        logger.debug("PREPROCESSOR: running syslog to tables for {0}: {1}".format(sub_id, ds))
        processor = sam.preprocess.Preprocessor(sam.common.db_quiet, sub_id, ds)
        processor.run_all()

    def buffer_to_syslog(self, buff):
        """
        Immediately ingest the contents of this buffer into the syslog table.

        :type buff: Buffer
        """
        sub_id = buff.sub
        ds_id = buff.ds
        lines = buff.pop_all()
        DatabaseInserter.run_importer(sub_id, ds_id, lines)

    def syslog_to_tables(self, buff):
        """
        Immediately process the contents of this buffer's syslog table into the links table.

        :type buff: Buffer
        """
        sub = buff.sub
        ds = buff.ds
        buff.last_proc_time = time.time()
        buff.flag_unexpired()
        DatabaseInserter.run_preprocessor(sub, ds)


class Aggregator(object):
    @staticmethod
    def handle(rawdata):
        # logger.debug("SERVER: Handling input!")
        try:
            data = cPickle.loads(rawdata)
        except:
            return 'failed: could not unpickle data.'

        if not data:
            return 'failed: no data received.'

        errors = Aggregator.socket_to_buffer(data)

        if errors == 'handshake':
            return 'handshake'
        elif errors:
            return 'failed: {0}'.format(errors)
        else:
            return 'success'

    @staticmethod
    def validate_data(data):
        # logger.debug("SERVER: validating...")
        if type(data) is not dict:
            return {}, "Cannot interpret data."
        access_key = data.pop('access_key', None)
        if not access_key:
            return {}, 'No access key. Access Denied'
        version = data.pop('version', None)
        if not version:
            return {}, 'Version absent. Access Denied'
        if version != "1.0":
            return {}, 'Version not compatible. Recieved {0}, expected {1}. Access Denied'.format(version, '1.0')

        key_model = sam.models.livekeys.LiveKeys(sam.common.db_quiet, 0)
        access = key_model.validate(access_key)
        return access, ''

    @staticmethod
    def socket_to_buffer(data):
        global BUFFERS

        access, error = Aggregator.validate_data(data)
        if error:
            return error
        if not access:
            return "Not Authorized"

        sub = access['subscription']
        ds = access['datasource']

        # It may have just been a handshake.
        if 'msg' in data:
            if data['msg'] == 'handshake':
                return 'handshake'

        # read lines/etc
        # insert lines into buffer
        logger.info("SERVER: Received input.")
        BUFFERS.add(sub, ds, data)
        # buffers = BUFFERS.get_all()
        # logger.debug("SERVER: Number of Buffers = {0}".format(len(buffers)))
        # logger.debug("SERVER: Buffer[0] = {0}".format(buffers[0]))
        return False

    @staticmethod
    def ensure_processing_thread():
        global IMPORTER_THREAD

        if IMPORTER_THREAD is None or IMPORTER_THREAD.is_alive is False:
            IMPORTER_THREAD = DatabaseInserter(BUFFERS)
            IMPORTER_THREAD.daemon = True
            IMPORTER_THREAD.start()

    def POST(self):
        response = Aggregator.handle(web.data())
        Aggregator.ensure_processing_thread()
        return response


def start_server(port=None):
    sam.common.load_plugins()

    if port is None:
        port = constants.aggregator['listen_port']

    urls = ['/', 'Aggregator']
    app = web.application(urls, globals(), autoreload=False)
    try:
        sam.httpserver.runwsgi(app.wsgifunc(sam.httpserver.PluginStaticMiddleware), port)
    finally:
        logger.info("{} shutting down.".format(sys.argv[0]))


def start_wsgi():
    global application
    sam.common.load_plugins()
    urls = ['/', 'Aggregator']
    app = web.application(urls, globals())
    return app.wsgifunc(sam.httpserver.PluginStaticMiddleware)


# buffer to pass data between threads
BUFFERS = MemoryBuffers()
# to persist the thread reference between invocations
IMPORTER_THREAD = None

application = start_wsgi()
