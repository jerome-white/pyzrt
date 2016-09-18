from pathlib import Path

class Corpus(dict):
    def __init__(self, path):
        for i in path.iterdir():
            with i.open() as fp:
                self[i.name] = fp.read()

class CorpusListing(list):
    def __init__(self, directory):
        path = Path(directory)
        assert(path.is_dir())
        super().__init__(self._sort(path.iterdir()))

    def _sort(self, files):
        raise NotImplementedError()

class NameSortedCorpus(CorpusListing):
    def _sort(self, files):
        return sorted(files)
