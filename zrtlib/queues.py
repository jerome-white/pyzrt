import queue
import ctypes
import multiprocessing as mp
from multiprocessing.queues import Queue, JoinableQueue

class JobQueue(JoinableQueue):
    def __init__(self, ledger):
        super().__init__(ctx=mp.get_context())
        self.ledger = ledger

    def task_done(self, key):
        self.ledger.record(key)
        super().task_done()

class WorkQueue(Queue):
    def __init__(self):
        super().__init__(ctx=mp.get_context())
        self.counter = mp.Value(ctypes.c_uint)

    def put(self, obj, block=True, timeout=None):
        with self.counter.get_lock():
            super().put(obj, block, timeout)
            self.counter.value += 1

    def get(self, block=True, timeout=None):
        with self.counter.get_lock():
            if self.counter.value > 0:
                return super().get(block, timeout)
            raise queue.Empty

    def task_done(self):
        with self.counter.get_lock():
            assert(self.counter.value >= 0)
            self.counter.value -= 1

    def empty(self):
        with self.counter.get_lock():
            return self.counter.value == 0
