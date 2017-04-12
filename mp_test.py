import os
import sys
import multiprocessing
import constants
import threading
from pprint import pprint


def printer():
    pprint(constants.collector)

def spawn_coll():
    threading._sleep(2)
    print("SUBPROCESS ALIVE".center(70, '-'))
    printer()
    print("SUBPROCESS DEAD".center(70, '-'))

if __name__ == '__main__2':
    print("MAIN".center(70, '-'))
    printer()

    constants.enable_local_mode()
    #newstdin = os.fdopen(os.dup(sys.stdin.fileno()))
    try:
        #p = multiprocessing.Process(target=spawn_coll, args=(newstdin,))
        p = multiprocessing.Process(target=spawn_coll)
        p.start()
    finally:
        #newstdin.close()  # close in the parent
        pass

    print("MAIN: local enabled".center(70, '-'))
    printer()
    sys.stdout.flush()
    threading._sleep(0.5)
    p.join()
    print("main process ending")


class FileListener(threading.Thread):
    def set_file(self, f):
        self.file = f

    def run(self):
        global SOCKET_BUFFER
        alive = True
        while alive:

    def shutdown(self):
        pass


t1 = FileListener()
t1.set_file(sys.stdin)


if __name__ == '__main__':
    print("MAIN: begun")
    t1.start()
    print("MAIN: thread started. awaiting join")
    t1.join()
    print("MAIN: thread joined. Exiting.")