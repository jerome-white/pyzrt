#!/bin/bash

#SBATCH --mem=60GB
#SBATCH --time=60
#SBATCH --cpus-per-task=20
#SBATCH --nodes=1
#SBATCH --job-name=pyzrt-prep

data=$HOME/etc/wsj

#
# Generate the queries
#
o1=`mktemp --directory --tmpdir=$SLURM_JOBTMP`

python $ZR_HOME/scripts/misc/topics.py \
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

python $ZR_HOME/scripts/parse/qformatter.py \
       --input $o1 \
       --output $o2 \
       --with-topic
