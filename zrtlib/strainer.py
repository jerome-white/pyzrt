import operator as op
import xml.etree.ElementTree as et

class Strainer:
    def __init__(self, strainer=None):
        self.strainer = strainer if strainer else self
        self.fmt = None

    def strain(self, document):
        return document

class AlphaNumericStrainer(Strainer):
    def __init__(self, strainer, extended=False):
        super().__init__(strainer)

        self.fmt = lambda x: x.lower()
        self.table = {}

        ascii_range = 7
        if extended:
            ascii_range += 1

        for i in range(2 ** ascii_range):
            c = chr(i)
            if not c.isalnum():
                if c == '%':
                    c = ' percent '
                elif c == '.':
                    c = ''
                else:
                    c = ' '
            self.table[i] = c

    def strain(self, document):
        document.text = document.text.translate(self.table)
        return self.strainer.strain(document)

class TRECStrainer(Strainer):
    def strain(self, document):
        top = et.Element('DOC')
        top.text = '\n'

        for i in [ 'docno', 'text' ]:
            e = et.SubElement(top, i.upper())
            e.text = op.attrgetter(i)(document)
            if i == 'text':
                e.text = '\n' + e.text + '\n'
            e.tail = '\n'

        document.text = et.tostring(top, encoding="unicode") + '\n'
        return self.strainer.strain(document)
