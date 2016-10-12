from argparse import ArgumentParser

from zrtlib.corpus import Corpus
from zrtlib.suffix import SuffixTree
from zrtlib.tokenizer import Sequencer, Tokenizer, CorpusTranscriber

arguments = ArgumentParser()
arguments.add_argument('--corpus', type=Path)
arguments.add_argument('--min-gram', type=int, default=1)
arguments.add_argument('--max-gram', type=int)
args = arguments.parse_args()

suffix = SuffixTree()
corpus = Corpus(args.corpus)
max_gram = args.max_gram if args.max_gram else corpus.characters() + 1

for i in range(args.min_gram, max_gram):
    sequencer = Sequencer(corpus, block_size=i)
    tokenizer = Tokenizer(sequencer)
    for (_, j) in tokenizer.each():
        transcription = CorpusTranscriber(j, corpus)
        suffix.add(str(transcription), j)
