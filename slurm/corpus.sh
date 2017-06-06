#!/bin/bash

#SBATCH --mem=60GB
#SBATCH --time=60
#SBATCH --cpus-per-task=20
#SBATCH --nodes=1
#SBATCH --job-name=pyzrt-corpus
#SBATCH --mail-type=ALL
#SBATCH --mail-user=jsw7@nyu.edu

data=$HOME/etc/wsj

#
# Generate the queries
#
o1=`mktemp --directory --tmpdir=$SLURM_JOBTMP`

python3 $ZR_HOME/src/support/topics.py \
        --topics $data/topics.251-300.gz \
        --output $o1 \
        --with-title \
        --with-description \
        --with-narrative

#
# Format the queries
#
o2=$data/docs/0000
rm --force --recursive $o2
mkdir --parents $o2

python3 $ZR_HOME/src/create/qformatter.py \
        --input $o1 \
        --output $o2 \
        --with-topic

#
# Build the corpus
#
o3=$SCRATCH/zrt/corpus
rm --force --recursive $o3
mkdir --parents $o3

python3 $ZR_HOME/src/create/parse.py \
        --documents `dirname $o2` \
        --output $o3 \
        --parser wsj \
        --strainer space:lower:alpha
