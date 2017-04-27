import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
import time
import cPickle
from sam import constants
import web
from sam import common
import threading
import sam.models.livekeys
import sam.models.nodes
from sam import preprocess
import sam.importers.import_base


"""
Live Server
-----------

* runs server-side.
* listens for uploaded log lines
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
        # type: (int, int, [str]) -> None
        buff = self.buffers.get(sub, {}).get(ds)
        if not buff:
            self.create(sub, ds)
            buff = self.buffers.get(sub, {}).get(ds)
        with buff.lock:
            buff.add(message)

    def remove(self, sub, ds):
        # type: (int, int) -> None
        sub_buffer = self.buffers.get(sub)
        if sub_buffer:
            if ds in sub_buffer:
                del sub_buffer[ds]
            if not sub_buffer:
                del self.buffers[sub]

    def get_all(self):
        # type: () -> [Buffer]
        buffers = [v for sub in self.buffers.keys() for v in self.buffers[sub].values()]
        return buffers

    def yank(self, sub, ds):
        buff = self.buffers.get(sub, {})[ds]
        with buff.lock:
            lines = buff.pop_all()
        return lines


class DatabaseInserter(threading.Thread):
    SIZE_QUOTA = 1000  # log lines.  When the syslog has this many entries, process it.
    TIME_QUOTA = 20  # seconds. Process a partially-filled syslog with this period.
    CYCLE_SLEEP = 1  # seconds. sleep period between buffer-checking cycles

    def __init__(self, buffers):
        threading.Thread.__init__(self)
        # type: (MemoryBuffers) -> None
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
                # import any lines into Syslog
                self.buffer_to_syslog(buff)

                processor = preprocess.Preprocessor(common.db_quiet, buff.sub, buff.ds)
                rows = processor.count_syslog()

                if rows >= self.SIZE_QUOTA:
                    # process the buffer
                    print("PREPROCESSOR: exceeded size quota")
                    self.syslog_to_tables(buff)
                    buff.flag_unexpired()
                elif time.time() > buff.last_proc_time + self.TIME_QUOTA:
                    print("PREPROCESSOR: exceeded time quota")
                    if rows > 0:
                        # process the buffer
                        self.syslog_to_tables(buff)
                        buff.flag_unexpired()
                    else:
                        if buff.expiring:
                            # remove the buffer from the buffer list
                            print("PREPROCESSOR: removing {0}: {1}".format(buff.sub, buff.ds))
                            self.buffers.remove(buff.sub, buff.ds)
                        else:
                            # flag the buffer as inactive for future removal
                            print("PREPROCESSOR: flagging for removal {0}: {1}".format(buff.sub, buff.ds))
                            buff.flag_expired()
                else:
                    # rows are under quota, and time is not up. Move on
                    pass

    def shutdown(self):
        self.e_shutdown.set()

    @staticmethod
    def run_importer(sub, ds, messages):
        importer = sam.importers.import_base.BaseImporter()
        importer.set_subscription(sub)
        importer.set_datasource(ds)

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
        print("PREPROCESSOR: running syslog to tables for {0}: {1}".format(sub_id, ds))
        processor = preprocess.Preprocessor(common.db_quiet, sub_id, ds)
        processor.run_all()

    def buffer_to_syslog(self, buff):
        sub_id = buff.sub
        ds_id = buff.ds
        lines = self.buffers.yank(sub_id, ds_id)
        DatabaseInserter.run_importer(sub_id, ds_id, lines)

    def syslog_to_tables(self, buff):
        sub = buff.sub
        ds = buff.ds
        buff.last_proc_time = time.time()
        DatabaseInserter.run_preprocessor(sub, ds)

class Aggregator(object):
    @staticmethod
    def handle(rawdata):
        # print("SERVER: Handling input!")
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
        # print("SERVER: validating...")
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

        key_model = sam.models.livekeys.LiveKeys(common.db_quiet, 0)
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
        print("SERVER: Received input.")
        BUFFERS.add(sub, ds, data)
        buffers = BUFFERS.get_all()
        #print("SERVER: Number of Buffers = {0}".format(len(buffers)))
        #print("SERVER: Buffer[0] = {0}".format(buffers[0]))
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
    if port == None:
        port = constants.aggregator['listen_port']

    urls = ['/', 'Aggregator']
    app = web.application(urls, globals(), autoreload=False)
    try:
        runwsgi(app.wsgifunc(), port)
    finally:
        print("{} shutting down.".format(sys.argv[0]))


def runwsgi(func, port):
    server_addr = web.validip(port)
    return web.httpserver.runsimple(func, server_addr)


def start_wsgi():
    global application
    urls = ['/', 'Aggregator']
    app = web.application(urls, globals())
    return app.wsgifunc()


# buffer to pass data between threads
BUFFERS = MemoryBuffers()
# to persist the thread reference between invocations
IMPORTER_THREAD = None

application = start_wsgi()
