#!/bin/bash

#SBATCH --mem=60G
#SBATCH --time=12:00:00
#SBATCH --nodes=1
#SBATCH --cpus-per-task=20
#SBATCH --job-name=term2vec

# ${1} run (directory inside wsj)
# ${2} ngrams

ngrams=`printf "%02.f" ${2}`

#
# Extract the term files
#
tmp=`mktemp --directory --tmpdir=$BEEGFS`
tar \
    --extract \
    --bzip \
    --directory=$tmp \
    --file=${1}/pseudoterms/${ngrams}.tar.bz

output=${1}/embeddings/$ngrams
mkdir --parents $output

python3 $ZR_HOME/src/misc/term2vec.py \
        --corpus $tmp \
        --output $output \
        --workers 20

rm --recursive --force $tmp
