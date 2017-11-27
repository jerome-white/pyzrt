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

    def add(self, text):
        self.text.append(text)

arguments = ArgumentParser()
arguments.add_argument('--topics')
arguments.add_argument('--output', type=Path)
arguments.add_argument('--with-title', action='store_true')
arguments.add_argument('--with-description', action='store_true')
arguments.add_argument('--with-narrative', action='store_true')
args = arguments.parse_args()

log = pz.util.get_logger(True)

with gzip.open(args.topics) as fp:
    for i in fp:
        line = i.decode().strip()
        if not line:
            continue

        parts = line.split()
        kind = parts[0]

        if kind == '<top>':
            tracker = Tracker()

        elif kind == '<num>':
            tracker.topic = parts[-1]

        elif kind == '<title>' and args.with_title:
            start = 2 if parts[1] == 'Topic:' else 1
            tracker.add(' '.join(parts[start:]) + '.')

        elif kind == '<desc>':
            tracker.recording = args.with_description

        elif kind == '<narr>':
            tracker.recording = args.with_narrative

        elif kind == '</top>':
            assert(tracker)
            log.info(tracker.topic)

            args.output.joinpath(tracker.topic).write_text(str(tracker))

        elif tracker.recording:
            tracker.add(line)
