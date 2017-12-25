import collections as cl

class TermSelector:
    def __init__(self, index, seed=None):
        self.index = index
        self.seed = cl.deque(seed) if seed is not None else []

        self.feedback = None
        self.selected = None

    #
    # Set up the DataFrame used by the selectors
    #
    def __iter__(self):
        self.selected = {}
        return self

    #
    # Each iteration presents the dataframe to the strategy and marks
    # the choice as selected
    #
    def __next__(self):
        if self.seed:
            term = self.seed.popleft()
        else:
            with self.index.reader() as reader:
                while True:
                    term = self.pick(reader)
                    if term not in self.selected:
                        break

        self.selected[term] = len(self.selected) + 1

        return term

    def pick(self, reader):
        raise NotImplementedError()

class SequentialSelector(TermSelector):
    def __init__(self, index, seed=None):
        super().__init__(index, seed):
        self.documents = None

    def pick(self, reader):
        if self.document is None:
            for i in reader.all_doc_ids():
                entry = WhooshEntry(reader.stored_fields(i))
                with entry.document.open() as fp:
                    word = []
                    while True:
                        c = fp.read()
                        if not c:
                            break
                        if c in strings.whitespace:
                            yield ''.join(word)
                            word = []
                        else:
                            word.append(c)
