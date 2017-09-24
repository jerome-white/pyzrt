import string
import operator as op
import xml.etree.ElementTree as et

class Strainer:
    def __init__(self, strainer=None):
        self.strainer = strainer if strainer else self

    def strain(self, document):
        return document

    @classmethod
    def builder(cls, strainers):
        strain_selector = {
            'trec': TRECStrainer,
            'lower': CaseStrainer,
            'space': SpaceStrainer,
            'under': UnderscoreStrainer,
            'alpha': AlphaNumericStrainer,
        }

        s = cls()
        for i in strainers:
            Strainer = strain_selector[i.lower()]
            s = Strainer(s)

        return s

class CaseStrainer(Strainer):
    def __init__(self, strainer, casing='lower'):
        super().__init__(strainer)

        self.casing = op.methodcaller(casing)

    def strain(self, document):
        document.text = self.casing(document.text)
        return self.strainer.strain(document)

#
# Replace characters with "delimiter". Uses split so that multiple
# split_on's in-a-row are also replace; its primary purpose is to
# ensure there are single spaces between words.
#
class ReplacementStrainer(Strainer):
    def __init__(self, strainer, new, old=' '):
        super().__init__(strainer)

        self.new = new
        self.old = old

    def strain(self, document):
        pieces = document.text.split(self.old)
        document.text = self.new.join(pieces)

        return self.strainer.strain(document)

class SpaceStrainer(ReplacementStrainer):
    def __init__(self, strainer):
        super().__init__(strainer, ' ')

class UnderscoreStrainer(ReplacementStrainer):
    def __init__(self, strainer):
        super().__init__(strainer, '_')

class AlphaNumericStrainer(Strainer):
    def __init__(self, strainer, extended=False):
        super().__init__(strainer)

        replacements = {
            '&': ' and ',
            '%': ' percent ',
            '-': ' ',
        }

        self.table = {}

        ascii_range = 7
        if extended:
            ascii_range += 1

        for i in range(2 ** ascii_range):
            c = chr(i)
            if c in replacements:
                c = replacements[c]
            elif c in string.whitespace:
                c = ' '
            elif not c.isalnum():
                c = ''
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
