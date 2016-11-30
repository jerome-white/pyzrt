import multiprocessing as mp
import xml.etree.ElementTree as et
from pathlib import Path
from argparse import ArgumentParser

from zrtlib import logger
from zrtlib.zparser import PseudoTermParser

def func(incoming, outgoing):
    log = logger.getlogger()
    parser = WSJParser()
    
    while True:
        document = incoming.get()
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

    keys = [ 'type', 'number', 'text' ]
    query = et.Element('parameter')
    for i in range(jobs):
        text = incoming.get()
        for (j, k) in zip(keys, ('indri', str(i), text)):
            et.SubElement(query, j).text = k
    print(et.tostring(query, encoding='unicode'))
