import xml.etree.ElementTree as et
from pathlib import Path
from argparse import ArgumentParser

from zrtlib import logger
from zrtlib.zparser import PseudoTermParser

def func(incoming, outgoing):
    log = logger.getlogger()
    parser = PseudoTermParser()
    
    while True:
        (document, ) = incoming.get()
        log.info(document)

        for i in parser.parse(document):
            outgoing.put(i.text)

arguments = ArgumentParser()
arguments.add_argument('--input', type=Path)
args = arguments.parse_args()

incoming = mp.Queue()
outgoing = mp.Queue()
with mp.Pool(initializer=func, initargs=(outgoing, incoming)):
    jobs = 0
    for document in args.input.iterdir():
        outgoing.put(document)
        jobs += 1

    query = et.Element('parameter')
    while jobs > 0:
        (text, ) = incoming.get()
        et.SubElement(query, 'type').text = 'indri'
        et.SubElement(query, 'number').text = str(jobs)
        et.SubElement(query, 'text').text = text
        jobs -= 1
    print(et.tostring(query, encoding='unicode'))
