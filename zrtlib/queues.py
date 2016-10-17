import queue
import ctypes
import multiprocessing as mp
from multiprocessing.queues import Queue, JoinableQueue

class MarkerQueue(JoinableQueue):
    def __init__(self, ledger):
        super().__init__(ctx=mp.get_context())
        self.ledger = ledger

    def mark_done(self, key):
        self.ledger.record(key)
        super().task_done()

class ConsumptionQueue(Queue):
    def __init__(self):
        super().__init__(ctx=mp.get_context())
        self.size = mp.Value(ctypes.c_uint)
        self.barrier = mp.Event()

    def put(self, obj, block=True, timeout=None):
        with self.size.get_lock():
            super().put(obj, block, timeout)
            self.size.value += 1

    def get(self, block=True, timeout=None):
        self.barrier.wait()
        return super().get(block, timeout)

    def release(self):
        for _ in range(self.qsize()):
            self.put(None)
        self.barrier.set()

    def qsize(self):
        with self.size.get_lock():
            return self.size.value
