#!/bin/bash

#SBATCH --mem=60G
#SBATCH --time=4:00:00
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=jsw7@nyu.edu
#SBATCH --nodes=1
#SBATCH --cpus-per-task=4
#SBATCH --job-name=archive

module load parallel/20161122

directory=$SCRATCH/zrt/wsj/${1}/pseudoterms
tmp=`mktemp --directory --tmpdir=.`

for i in $directory/*; do
    j=`basename $i`
    cat <<EOF
tar \
    --create \
    --bzip2 \
    --verbose \
    --file=$directory/$j.tar.bz \
    --directory=$directory \
    $j &> $tmp/$j
EOF
done | parallel --no-notice
