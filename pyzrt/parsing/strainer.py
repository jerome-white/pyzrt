import string
import operator as op
import functools as ft
import xml.etree.ElementTree as et

def Strainer(strainers=None):
    if strainers is None:
        strainers = []
    return _Strainer.builder(strainers)

class _Strainer:
    def __init__(self, strainer=None):
        self.strainer = strainer if strainer else self

    def strain(self, document):
        manipulation = self._manipulate(str(document))

        return document.xerox(self.strainer.strain(manipulation))

    def _manipulate(self, text):
        return text

    @classmethod
    def builder(cls, strainers):
        strain_selector = {
            'trec': TrecGenerate,
            'pause': PauseNormalize,
            'alpha': AlphaNumeric,
            'lower': ft.partial(CaseNormalize, casing='lower'),
            'space': ft.partial(ReplacementPlus, new=' '),
            'under': ft.partial(ReplacementPlus, new='_'),
            'nospace': ft.partial(ReplacementPlus, new=''),
        }

        s = cls()
        for i in strainers:
            Strainer = strain_selector[i.lower()]
            s = Strainer(s)

        return s

class CaseNormalize(_Strainer):
    def __init__(self, strainer, casing):
        assert(hasattr(str, casing))
        super().__init__(strainer)

        self.casing = op.methodcaller(casing)

    def _manipulate(self, text):
        return self.casing(text)

class ReplacementPlus(_Strainer):
    '''Replace characters with "delimiter". Uses split so that multiple
       split_on's in-a-row are also replaced; its primary purpose is
       to ensure there are single spaces between words.

    '''

    def __init__(self, strainer, new, old=None):
        super().__init__(strainer)

        self.new = new
        self.old = old

    def _manipulate(self, text):
        return self.new.join(text.split(self.old))

class Translate(_Strainer):
    def __init__(self, strainer, extended):
        super().__init__(strainer)

        ascii_range = 7
        if extended:
            ascii_range += 1

        self.table = { x: chr(x) for x in range(2 ** ascii_range) }

    def _manipulate(self, text):
        return text.translate(self.table)

class AlphaNumeric(Translate):
    def __init__(self, strainer, extended=False):
        super().__init__(strainer)

        self.table.update({
            '-': ' ',
            '&': ' and ',
            '%': ' percent ',
            **{ x: ' ' for x in string.whitespace },
        })

        for (i, c) in self.table.items():
            if not c.isalnum():
                self.table[i] = ''

class PauseNormalize(Translate):
    def __init__(self, strainer, pause=',;:.?!', norm='.'):
        super().__init__(strainer)

        self.table.update({ x: stop for x in pause })

class TrecGenerate(_Strainer):
    def _manipulate(self, text):
        top = et.Element('DOC')
        top.text = '\n'

        for i in ('docno', 'text'):
            e = et.SubElement(top, i.upper())
            e.text = getattr(text, i)
            if i == 'text':
                e.text = '\n' + e.text + '\n'
            e.tail = '\n'

        return et.tostring(top, encoding="unicode") + '\n'
