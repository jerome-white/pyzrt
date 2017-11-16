class JobQueue:
    def __init__(self, incoming, outgoing, jobs):
        self.incoming = incoming
        self.outgoing = outgoing
        self.job_count = 0

        for i in jobs:
            self.outgoing.put(i)
            self.job_count += 1

    def __iter__(self):
        return self

    def __next__(self):
        if self.job_count < 1:
            raise StopIteration

        item = self.incoming.get()
        if self.decrement(item):
            self.job_count -= 1

        return item

    def decrement(self, item):
        return True

# XXX Not completely tested!
class SentinalJobQueue(JobQueue):
    def __init__(self, incoming, outgoing, jobs, sentinal=None):
        super().__init__(incoming, outgoing, jobs)
        self.sentinal = sentinal

    def decrement(self, item):
        return item == self.sentinal
