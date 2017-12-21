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

    def __str__(self):
        '''Suitable for supplying directly to the trec_eval command

        '''
        return '-m' + self.metric

    def __repr__(self):
        '''The key in trec_eval results

        '''
        return '_'.join(self.metric.split('.', 1))

class QueryRelevance:
    def __init__(self, qrels):
        self.qrels = qrels

    def __str__(self):
        return str(self.qrels)

    def __len__(self):
        with self.qrels.open() as fp:
            counts = set()
            for line in fp:
                (iteration, *_) = line.strip().split()
                counts.add(iteration)
            return len(counts)

    def relevant(self):
        with self.qrels.open() as fp:
            # http://trec.nist.gov/data/qrels_eng/
            for line in fp:
                (topic, _, document, relevant) = line.strip().split()
                if not int(topic) and int(relevant) > 0:
                    yield document

class Search:
    def __init__(self, index, qrels):
        self.qrels = qrels
        self.count = len(self.qrels)

        self.trec = sh.which('trec_eval')

    def _shell(self, cmd):
        with sp.Popen(cmd,
                      bufsize=1,
                      stdout=sp.PIPE,
                      universal_newlines=True) as proc:
            proc.wait()

            yield from proc.stdout

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

class IndriSearch(Search):
    def __init__(self, index, qrels):
        super().__init__(qrels)

        self.index = index
        self.indri = sh.which('IndriRunQuery')

    def execute(self, query, baseline=None):
        '''Build/execute the Indri command

        '''

        cmd = [
            self.indri,
            '-trecFormat=true',
            '-count={0}'.format(self.count),
            '-index={0}'.format(self.index),
            str(query),
        ]
        if baseline:
            cmd.insert(-1, '-baseline='.format(baseline))

        yield from self._shell(cmd)
