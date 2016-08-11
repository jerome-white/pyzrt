import pickle

from pathlib import Path

class Output:
    def __init__(self, output):
        self.output = Path(output)

    def fpath(self, fname, suffix):
        return self.output.joinpath(fname).with_suffix('.' + suffix)

    def to_pickle(self, fname, data, suffix='pkl'):
        o = self.fpath(fname, suffix)
        with o.open('wb') as fp:
            pickle.dump(data, fp)
