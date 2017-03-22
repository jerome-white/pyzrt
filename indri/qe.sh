#!/bin/bash

basenames() {
    unset names
    for ii in $@; do
	names=( ${names[@]} `basename $ii` )
    done
    echo ${names[@]}
}

while getopts "c:i:q:r:o:b:" OPTION; do
    case $OPTION in
	c) count=$OPTARG ;;
	i) index=$OPTARG ;;
	q) query=$OPTARG ;;
	r) qrels=$OPTARG ;;
	o) output=$OPTARG ;;
	b) baseline="-baseline=$OPTARG" ;;
	*) exit 1 ;;
    esac
done

q=`basename $query`
if [ $output ]; then
    output="> $output/$q"
fi
topic=`cut --delimiter='-' --fields=1 <<< $q`
qrels=$qrels/${topic:(-3)}

if [ $baseline ]; then
    grep --quiet '#' $query || unset baseline
fi

echo "[ `date` ] $query"

results=`mktemp`
IndriRunQuery $baseline -trecFormat=true -count=$count -index=$index $query > \
	      $results
trec_eval -q -m all_trec -c -M$count $qrels $results $output && rm $results
