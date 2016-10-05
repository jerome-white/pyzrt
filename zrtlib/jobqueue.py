from collections import namedtuple
from multiprocessing import get_context
from multiprocessing.queues import JoinableQueue

Job = namedtuple('Job', 'key, indices, weight, dp')

class JobQueue(JoinableQueue):
    def __init__(self, ledger):
        super().__init__(ctx=get_context())
        self.ledger = ledger

    def task_done(self, key):
        self.ledger.record(key)
        super().task_done()
