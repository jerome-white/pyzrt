#!/bin/bash

#SBATCH --mem=60GB
#SBATCH --time=60
#SBATCH --cpus-per-task=20
#SBATCH --nodes=1
#SBATCH --job-name=pyzrt-corpus
#SBATCH --mail-type=ALL
#SBATCH --mail-user=jsw7@nyu.edu

#
# Generate the queries
#
o1=$ZR_HOME/data/queries
rm --recursive --force $o1
mkdir --parents $o1

python3 $ZR_HOME/src/support/topics.py \
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

python3 $ZR_HOME/src/create/qformatter.py \
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

python3 $ZR_HOME/src/create/parse.py \
    --documents $o2 \
    --output $o3 \
    --parser wsj \
    --strainer space:lower:alpha

# leave a blank line at the end
