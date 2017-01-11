#!/bin/bash

nodes=20
data=$WORK/wsj/2016_1128_014701
model=ua

while getopts "g:d:m:n:s:h" OPTION; do
    case $OPTION in
        g) ngrams=`printf "%02d" $OPTARG` ;;
        d) data=$OPTARG ;;
        m) model=$OPTARG ;;
        n) nodes=$OPTARG ;;
        s) selector=$OPTARG ;;
        h)
            exit
            ;;
        *) exit 1 ;;
    esac
done

output=$data/selector/$ngrams/$selector
mkdir --parents $output
rm --force jobs

qsub=`mktemp`
queries=( `find $data/pseudoterms -name 'WSJQ*'` )
last=`${queries[${#queries[@]}-1]}`

for i in ${queries[@]}; do
    if [ `wc --lines $qsub` -lt $nodes ] || [ $i != $last  ]; then
        q=`basename $i`
        topic=${q:6:3}
        
        cat <<EOF >> $qsub
python3 $HOME/src/pyzrt/src/reveal.py \
    --model ua \
    --qrels $WORK/qrels/$topic \
    --index $data/indri/$ngrams \
    --input $data/pseudoterms/$ngrams \
    --output $output/$topic \
    --selector $selector \
    --query $i
EOF
    else
        echo "[ `date` ] $qsub"        
        qsub \
	    -j oe \
	    -l nodes=1:ppn=$nodes,mem=60GB,walltime=6:00:00 \
	    -m abe \
	    -M jsw7@nyu.edu \
	    -N reveal-$qsub \
	    -V \
 	    parallel $qsub >> jobs
        if [ $i != $last ]; then
            qsub=`mktemp`
        fi
    fi
done

# leave a blank line at the end
