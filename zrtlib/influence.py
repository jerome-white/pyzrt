import csv
import collections

TermScore = collections.namedtuple('TopTerm', 'term, score, unique')

class Influence:
    def __init__(self, results, metric):
        '''
        results: location of results file (Pathlike)
        metric: metric of interest (TrecMetric)
        '''

        self.high = None
        self.aggregate = collections.defaultdict(list)
    
        with results.open() as fp:
            reader = csv.DictReader(fp)
            for line in reader:
                (score, term) = [ line[x] for x in (repr(metric), 'term') ]
                score = float(score)
                
                self.aggregate[score].append(term)
                if self.high is None or score > self.high:
                    self.high = score

    def __bool__(self):
        return self.high > 0

    def __iter__(self):                
        for score in sorted(self.aggregate.keys(), reverse=True):
            terms = self.aggregate[score]
            for i in self.subsort(terms):
                yield TermScore(i, score, len(terms) == 0)
    
    def top(self, n):
        for (i, term) in enumerate(self):
            yield term
            if i > n:
                break

    def best(self):
        return next(self.top(1))

    def subsort(self, terms):
        raise NotImplementedError()

class TermInfluence(Influence):
    def subsort(self, terms):
        yield from terms
