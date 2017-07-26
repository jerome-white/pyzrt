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
#  $> sbatch $0 n path/to/toplevel version
#
# {1} n                 number of n-grams to work with
# {2} path/to/toplevel  path to the directory containing the trees
#                       ($output in $ZR_HOME/qsub/suffix.sh)
# {3} version           Tree format version (optional)
#

ngrams=`printf "%02.f" ${1}`
if [ ${3} ]; then
    version="--version ${3}"
fi

#
# Convert the suffix trees to term files
#

terms=$SLURM_JOBTMP/$ngrams
mkdir $terms

python3 -u $ZR_HOME/src/create/suffix2terms.py $version \
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
