from pathlib import Path
from argparse import ArgumentParser

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from zrtlib import logger
from zrtlib import zutils
from zrtlib.indri import QueryDoc

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

stats = []
for ngram in args.zrt.iterdir():
    for model in ngram.iterdir():
        for (topic, value) in zutils.get_stats(model, args.metric, args.all):
            qid = QueryDoc.components(Path(topic))
            stats.append({
                'n-grams': ngram.stem,
                'model': model.stem,
                'topic': qid.topic,
                metric: value,
            })
            log.debug(stats[-1].keys())
data = pd.DataFrame(stats)
fname = 'inter-{0}.png'.format(args.metric)

plt.figure(figsize=(24, 6))
#sns.set_context('tab')
sns.barplot(x='n-grams', y=metric, hue='model', data=data)
plt.savefig(fname, bbox_inches='tight')
