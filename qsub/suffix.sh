#!/bin/bash

#PBS -V
#PBS -l nodes=1:ppn=20,mem=492GB,walltime=48:00:00
#PBS -m abe
#PBS -M jsw7@nyu.edu
#PBS -N pyzrt-suffix
#PBS -j oe

n=4
m=12
path=$SCRATCH/zrt/wsj
tld=2017_0115_001558

output=$path/$tld/trees
if [ -e $output ]; then
    existing="--existing $output/`ls --sort=time $output | head --lines=1`"
else
    mkdir --parents $output
fi

python3 -u $HOME/src/pyzrt/src/stree.py $existing \
    --corpus $path/$tld/corpus \
    --output $output \
    --min-gram $n \
    --max-gram $m \
    --prune 1 \
    --workers 10 \
    --incremental

# ssh -x `hostname` "`which python3` -u $HOME/src/pyzrt/src/stree.py --corpus $OUTPUT/corpus --min-gram $n --max-gram $m --output $OUTPUT/suffix.csv --incremental --workers 10 --existing $TMPDIR/tmpt68f_7hs.5 2>&1"

# leave a blank line at the end
