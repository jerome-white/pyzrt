#!/bin/bash

#PBS -V
#PBS -l nodes=1:ppn=20,mem=180GB,walltime=6:00:00
#PBS -m abe
#PBS -M jsw7@nyu.edu
#PBS -N pyzrt-reveal
#PBS -j oe

ngrams=6

n=`printf "%02d" $ngrams`
python3 $HOME/src/pyzrt/src/reveal.py \
    --model ua \
    --index $WORK/wsj/2016_1128_014701/indri/$n \
    --metric MAP \
    --qrels $WORK/qrels \
    --input $WORK/wsj/2016_1128_014701/pseudoterms/$n \
    --output $TMPDIR/$n.csv

# leave a blank line at the end
