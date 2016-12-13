#!/bin/bash

root=$WORK/wsj/2016_1128_014701
count=1000

for i in $root/indri/*; do
    terms=`basename $i`

    for j in ua sa u1 un; do
	#
	# Build the queries
	#
	queries=$root/queries/$terms/$j
	mkdir --parents $queries

	find $root/pseudoterms/$terms -name 'WSJQ*' | \
	    python $HOME/src/pyzrt/src/term2query.py \
	    --output $queries \
	    --model $j

	#
	# Run the queries
	#
	tmp=`mktemp`
	for k in $queries/*; do
	    IndriRunQuery \
		-count=$count \
		-index=$root/indri/$terms \
		-trecFormat=true $k > \
		$tmp

	    trec=$root/evals/$terms/$j/$i
	    mkdir --parents `dirname $trec`
	    trec_eval -q -c -M$count $WORK/qrels/`basename $i` $tmp > $trec
	done
	rm $tmp
    done
done
