#!/bin/bash

memory=60
hours=3
root=$WORK/wsj/2016_1128_014701
count=1000

rm --force jobs
for i in $root/indri/*; do
    for j in ua sa u1 un; do
	echo $i $j

	qsub=`mktemp`
	cat <<EOF > $qsub
i=$i
j=$j
root=$root
count=$count
EOF
	cat <<"EOF" >> $qsub
terms=`basename $i`
queries=$root/queries/$terms/$j
mkdir --parents $queries

find $root/pseudoterms/$terms -name 'WSJQ*' | \
    python $HOME/src/pyzrt/src/term2query.py \
    --output $queries \
    --model $j

tmp=`mktemp`
for k in $queries/*; do
    IndriRunQuery \
	-count=$count \
	-index=$root/indri/$terms \
	-trecFormat=true $k > \
	$tmp

    topic=`cut --delimiter='-' --fields=1 <<< $(basename $k)`
    trec=$root/evals/$terms/$j
    mkdir --parents $trec

    trec_eval -q -c -M$count $WORK/qrels/${topic:(-3)} $tmp > \
        $trec/`basename $k`
done
rm $tmp
EOF
	qsub \
	    -j oe \
	    -l nodes=1:ppn=20,mem=${memory}GB,walltime=${hours}:00:00 \
	    -m abe \
	    -M jsw7@nyu.edu \
	    -N query \
	    -V \
	    $qsub >> jobs
    done
done