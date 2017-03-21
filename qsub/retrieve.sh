#!/bin/bash

#PBS -V
#PBS -l nodes=1:ppn=20,mem=60GB,walltime=2:00:00
#PBS -m abe
#PBS -M jsw7@nyu.edu
#PBS -N pyzrt
#PBS -j oe

module purge
module load parallel/20140722

#
# Must define variables at time of submission (qsub -v ...)
#  queries Location of query files (see $queries in
#          $ZR_HOME/qsub/query.sh)
#  qrels   Location of QRELS tarball
#  count   Depth of retrieval results (see Indri/trec_eval
#          documentation)
#

root=`dirname ${queries}`

judgements=`mktemp --directory`
python3 -u $ZR_HOME/src/qrels.py \
    --input ${qrels} \
    --output $judgements \
    --document-class WSJ \
    --count ${count}

for term in ${queries}/*; do
    terms=`basename $term`

    for model in $term/*; do
	trec=$root/evals/$terms/`basename $model`
	rm --recursive --force $trec
	mkdir --parents $trec

	for query in $model/*; do
	    cat <<EOF
$ZR_HOME/indri/qe.sh \
  -c ${count} \
  -i $root/indri/$terms \
  -q $query \
  -r $judgements \
  -o $trec \
  -b tfidf
EOF
	done
    done
done | parallel --no-notice
