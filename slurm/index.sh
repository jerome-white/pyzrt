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

ngrams=`printf "%02.f" ${1}`

#
# Convert the suffix trees to term files
#

terms=`mktemp --directory`

python3 $ZR_HOME/src/create/suffix2terms.py \
  --suffix-tree ${2}/trees/${ngrams}.csv \
  --output $terms

#
# Archive the term files
#

pseudoterms=${2}/pseudoterms
mkdir --parents $pseudoterms

tar \
    --create \
    --bzip2 \
    --file=$pseudoterms/$ngrams.tar.bz \
    --directory=`dirname $terms` \
    `basename $terms`

#
# Generate TREC formatted documents
#

documents=`mktemp --directory`

find $terms -name 'WSJ*' -not -name 'WSJQ*' | \
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
