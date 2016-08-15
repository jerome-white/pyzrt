import csv
import similarity

from pathlib import Path
from argparse import ArgumentParser
from multiprocessing import Manager

arguments = ArgumentParser()
arguments.add_argument('--corpus-directory')
arguments.add_argument('--fragment-file')
args = arguments.parse_args()

similarity.pairs(args.corpus_directory, args.fragment_file)
