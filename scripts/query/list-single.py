import operator as op
from pathlib import Path
from argparse import ArgumentParser
from multiprocessing import Pool

from zrtlib import zutils
from zrtlib import logger
from zrtlib.indri import TrecMetric
from zrtlib.influence import TermInfluence
import zrtlib.selector.technique as tq

def func(args):
    (results, opts) = args

    log = logger.getlogger()

    influence = TermInfluence(results, TrecMetric(opts.metric))
    if not influence:
        log.warning(results.stem)
    score = influence.best()
    
    # data = [ zutils.top_terms(results, TrecMetric(opts.metric)) ]
    
    # document = TermDocument(opts.terms.joinpath(results.stem))
    # techniques = [
    #     tq.DocumentFrequency,
    #     tq.TermFrequency,
    #     tq.Entropy,
    #     tq.TFIDF,
    # ]
    # data.extend([ x(document) for x in techniques ])

    # pd.DataFrame(np.column_stack(map(list, data))
    #              columns=map(op.attrgetter('__name__'), techniques))

    # pd.to_csv('/Users/jerome/Downloads/' + results.stem)

    return (results.stem, score.term, score.unique)

arguments = ArgumentParser()
arguments.add_argument('--metric')
arguments.add_argument('--results', type=Path)
arguments.add_argument('--term-files', type=Path)
args = arguments.parse_args()

log = logger.getlogger(True)

with Pool() as pool:
    iterable = map(lambda x: (x, args), args.results.iterdir())
    for i in pool.imap_unordered(func, iterable):
        log.info('{0} {1} {2}'.format(*i))
