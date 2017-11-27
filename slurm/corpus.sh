#!/bin/bash

#SBATCH --mem=60GB
#SBATCH --time=60
#SBATCH --cpus-per-task=20
#SBATCH --nodes=1
#SBATCH --job-name=pyzrt-corpus

#
# Usage:
#
#  $> sbatch $0 strainer path/to/raw/data
#
# where
#    - strainer is the colon separated strainers to use; examples:
#
#        space:lower:alpha            "standard"
#        nospace:lower:alpha          no spaces
#        pause:nospace:lower:alpha    no spaces, pauses as periods
#
#      see pyzrt/parsing/strainer.py
#
#    - path/to/raw/data is the path to the directory containing the
#      unformatted data; assumes TREC WSJ
#

if [ ${2} ]; then
    data=${2}
else
    data=$HOME/etc/wsj
fi

#
# Generate the queries
#
o1=`mktemp --directory --tmpdir=$SLURM_JOBTMP`

python $ZR_HOME/src/support/topics.py \
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

python $ZR_HOME/src/create/qformatter.py \
       --input $o1 \
       --output $o2 \
       --with-topic

#
# Build the corpus
#

o3=$BEEGFS/corpus/`sed -e's/:/_/g' <<< $strainer`
rm --force --recursive $o3
mkdir --parents $o3

python3 $ZR_HOME/src/create/parse.py \
        --documents `dirname $o2` \
        --output $o3 \
        --parser wsj \
        --strainer ${1}
