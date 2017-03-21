#!/bin/bash

model=sa
while getopts "q:r:s:c:t:n:p:m:h" OPTION; do
    case $OPTION in
        q) query=$OPTARG ;;
        r) qrels=$OPTARG ;;
        s) strategy=$OPTARG ;;
        c) count=$OPTARG ;;
        # optional
        t) topic=$OPTARG ;;
        n) ngrams=$OPTARG ;;
        p) root=$OPTARG ;;
        m) model=$OPTARG ;;
        h)
            exit
            ;;
        *) exit 1 ;;
    esac
done

if [ ! $root ] || [ ! $ngrams ]; then
    components=( `sed -e's/\// /g' <<< $query` )
    n=${#components[@]}

    if [ ! $root ]; then
        root=`sed -e's/ /\//g' <<< ${components[@]::$n-3}`
        if [ ${query:0:1} = '/' ]; then
            root=/$root
        fi
    fi
    if [ ! $ngrams ]; then
        ngrams=${components[@]:$n-2:1}
    fi
fi

if [ ! $topic ]; then
    topic=`python3 $ZR_HOME/src/query2topic.py --query $query`
fi

output=$root/selector/$ngrams/$strategy/$topic
mkdir --parents `dirname $output`

qsub=`mktemp`
judgements=`mktemp --directory`

cat <<EOF >> $qsub
python3 -u $ZR_HOME/src/qrels.py \
    --input $qrels \
    --output $judgements \
    --topic $topic \
    --document-class WSJ \
    --count $count

python3 -u $ZR_HOME/src/reveal.py \
    --index $root/indri/$ngrams \
    --input $root/pseudoterms/$ngrams \
    --output $output \
    --qrels $judgements/$topic \
    --selection-strategy $strategy \
    --query $query \
    --retrieval-model $model

rm --recursive --force $judgements
EOF

qsub \
    -j oe \
    -l nodes=1:ppn=20,mem=60GB,walltime=6:00:00 \
    -m abe \
    -M jsw7@nyu.edu \
    -N reveal-`basename $query` \
    -V \
    $qsub
