import csv
import itertools as it

def read_baseline(baseline, metric, single_topics=True):
    '''Read the file created by baseline.py
    baseline (Path): path to baseline file
    metric (TrecMetric): metric of choice
    single_topics (Bool): whether to ensure topics are listed once
    '''

    seen = set()

    with baseline.open() as fp:
        reader = csv.DictReader(fp)
        for line in reader:
            topic = line['topic']
            if single_topics:
                assert(topic not in seen)
                seen.add(topic)
            yield (topic, float(line[repr(metric)]))

# https://docs.python.org/3/library/itertools.html#itertools-recipes
def pairwise(iterable):
    '''s -> (s0,s1), (s1,s2), (s2, s3), ...
    '''

    (first, second) = it.tee(iterable)
    next(second, None)

    yield from zip(first, second)
