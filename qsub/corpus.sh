#!/bin/bash

#PBS -V
#PBS -l nodes=1:ppn=20,mem=60GB,walltime=1:00:00
#PBS -m abe
#PBS -M jsw7@nyu.edu
#PBS -N pyzrt-corpus
#PBS -j oe

#
# Generate the queries
#
o1=$HOME/src/pyzrt/data/queries
rm --recursive --force $o1
mkdir --parents $o1

python3 $HOME/src/pyzrt/src/topics.py \
  --topics $HOME/src/pyzrt/data/topics.251-300.gz \
  --output $o1 \
  --title \
  --description \
  --narrative

#
# Format the queries
#
o2=$HOME/var/WSJ/0000
rm --recursive --force $o2
mkdir --parents $o2

python3 $HOME/src/pyzrt/src/qformatter.py \
    --input $o1 \
    --output $o2 \
    --include-topic
o2=`dirname $o2`

#
# Build the corpus
#
o3=$SCRATCH/zrt/wsj/`date +'%Y_%m%d_%H%M%S'`/corpus
rm --force --recursive $o3
mkdir --parents $o3

python3 $HOME/src/pyzrt/src/parse.py \
    --raw-data $o2 \
    --output-data $o3 \
    --parser wsj \
    --strainer space:lower:alpha

# leave a blank line at the end
