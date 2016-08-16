#!/bin/bash

rm --recursive --force test-docs
mkdir --parents test-docs/{parsed,raw}
cat <<EOF > `mktemp --tmpdir=test-docs/raw`
text processing vs. speech processing
EOF

ls test-docs/raw/* | \
    python3 archive.py \
            --archive-type test \
            --output-directory test-docs/parsed

python3 fragment.py \
        --corpus-directory test-docs/parsed > \
        test-docs/fragments.csv

python3 -u similarity-gen.py \
        --corpus-directory test-docs/parsed \
        --fragment-file test-docs/fragments.csv > test-docs/similarity.csv

python3 dot-gen.py --png test-docs/dot-plot.png < test-docs/similarity.csv
