#!/bin/bash

while getopts "r:h" OPTION; do
    case $OPTION in
	r) root=$OPTARG ;;
	h)
	    cat<<EOF
$0 [options]
     -r top level run directory (usually directory containing the
        directory of trees)
EOF
	    exit
	    ;;
        *) exit 1 ;;
    esac
done

results=`mktemp`
for term in $root/queries/*; do
    terms=`basename $term`

    for model in $term/*; do
	trec=$root/evals/$terms/`basename $model`
	rm --recursive --force $trec
	mkdir --parents $trec

	for query in $model/*; do
	    echo $term $model $query

	    IndriRunQuery \
		-baseline=tfidf \
		-count=$count \
		-index=$root/indri/$terms \
		-trecFormat=true \
		$query > \
		$results

	    q=`basename $query`
	    topic=`cut --delimiter='-' --fields=1 <<< $q`
	    trec_eval -q -c -M$count $WORK/qrels/${topic:(-3)} $results > \
		      $trec/$q
	done
    done
done
