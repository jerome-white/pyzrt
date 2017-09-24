#!/bin/bash

#SBATCH --mem=60G
#SBATCH --time=4:00:00
#SBATCH --mail-type=ALL
#SBATCH --mail-user=jsw7@nyu.edu
#SBATCH --nodes=1
#SBATCH --cpus-per-task=20
#SBATCH --job-name=index

#
# Usage:
#
#  $> sbatch $0 n path/to/toplevel parser
#
# where
#    - n is the number of n-grams with which to work
#    - path/to/toplevel is the path to the directory containing the
#      trees ($output in $ZR_HOME/slurm/suffix.sh)
#    - parser is the type of parsing desired. Default is 'pt'. See
#      zrtlib/zparser.Paserer for details
#

module load pbzip2/intel/1.1.13

ngrams=`printf "%02.f" ${1}`
if [ ${3} ]; then
    parser=${3}    
else
    parser=pt    
fi

#
# Extract the term files
#

tar \
    --extract \
    --use-compress-prog=pbzip2 \
    --directory=$SLURM_JOBTMP \
    --file=${2}/pseudoterms/${ngrams}.tar.bz

#
# Generate TREC formatted documents
#

documents=`mktemp --directory --tmpdir=$BEEGFS`

find $SLURM_JOBTMP/$ngrams -name 'WSJ*' -not -name 'WSJQ*' | \
  python3 $ZR_HOME/src/create/parse.py \
    --output $documents \
    --parser $parser \
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

rm --recursive --force $documents
