#!/bin/bash

#
#
#
for i in `seq 1990 1992`; do
    output=$SCRATCH/WSJ.fmt/$year
    mkdir --parents $output
    ls $SCRATCH/WSJ/$i/WSJ_* | \
	python3 archive.py --output-directory $output --archive-type WSJ
done

#
#
#
