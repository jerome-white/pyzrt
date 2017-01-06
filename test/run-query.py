from pathlib import Path
from argparse import ArgumentParser
from tempfile import NamedTemporaryFile
from collections import namedtuple

import numpy as np

# from zrtlib import logger
from zrtlib.query import QueryBuilder
from zrtlib.indri import QueryDoc, QueryExecutor
from zrtlib.document import TermDocument # HiddenDocument

arguments = ArgumentParser()
arguments.add_argument('--index')
arguments.add_argument('--query', type=Path)
arguments.add_argument('--qrels', type=Path)
args = arguments.parse_args()

with QueryExecutor() as engine:
    count = 1000
    document = TermDocument(args.query)
    
    with NamedTemporaryFile(mode='w') as tmp:
        print(QueryBuilder('ua', document), file=tmp)
        result = engine.query(tmp.name, args.index, count)
        result.check_returncode()

    values = []
    info = QueryDoc.components(args.query)
    qrels = opts.qrels.joinpath(info.topic)
    for line in engine.evaluate(str(qrels), count)
        (metric, run, value) = line.strip().split()
        if run.isdigit() and metric == opts.metric:
            values.append(metric)
    assert(values)
    print(info.topic, np.mean(values))
