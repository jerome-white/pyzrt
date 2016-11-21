from pathlib import Path
from argparse import ArgumentParser

from zrtlib import logger
from zrtlib.suffix import suffix_builder
from zrtlib.tokenizer import TokenSet, unstream
from zrtlib.pseudoterm import PseudoTermWriter

arguments = ArgumentParser()
arguments.add_argument('--suffix-tree', type=Path)
arguments.add_argument('--basic-output', type=Path)
args = arguments.parse_args()

log = logger.getlogger()

log.info('suffix tree')
suffix = suffix_builder(args.suffix_tree, unstream, TokenSet)

log.info('term writer')
writer = PseudoTermWriter(s)
writer.write(args.basic_output)
