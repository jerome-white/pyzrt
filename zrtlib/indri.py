import xml.etree.ElementTree as et

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
