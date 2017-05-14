#!/bin/bash

#SBATCH --mem=60G
#SBATCH --time=3:00:00
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

ngrams=`printf "%02d" ${1}`

#
# Convert the suffix trees to term files
#

pseudoterms=${2}/pseudoterms/$ngrams
rm --recursive --force $pseudoterms
mkdir --parents $pseudoterms

python3 $ZR_HOME/src/create/suffix2terms.py \
  --suffix-tree ${2}/trees/${ngrams}.csv \
  --output $pseudoterms

#
# Generate TREC formatted documents
#

documents=`mktemp --directory --tmpdir=$SLURM_JOBTMP`

find $pseudoterms -name 'WSJ*' -not -name 'WSJQ*' | \
  python3 $ZR_HOME/src/create/parse.py \
    --output $documents \
    --parser pt \
    --strainer trec \
    --consolidate

#
# Generate Indri indexes from term files
#
index=${2}/index/$ngrams
rm --recursive --force $index
mkdir --parents $index

IndriBuildIndex \
  -corpus.path=$documents \
  -corpus.class=trectext \
  -index=$index
