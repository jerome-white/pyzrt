from collections import namedtuple
from multiprocessing import JoinableQueue

Job = namedtuple('Job', 'key, indices, weight, dp')

class JobQueue(JoinableQueue):
    def __init__(self, ledger):
        super().__init__()
        self.ledger = ledger

    def task_done(self, key):
        self.ledger.record(key)
        super().task_done()
