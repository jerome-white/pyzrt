import os
import sys
import shutil
import subprocess
import collections
import xml.etree.ElementTree as et
from tempfile import NamedTemporaryFile

QueryID = collections.namedtuple('QueryID', 'topic, number')

# XXX should replace the element function
class IndriElement:
    def __init__(self, root):
        self.element = None
        self._push(root, et.Element, '\n', '\n')

    def _push(self, name, loc, text, tail):
        self.element = loc(self.element, name)
        (self.element.text, self.element.tail) = (text, tail)
        
    def add(self, name, text='\n', tail='\n'):
        self._push(name, et.SubElement, text, tail)
        
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

    def __str__(self):
        return et.tostring(self.query, encoding='unicode')

    def add(self, text):
        q = element('query', self.query)
        for (i, j) in zip(self.keys, ('indri', str(self.i), text)):
            element(i, q, j)

        self.i += 1

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

        return QueryID(topic, int(number))

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
