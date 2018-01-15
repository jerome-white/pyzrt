import os
import string
import operator as op
import functools as ft
import xml.etree.ElementTree as et
from pathlib import Path

import nltk

def Strainer(strainers=None):
    if strainers is None:
        strainers = []
    return _Strainer.builder(strainers)

class _Strainer:
    def __init__(self, strainer=None):
        self.strainer = strainer

    def strain(self, document):
        if not self.strainer:
            return document

        manipulation = self._manipulate(str(document))
        return self.strainer.strain(document.xerox(manipulation))

    def _manipulate(self, text):
        return text

    @classmethod
    def builder(cls, strainers):
        strain_selector = {
            'trec': TrecGenerate,
            'alpha': AlphaNumeric,
            'pause': PauseNormalize,
            'space': ft.partial(ReplacementPlus, new=' '),
            'under': ft.partial(ReplacementPlus, new='_'),
            'lower': ft.partial(CaseNormalize, casing='lower'),
            'symbol': SymbolNormalize,
            'clobber': ft.partial(ReplacementPlus, new=''),
            'phonetic': Phonetic,
        }

        s = cls()
        for i in strainers:
            Strainer = strain_selector[i.lower()]
            s = Strainer(s)

        return s

class Phonetic(_Strainer):
    '''Should be run before whitespace removal.
    '''

    def __init__(self, strainer):
        super().__init__(strainer)

        self.pronunciation = nltk.corpus.cmudict.dict()

    def _manipulate(self, text):
        speech = []

        for i in text.split():
            key = i.lower()
            if key in self.pronunciation:
                p = self.pronunciation[key]
                trans = ' '.join(p[0])
            else:
                trans = i
            speech.append(trans)

        return ' '.join(speech)

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
    ascii_range = 7

    def __init__(self, strainer):
        super().__init__(strainer)

        self.table = { x: chr(x) for x in range(2 ** self.ascii_range) }

    def _manipulate(self, text):
        return text.translate(str.maketrans(self.table))

class SymbolNormalize(Translate):
    def __init__(self, strainer):
        super().__init__(strainer)

        punctuation = {}
        for i in string.punctuation:
            if i not in PauseNormalize.pauses:
                punctuation[i] = ' '

        self.table.update({
            '-': ' ',
            '&': ' and ',
            '%': ' percent ',
            **punctuation,
            **{ x: ' ' for x in string.whitespace },
        })

class AlphaNumeric(Translate):
    def __init__(self, strainer):
        super().__init__(strainer)

        for (i, c) in self.table.items():
            if not c.isalnum():
                self.table[i] = ' '

class PauseNormalize(Translate):
    pauses = ',;:.?!'

    def __init__(self, strainer):
        super().__init__(strainer)

        self.table.update({ x: ' . ' for x in PauseNormalize.pauses })

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
