from pathlib import Path
from argparse import ArgumentParser
from multiprocessing import Pool

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from zrtlib import logger
from zrtlib import zutils
from zrtlib.indri import QueryDoc

def walk(path):
    for ngram in path.iterdir():
        for model in ngram.iterdir():
            yield (ngram, model)

def func(args):
    (ngram, model, metric, aggregate) = args

    stats = []
    for (topic, value) in zutils.get_stats(model, metric, aggregate):
        qid = QueryDoc.components(Path(topic))
        entry = [ ngram.stem, model.stem, qid.topic, value ]
        log.info(' '.join(map(str, entry[:-1])))

        stats.append(entry)

    return stats

def aquire(args):
    with Pool() as pool:
        keys = [ 'n-grams', 'model', 'topic', metric ]
        iterable = map(lambda x: (*x, args.metric, args.all), walk(args.zrt))
        for models in pool.imap_unordered(func, iterable):
            for i in models:
                yield dict(zip(keys, i))

arguments = ArgumentParser()
arguments.add_argument('--metric')
arguments.add_argument('--all', action='store_true') # "all" or runs only?
arguments.add_argument('--zrt', type=Path)
arguments.add_argument('--baseline', type=Path)
args = arguments.parse_args()

log = logger.getlogger()

metric = {
    'map': 'MAP',
    'recip_rank': 'Reciprocal Rank',
}[args.metric]

df = pd.DataFrame(aquire(args))

plt.figure(figsize=(24, 6))
# sns.set_context('paper')
sns.barplot(x='n-grams', y=metric, hue='model', data=df, errwidth=0.1)

fname = 'inter-{0}.png'.format(args.metric)
plt.savefig(fname, bbox_inches='tight')
