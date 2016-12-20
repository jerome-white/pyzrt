#!/bin/bash

basenames() {
    unset names
    for ii in $@; do
	names=( ${names[@]} `basename $ii` )
    done
    echo ${names[@]}
}

while getopts "c:t:q:r:o:" OPTION; do
    case $OPTION in
	c) count=$OPTARG ;;
	i) index=$OPTARG ;;
	q) query=$OPTARG ;;
	r) qrels=$OPTARG ;;
	o) output=$OPTARG ;;
	*) exit 1 ;;
    esac
done

q=`basename $query`
topic=`cut --delimiter='-' --fields=1 <<< $q`
topic=${topic:(-3)}

echo "[ `date` ] `basenames $term $model $query` $topic"

results=`mktemp`
IndriRunQuery -count=$count -index=$index -trecFormat=true $query > $results
trec_eval -q -c -M$count $qrels/$topic $results > $output/$q
rm $results
