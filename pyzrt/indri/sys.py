import shutil as sh
import subprocess as sp
import collections as cl
from tempfile import SpooledTemporaryFile

TrecMeasurement = cl.namedtuple('TrecMeasurement', 'run, results')

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
        with qrels.open() as fp:
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
        self.index = index
        self.qrels = qrels
        self.count = len(self.qrels)

        self.indri = sh.which('IndriRunQuery')
        self.trec = sh.which('trec_eval')

    def execute(query):
        '''Build/execute the Indri command

        '''

        cmd = [
            sh.which('IndriRunQuery'),
            '-trecFormat=true',
            '-count={0}'.format(self.count),
            '-index={0}'.format(index),
            str(query),
        ]

        with SpooledTemporaryFile(mode='w') as fp:
            result = sp.run(cmd, check=check, stdout=fp)
            result.wait()

            fp.flush()
            fp.seek(0)

            yield from fp

    def evaluate(self, rankings, metrics=None):
        if not metrics:
            metrics = [ TrecMetric('all_trec') ]

        cmd = [
            self.trec,
            '-q',
            '-c',
            *map(str, metrics),
            '-M{0}'.format(self.count),
            str(self.qrels),
#            self.results_fp.name,
        ]

        with sp.Popen(cmd,
                      bufsize=1,
                      stdin=sp.PIPE,
                      stdout=sp.PIPE,
                      universal_newlines=True) as proc:
            with proc.stdin as pipe:
                for i in rankings:
                    pipe.write(i)
            proc.wait()

            yield from proc.stdout

    def interpret(self, results, summary=False):
        previous = None
        summarised = False
        results = {}

        for line in results:
            (metric, run, value) = line.strip().split()
            try:
                run = int(run)
                assert(run >= 0)
            except ValueError:
                run = -1

            if previous is not None and previous != run:
                assert(not summarised)

                yield TrecMeasurement(previous, results)

                results = {} # probably not necessary, but safe
                if run < 0:
                    summarised = True

            try:
                results[metric] = float(value)
            except ValueError:
                results[metric] = value

            previous = run

        if results and (summary or run >= 0):
            yield TrecMeasurement(run, results)
