#!/bin/bash

#SBATCH --mem=60G
#SBATCH --time=30
#SBATCH --mail-type=ALL
#SBATCH --mail-user=jsw7@nyu.edu
#SBATCH --nodes=1
#SBATCH --cpus-per-task=20
#SBATCH --job-name=index

#
# Usage:
#
#  $> sbatch $0 n path/to/toplevel
#
# where n are the number of n-grams to work with and path/to/toplevel
# is the path to the directory containing the trees ($output in
# $ZR_HOME/qsub/suffix.sh)
#

ngrams=`printf "%02.f" ${1}`

#
# Extract the term files
#

tar \
    --extract \
    --bzip \
    --directory=$SLURM_JOBTMP \
    --file=${2}/pseudoterms/${ngrams}.tar.bz

#
# Generate TREC formatted documents
#

documents=`mktemp --directory --tmpdir=$SLURM_JOBTMP`

find $SLURM_JOBTMP/$ngrams -name 'WSJ*' -not -name 'WSJQ*' | \
  python3 $ZR_HOME/src/create/parse.py \
    --output $documents \
    --parser pt \
    --strainer trec \
    --consolidate

#
# Generate Indri indexes from the documents
#

index=${2}/indri/$ngrams
rm --recursive --force $index
mkdir --parents $index

IndriBuildIndex \
  -corpus.path=$documents \
  -corpus.class=trectext \
  -index=$index
