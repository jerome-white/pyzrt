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
o1=$ZR_HOME/data/queries
rm --recursive --force $o1
mkdir --parents $o1

python3 $ZR_HOME/src/topics.py \
  --topics $ZR_HOME/data/topics.251-300.gz \
  --output $o1 \
  --with-title \
  --with-description \
  --with-narrative

#
# Format the queries
#
o2=$HOME/var/WSJ/0000
rm --recursive --force $o2
mkdir --parents $o2

python3 $ZR_HOME/src/qformatter.py \
    --input $o1 \
    --output $o2 \
    --with-topic

#
# Build the corpus
#
o2=`dirname $o2`

o3=$SCRATCH/zrt/wsj/`date +'%Y_%m%d_%H%M%S'`/corpus
rm --force --recursive $o3
mkdir --parents $o3

python3 $ZR_HOME/src/parse.py \
    --input $o2 \
    --output $o3 \
    --parser wsj \
    --strainer space:lower:alpha

# leave a blank line at the end
