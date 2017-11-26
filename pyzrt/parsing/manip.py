import xml.etree.ElementTree as et

def ascii_map(extended=False):
    ascii_range = 7
    if extended:
        ascii_range += 1

    for i in range(2 ** ascii_range):
        yield (i, chr(i))
    
def case_normalize(func, text, casing='lower'):
    assert(hasattr(str, casing))
    
    def manipulator(text):
        return op.methodcaller(casing)(text)

    return func

def punc_normalize(func, text, punctuation=None, stop='.'):
    table = dict(ascii_map(extended))
    
    if not punctuation:
        punctuation = '.?!,;:'
        
    table.update({ x: stop for x in punctuation })
    
    def manipulator(text):
        return func(text.translate(table))

    return func
    
def replace_multi(func, text, this, that):
    def manipulator(text, this, that):
        return func(that.join(text.split(this)))
    return manipulator

def alphanumeric(func, text, extended=False, stops=True):
    table = dict(ascii_map(extended))
    
    replacements = {
        '&': ' and ',
        '%': ' percent ',
        '-': ' ',
    }
    
    for (i, c) in table.items():
        updated = None
        elif c in string.whitespace:
            replacements[i] = ' '
        elif not c.isalnum():
            replacements[i] = ''

    table.update(replacements)
    
    def manipulator(text):
        return func(text.translate(table))

    return func

def trec(func, text):
    def manipulator(text):
        top = et.Element('DOC')
	top.text = '\n'

        for i in ('docno', 'text'):
            e = et.SubElement(top, i.upper())
            e.text = getattr(document, i)
            if i == 'text':
                e.text = '\n' + e.text + '\n'
            e.tail = '\n'

        return et.tostring(top, encoding="unicode") + '\n'
    
    return func
