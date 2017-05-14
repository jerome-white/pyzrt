#!/bin/bash

#SBATCH --mem=60GB
#SBATCH --time=120
#SBATCH --cpus-per-task=20
#SBATCH --nodes=1
#SBATCH --job-name=pyzrt-retrieve
#SBATCH --mail-type=ALL
#SBATCH --mail-user=jsw7@nyu.edu

module purge
module load parallel/20140722

#
# Must define variables at time of submission (qsub -v ...)
#  queries Location of query files (see $queries in
#          $ZR_HOME/qsub/query.sh)
#  qrels   Location of QRELS tarball
#  count   Depth of retrieval results (see Indri/trec_eval
#          documentation)
#  action  Term action (see src/term2query.py and query.sh)
#

root=`dirname ${queries}`

judgements=`mktemp --directory`
python3 -u $ZR_HOME/src/support/qrels.py \
    --input ${qrels} \
    --output $judgements \
    --document-class WSJ \
    --count ${count}

for term in ${queries}/*; do
    terms=`basename $term`

    for model in $term/*; do
	trec=$root/evals/$action/$terms/`basename $model`
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
