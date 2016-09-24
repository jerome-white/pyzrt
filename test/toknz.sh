#!/bin/bash

python3 ../src/toknz.py \
        --corpus test-docs/parsed \
        --block-size 4 > \
        test-docs/fragments.csv
