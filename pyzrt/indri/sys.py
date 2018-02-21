import os
import shutil as sh
import subprocess as sp
import collections as cl
from tempfile import NamedTemporaryFile

Measurement = cl.namedtuple('Measurement', 'run, results')

class TrecMetric:
    '''The trec_eval program uses different formats for the way metrics
    are specified and how they are presented in their results; this
    class acts a shield between knowing the difference.
    '''

    def __init__(self, metric):
        '''A metric as it would be specified to the trec_eval command.

        '''
        self.metric = metric

    #
    # Suitable for supplying directly to the trec_eval command
    #
    def __str__(self):
        return '-m' + self.metric

    #
    # The key in trec_eval results
    #
    def __repr__(self):
        return '_'.join(self.metric.split('.', 1))

class QueryRelevance:
    def __init__(self, qrels):
        self.qrels = qrels

    def __str__(self):
        return str(self.qrels)

    def __len__(self):
        counts = set()

        with self.qrels.open() as fp:
            for line in fp:
                (iteration, *_) = line.lstrip().split()
                counts.add(iteration)
            return len(counts)

    # http://trec.nist.gov/data/qrels_eng/
    def relevant(self):
        reported = set()

        with self.qrels.open() as fp:
            for line in fp:
                (*_, document, relevant) = line.rstrip().split()
                if document not in reported and int(relevant) > 0:
                    reported.add(document)
                    yield document

class Search:
    def __init__(self, qrels):
        self.qrels = qrels
        self.count = len(self.qrels)

        self.trec = sh.which('trec_eval')

    def _shell(self, cmd):
        with sp.Popen(cmd,
                      bufsize=1,
                      stdout=sp.PIPE,
                      universal_newlines=True) as proc:
            proc.wait()

            for i in proc.stdout:
                yield i.strip()

    def execute(self, query):
        raise NotImplementedError()

    def evaluate(self, execution, metrics=None):
        if not metrics:
            metrics = [ TrecMetric('all_trec') ]

        cmd = [
            self.trec,
            '-q',
            '-c',
            *map(str, metrics),
            '-M{0}'.format(self.count),
            str(self.qrels),
        ]

        with NamedTemporaryFile(mode='w') as fp:
            for i in execution:
                fp.write(i)
            fp.flush()

            if os.stat(fp.name):
                cmd.append(fp.name)
                yield from self._shell(cmd)

    def interpret(self, evaluation, summary=False):
        previous = None
        summarised = False
        results = {}

        for line in evaluation:
            (metric, run, value) = line.strip().split()
            try:
                run = int(run)
                assert(run >= 0)
            except ValueError:
                run = -1

            if previous is not None and previous != run:
                assert(not summarised)

                yield Measurement(previous, results)

                results = {} # probably not necessary, but safe
                if run < 0:
                    summarised = True

            try:
                results[metric] = float(value)
            except ValueError:
                results[metric] = value

            previous = run

        if results and (summary or run >= 0):
            yield Measurement(run, results)

    def do(self, query, metrics=None):
        yield from self.interpret(self.evaluate(self.execute(query), metrics))

    def get(self, query, metrics=None):
        return next(self.do(query, metrics))
