import shlex
import shutil
import subprocess
import collections
import xml.etree.ElementTree as et
from tempfile import NamedTemporaryFile

QueryID = collections.namedtuple('QueryID', 'topic, number')

def element(name, parent=None, text='\n', tail='\n'):
    if parent is None:
        e = et.Element(name)
    else:
        e = et.SubElement(parent, name)
    e.text = text
    e.tail = tail

    return e

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

class QueryExecutor:
    def __init__(self, indri='IndriRunQuery', trec='trec_eval'):
        self.indri = shutil.which(indri)
        self.trec = shutil.which(trec)
        self.results = NamedTemporaryFile(mode='w')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.results.close()

    def query(self, query, index, count):
        cmd = [
            self.indri,
            '-trecFormat=true',
            '-count={0}'.format(count),
            '-index={0}'.format(index),
            str(query),
            ]

        return subprocess.run(cmd, stdout=self.results)

    def evaluate(self, qrels, count, aggregate=False):
        cmd = [
            self.trec,
            '-q',
            '-c',
            '-M{0}'.format(count),
            str(qrels),
            self.results.name,
            ]

        with subprocess.Popen(cmd,
                              bufsize=1,
                              stdout=subprocess.PIPE,
                              universal_newlines=True) as fp:
            previous = None
            results = {}

            for line in fp.stdout:
                (metric, run, value) = line.strip().split()
                if not run.isdigit():
                    continue

                if previous is not None and previous != run:
                    yield results
                    results = {} # probably not necessary, but safe

                results[metric] = float(value)
                previous = run

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

        (name, number) = doc.stem.split('-')
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
