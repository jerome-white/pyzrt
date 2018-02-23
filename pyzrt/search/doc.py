import collections as cl
import xml.dom.minidom as dom
import xml.etree.ElementTree as et

QueryID = cl.namedtuple('QueryID', 'topic, number')

class _IndriXML:
    def __init__(self):
        self.xml = None

    def __str__(self):
        flatten = et.tostring(self.xml, encoding='utf-8')
        pretty = dom.parseString(flatten).toprettyxml(indent='')
        body = pretty.index('\n') + 1 # first line ('<? xml...') confuses Indri

        return pretty[body:]

class IndriDocument(_IndriXML):
    def __init__(self, collection):
        super().__init__()

        self.xml = et.Element('DOC')
        parts = map(lambda x: x(collection), (repr, str))
        for (i, j) in zip(('DOCNO', 'TEXT'), parts):
            e = et.SubElement(self.xml, i)
            e.text = str(j)

class IndriQuery(_IndriXML):
    def __init__(self):
        super().__init__()

        self.xml = et.Element('parameter')
        self.keys = ('type', 'number', 'text')
        self.number = 0

    def add(self, text):
        child = et.SubElement(self.xml, 'query')
        for (x, y) in zip(self.keys, ('indri', str(self.number), text)):
            e = et.SubElement(child, x)
            e.text = str(y)

        self.number += 1

class TrecDocument:
    separator = '-'
    prefix = 'WSJQ00'

    def __init__(self, path):
        self.name = path.stem.zfill(3)
        self.docs = []

    def __iter__(self):
        yield from map(lambda x: et.tostring(x, encoding='unicode'), self.docs)

    def __bool__(self):
        return bool(self.docs)

    @classmethod
    def isquery(cls, doc):
        return doc.stem[:len(cls.prefix)] == cls.prefix

    @classmethod
    def components(cls, doc):
        if not cls.isquery(doc):
            raise ValueError()

        (name, number) = doc.stem.split(cls.separator)
        topic = name[len(cls.prefix):]

        return QueryID(*map(int, (topic, number)))

    def add(self, query):
        attrs = cl.OrderedDict()
        attrs['DOCNO'] = '{0}{1}{2}{3:04d}'.format(self.prefix,
                                                   self.name,
                                                   self.separator,
                                                   len(self.docs))
        attrs['TEXT'] = ' '.join(query)

        doc = element('DOC')
        for (i, j) in attrs.items():
            element(i, doc, text=j)

        self.docs.append(doc)
