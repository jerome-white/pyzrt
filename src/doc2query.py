import multiprocessing as mp
import xml.etree.ElementTree as et
from pathlib import Path
from argparse import ArgumentParser

from zrtlib import logger
from zrtlib import zutils
from zrtlib.zparser import WSJParser

def mkelement(name, parent=None, text='\n', tail='\n'):
    element = et.SubElement(parent, name) if parent else et.Element(name)
    element.text = text
    element.tail = tail

    return element

def func(incoming, outgoing):
    log = logger.getlogger()
    parser = WSJParser()
    
    while True:
        document = incoming.get()
        log.info(document)

        for i in parser.parse(document):
            query = mkelement('query')
            for (j, k) in zip(('type', 'text'), ('indri', i.text)):
                # mkelement(j, text=k, parent=query)
                e = et.SubElement(query, j)
                e.text = k
                e.tail = '\n'
            outgoing.put(query)

arguments = ArgumentParser()
arguments.add_argument('--input', type=Path)
args = arguments.parse_args()

incoming = mp.Queue()
outgoing = mp.Queue()
with mp.Pool(initializer=func, initargs=(outgoing, incoming)):
    jobs = 0
    for document in zutils.walk(args.input):
        outgoing.put(document)
        jobs += 1

    keys = [ 'type', 'number', 'text' ]

    doc = mkelement('parameter')
    for i in range(jobs):
        query = incoming.get()
        mkelement('number', text=str(i), parent=query)
        doc.append(query)

    print(et.tostring(doc, encoding='unicode'))
