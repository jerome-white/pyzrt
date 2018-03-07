import csv

class Baseline(dict):
    '''Read the file created by baseline.py
    baseline (Path): path to baseline file
    metric (TrecMetric): metric of choice
    single_topics (Bool): whether to ensure topics are listed once
    '''
    
    def __init__(self, baseline, metric, unique=True):
        seen = set()

        with baseline.open() as fp:
            reader = csv.DictReader(fp)
            for line in reader:
                topic = line['query']
                if unique:
                    assert(topic not in seen)
                    seen.add(topic)
                self[topic] = float(line['map'])
