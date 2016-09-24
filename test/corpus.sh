#!/bin/bash

rm --recursive --force test-docs
mkdir --parents test-docs/{parsed,raw}
for i in `seq 100`; do
    for j in `seq $(expr $RANDOM % 10)`; do
        echo $j
    done > `mktemp --tmpdir=test-docs/raw`
done

ls test-docs/raw/* | \
    python3 ../src/parse.py \
            --archive-type test \
            --corpus test-docs/parsed
