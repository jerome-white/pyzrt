from pathlib import Path
from argparse import ArgumentParser

from zrtlib.indri import TrecMetric
from zrtlib.influence import TermInfluence

arguments = ArgumentParser()
arguments.add_argument('--metric')
arguments.add_argument('--results', type=Path)
arguments.add_argument('--non-zero', action='store_true')
args = arguments.parse_args()

influence = TermInfluence(args.results, TrecMetric(args.metric))
for score in influence:
    if args.non_zero and score.score == 0:
        break
    print(score.term)
