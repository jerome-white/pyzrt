#!/bin/bash

ngrams=6
data=2016_1128_014701
selectors=(
    random
    df
    tf
    entropy
)

n=`printf "%02d" $ngrams`
path=$WORK/wsj/$data
output=$path/selector/$n
mkdir --parents $output
rm --force jobs

for i in ${selectors[@]}; do
    echo "[ `date` ] $i"
    qsub=`mktemp`
    cat <<EOF > $qsub
python3 $HOME/src/pyzrt/src/reveal.py \
    --model ua \
    --metric map \
    --qrels $WORK/qrels \
    --index $path/indri/$n \
    --input $path/pseudoterms/$n \
    --output $output/$i \
    --selector $i
EOF
    qsub \
	-j oe \
	-l nodes=1:ppn=20,mem=60GB,walltime=6:00:00 \
	-m abe \
	-M jsw7@nyu.edu \
	-N reveal-$i \
	-V \
	$qsub >> jobs
done

# leave a blank line at the end
