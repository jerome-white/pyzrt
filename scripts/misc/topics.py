import gzip
from pathlib import Path
from argparse import ArgumentParser

import pyzrt as pz

class Tracker:
    def __init__(self):
        self.topic = None
        self.recording = False
        self.text = []

    def __bool__(self):
        return bool(self.topic)

    def __str__(self):
        return ' '.join(self.text)

arguments = ArgumentParser()
arguments.add_argument('--topics')
arguments.add_argument('--output', type=Path)
arguments.add_argument('--with-title', action='store_true')
arguments.add_argument('--with-description', action='store_true')
arguments.add_argument('--with-narrative', action='store_true')
args = arguments.parse_args()

log = pz.util.get_logger(True)

tracker = Tracker()

with gzip.open(args.topics) as fp:
    for i in fp:
        line = i.decode().strip()
        if not line:
            continue

        parts = line.split()
        line_type = parts[0]
        if line_type == '<num>':
            tracker.topic = parts[-1]
        elif line_type == '<title>' and args.with_title:
            start = 2 if parts[1] == 'Topic:' else 1
            tracker.text.extend(parts[start:])
        elif line_type == '<desc>':
            tracker.recording = args.with_description
        elif line_type == '<narr>':
            tracker.recording = args.with_narrative
        elif line_type == '</top>':
            assert(tracker)
            log.info(tracker.topic)
            path = args.output.joinpath(tracker.topic)
            with path.open('w') as op:
                print(tracker, file=op)

            tracker = Tracker()
        elif tracker.recording:
            tracker.text.append(line)
