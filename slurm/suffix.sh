#!/bin/bash

#SBATCH --mem=492G
#SBATCH --time=2-0
#SBATCH --mail-type=ALL
#SBATCH --mail-user=jsw7@nyu.edu
#SBATCH --nodes=1
#SBATCH --cpus-per-task=10
#SBATCH --job-name=reveal-suffix

#
# Usage:
#
#  $> sbatch $0 m n corpus output existing
#
#  1 m minimum n-gram
#  2 n maximum n-gram
#  3 path/to/corpus
#  4 output output directory (usually path/to/trees)
#  5 existing use most recent file in path/to/trees as "existing"
#

if [ ${5} ]; then
    recent=${4}/`ls --sort=time ${4} | head --lines=1`
    if [ $recent ]; then
        existing="--existing $recent"
    fi
fi

# compress=--no-compress

python3 -u $ZR_HOME/src/create/stree.py $existing $compress \
    --input ${3} \
    --output ${4} \
    --min-gram ${1} \
    --max-gram ${2} \
    --prune 1 \
    --workers $SLURM_CPUS_PER_TASK \
    --incremental \
    --document-boundaries

# for i in $output/*.csv; do
#     echo bzip2 $i
# done | parallel --no-notice
