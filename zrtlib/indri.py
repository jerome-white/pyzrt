import os
import shutil
import subprocess
import collections
import xml.etree.ElementTree as et
from tempfile import NamedTemporaryFile

from zrtlib import logger
from zrtlib import zutils

QueryID = collections.namedtuple('QueryID', 'topic, number')

def element(name, parent=None, text='\n', tail='\n'):
    if parent is None:
        e = et.Element(name)
    else:
        e = et.SubElement(parent, name)
    e.text = text
    e.tail = tail

    return e

def relevant_documents(qrels):
    with qrels.open() as fp:
        # http://trec.nist.gov/data/qrels_eng/
        for line in fp:
            (topic, iteration, document, relevant) = line.strip().split()
            if int(topic) == 0 and int(relevant) > 0:
                yield document

class IndriQuery:
    def __init__(self):
        self.i = 0
        self.query = element('parameter')
        self.keys = ('type', 'number', 'text')

    def add(self, text):
        q = element('query', self.query)
        for (i, j) in zip(self.keys, ('indri', str(self.i), text)):
            element(i, q, j)

        self.i += 1

    def __str__(self):
        return et.tostring(self.query, encoding='unicode')

class TrecMetric:
    def __init__(self, metric):
        self.metric = metric

    def __str__(self):
        return '-m' + self.metric

    def __repr__(self):
        return '_'.join(self.metric.split('.', 1))

class QueryExecutor:
    def __init__(self, index, qrels, keep=False):
        self.index = index
        self.indri = shutil.which('IndriRunQuery')
        self.trec = shutil.which('trec_eval')

        with qrels.open() as fp:
            counts = set()
            for line in fp:
                (iteration, *_) = line.strip().split()
                counts.add(iteration)
            self.count = len(counts)

        self.qrels = qrels

        delete = not keep
        f = lambda x: NamedTemporaryFile(mode='w',
                                         delete=delete,
                                         suffix='-{0}{1}'.format(x,qrels.stem))
        (self.query_fp, self.results_fp) = map(f, 'qr')

        if keep:
            log = logger.getlogger()
            log.debug(self.query_fp.name)
            log.debug(self.results_fp.name)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.query_fp.close()
        self.results_fp.close()

    def query(self, query, verify=True):
        # erase the query and results files
        for i in (self.query_fp, self.results_fp):
            if i.tell() > 0:
                i.seek(0)
                i.truncate()

        # print the query to disk
        print(query, file=self.query_fp, flush=True)

        # build/execute the Indri command
        cmd = [
            self.indri,
            '-trecFormat=true',
            '-count={0}'.format(self.count),
            '-index={0}'.format(self.index),
            self.query_fp.name,
        ]
        result = subprocess.run(cmd, stdout=self.results_fp)
        self.results_fp.flush()

        if verify:
            result.check_returncode()
            assert(os.stat(self.results_fp).st_size > 0)

        return result

    def relevant(self, judgements=None, limit=None):
        if judgements is None:
            judgements = relevant_documents(self.qrels)

        with open(self.results_fp.name) as fp:
            for line in fp:
                (_, document, order, *_) = line.strip().split()
                if limit is not None and int(order) > limit:
                    break
                if document in judgements:
                    yield document

    def evaluate(self, *metrics, all_metrics=True):
        cmd = [
            self.trec,
            '-q',
            '-c',
            '-mall_trec' if all_metrics else None,
            *map(str, metrics),
            '-M{0}'.format(self.count),
            str(self.qrels),
            self.results_fp.name,
        ]

        with subprocess.Popen(filter(None, cmd),
                              bufsize=1,
                              stdout=subprocess.PIPE,
                              universal_newlines=True) as fp:
            yield from zutils.read_trec(fp.stdout)

class QueryDoc:
    separator = '-'
    prefix = 'WSJQ00'

    def __init__(self, path):
        self.name = path.stem.zfill(3)
        self.docs = []

    def __iter__(self):
        yield from map(lambda x: et.tostring(x, encoding='unicode'), self.docs)

    def __bool__(self):
        return len(self.docs) > 0

    @classmethod
    def isquery(cls, doc):
        return doc.stem[:len(cls.prefix)] == cls.prefix

    @classmethod
    def components(cls, doc):
        if not cls.isquery(doc):
            raise ValueError()

        (name, number) = doc.stem.split(QueryDoc.separator)
        topic = name[len(QueryDoc.prefix):]

        return QueryID(topic, number)

    def add(self, query):
        attrs = collections.OrderedDict()
        attrs['DOCNO'] = '{0}{1}{2}{3:04d}'.format(QueryDoc.prefix,
                                                   self.name,
                                                   QueryDoc.separator,
                                                   len(self.docs))
        attrs['TEXT'] = ' '.join(query)

        doc = element('DOC')
        for (i, j) in attrs.items():
            element(i, doc, text=j)

        self.docs.append(doc)
