#!/bin/bash

#SBATCH --mem=60G
#SBATCH --time=24:00:00
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=jsw7@nyu.edu
#SBATCH --nodes=1
#SBATCH --cpus-per-task=20
#SBATCH --job-name=query-models

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
ngrams=`printf "%02.f" ${3}`

#
# Make QRELS
#
judgements=`mktemp --directory --tmpdir=$BEEGFS`
python3 -u $ZR_HOME/src/support/qrels.py \
        --input ${1} \
        --output $judgements \
        --document-class WSJ \
        --count $count

output=$BEEGFS/evals/$ngrams
# rm --force --recursive $output
mkdir --parents $output

python3 $ZR_HOME/src/query/baseline.py \
	--index $root/indri/$ngrams \
	--queries $root/queries \
	--qrels $judgements \
	--output $output

rm --recursive --force $judgements
