#!/bin/bash

#SBATCH --mem=60G
#SBATCH --time=6:00:00
#SBATCH --mail-type=ALL
#SBATCH --mail-user=jsw7@nyu.edu
#SBATCH --nodes=1
#SBATCH --cpus-per-task=20
#SBATCH --job-name=query-single

# ${1} /path/to/qrels
# ${2} run (directory inside wsj)
# ${3} ngrams
# ${4} count (optional)

if [ ${4} ]; then
    count=${4}
else
    count=1000
fi

root=$SCRATCH/zrt/wsj/${2}
ngrams=`printf "%02d" ${3}`

#
# Make QRELS
#
judgements=`mktemp --directory`
python3 $ZR_HOME/src/qrels.py \
        --input ${1} \
        --output $judgements \
        --document-class WSJ \
        --count $count

#
# Run the queries
#
output=$root/evals/single/$ngrams
rm --force --recursive $output
mkdir --parents $output

find $root/pseudoterms/$ngrams -name 'WSJQ*' | \
    python $ZR_HOME/src/single-term-queries.py \
           --index $root/indri/$ngrams \
           --qrels $judgements \
           --output $output
