import csv
from pathlib import Path
from argparse import ArgumentParser
from multiprocessing import Pool

from zrtlib import zutils
from zrtlib import logger
from zrtlib.indri import IndriQuery, QueryExecutor, QueryDoc
from zrtlib.document import TermDocument

def func(args):
    (terms, options) = args

    log = logger.getlogger()
    log.info(terms.stem)

    #
    # Create a set of queries with a different term flipped.
    #
    indri = IndriQuery()
    qterms = TermDocument(terms).df['term'].unique()

    for i in qterms:
        indri.add(i)

    #
    # Pose the set of queries to Indri
    #
    rows = []
    fieldnames = set()
    qid = QueryDoc.components(terms)
    qrels = options.qrels.joinpath(qid.topic)

    with QueryExecutor(options.index, qrels) as engine:
        engine.query(indri)
        for (run, results) in engine.evaluate():
            assert('term' not in results)
            rows.append({ 'term': qterms[run], **results })
            fieldnames.update(rows[-1].keys())

    #
    # Write the results. Do this after running the queries because
    # TREC eval isn't always consistent with its keys.
    #
    with options.output.joinpath(terms.stem).open('w') as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return terms

arguments = ArgumentParser()
arguments.add_argument('--index', type=Path)
arguments.add_argument('--qrels', type=Path)
arguments.add_argument('--input', type=Path)
arguments.add_argument('--output', type=Path)
args = arguments.parse_args()

log = logger.getlogger()

with Pool() as pool:
    mkargs = lambda x: (x, args)
    for i in pool.imap(func, map(mkargs, zutils.walk(args.input))):
        log.info(i.stem)
