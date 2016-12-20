#!/bin/bash

#PBS -V
#PBS -l nodes=1:ppn=20,mem=60GB,walltime=4:00:00
#PBS -m abe
#PBS -M jsw7@nyu.edu
#PBS -N pyzrt
#PBS -j oe

module purge
module load parallel/20140722

root=$WORK/wsj/2016_1128_014701
count=1000

# nodes=( `cat $PBS_NODEFILE | uniq` )
# n=${#nodes[@]}

for term in $root/queries/*; do
    terms=`basename $term`

    for model in $term/*; do
	trec=$root/evals/$terms/`basename $model`
	rm --recursive --force $trec
	mkdir --parents $trec

	for query in $model/*; do
	    cat <<EOF
$HOME/src/pyzrt/indri/qe.sh \
  -c $count \
  -i $root/indri/$terms \
  -q $query \
  -r $WORK/qrels \
  -o $trec
EOF
	done
    done
done | parallel --no-notice
