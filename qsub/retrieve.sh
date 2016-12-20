#!/bin/bash

basenames() {
    unset names
    for ii in $@; do
	names=( ${names[@]} `basename $ii` )
    done
    echo ${names[@]}
}

count=1000

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

for term in $root/queries/*; do
    terms=`basename $term`

    for model in $term/*; do
	trec=$root/evals/$terms/`basename $model`
	rm --recursive --force $trec
	mkdir --parents $trec

	for query in $model/*; do
	    results=`mktemp`
	    IndriRunQuery \
		-count=$count \
		-index=$root/indri/$terms \
		-trecFormat=true \
		$query > \
		$results

	    q=`basename $query`
	    topic=`cut --delimiter='-' --fields=1 <<< $q`
	    topic=${topic:(-3)}

	    echo "[ `date` ] `basenames $term $model $query` $topic"

	    trec_eval -q -c -M$count $WORK/qrels/$topic $results > \
		      $trec/$q
	    rm $results
	done
    done
done
