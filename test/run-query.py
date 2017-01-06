from pathlib import Path
from argparse import ArgumentParser
from tempfile import NamedTemporaryFile
from collections import namedtuple

import numpy as np

from zrtlib import logger
from zrtlib.query import QueryBuilder
from zrtlib.indri import QueryDoc, QueryExecutor
from zrtlib.document import TermDocument # HiddenDocument

arguments = ArgumentParser()
arguments.add_argument('--index')
arguments.add_argument('--query', type=Path)
arguments.add_argument('--qrels', type=Path)
arguments.add_argument('--indri')
arguments.add_argument('--trec-eval')
arguments.add_argument('--metric', default='map')
args = arguments.parse_args()

log = logger.getlogger()

with QueryExecutor(args.indri, args.trec_eval) as engine:
    count = 1000
    query = QueryBuilder('ua', TermDocument(args.query))
    
    with NamedTemporaryFile(mode='w', delete=False) as tmp:
        log.debug(tmp.name)
        print(QueryBuilder('ua', query, file=tmp, flush=True)
        result = engine.query(tmp.name, args.index, count)
        result.check_returncode()

    values = []
    info = QueryDoc.components(args.query)
    qrels = args.qrels.joinpath(info.topic)
    for line in engine.evaluate(str(qrels), count):
        (metric, run, value) = line.strip().split()
        if run.isdigit() and metric == args.metric:
            values.append(float(value))
    assert(values)

    print(info.topic, np.mean(values))
