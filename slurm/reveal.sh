#!/bin/bash

model=ua
while getopts "q:r:s:c:t:n:p:m:x:v:h" OPTION; do
    case $OPTION in
        q) query=$OPTARG ;;
        r) qrels=$OPTARG ;;
        s) strategy=$OPTARG ;;
        c) count=$OPTARG ;;
        x) metric=$OPTARG ;;
	v) sieve=$OPTARG ;;
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

output=$root/selector/$ngrams/$strategy
mkdir --parents $output

job=`mktemp`

cat <<EOF >> $job
#!/bin/bash

python3 -u $ZR_HOME/src/qrels.py \
    --input $qrels \
    --output \$SLURM_JOBTMP \
    --topic $topic \
    --document-class WSJ \
    --count $count

python3 -u $ZR_HOME/src/reveal.py \
    --index $root/indri/$ngrams \
    --input $root/pseudoterms/$ngrams \
    --output $output \
    --qrels \$SLURM_JOBTMP/$topic \
    --selection-strategy $strategy \
    --query $query \
    --retrieval-model $model \
    --feedback-metric $metric \
    --clusters $SCRATCH/zrt/wsj/2017_0118_020518/cluster/04/kmeans-mini.csv \
    --sieve $sieve
EOF

sbatch \
    --mem=150G \
    --time=12:00:00 \
    --mail-type=END,FAIL \
    --mail-user=jsw7@nyu.edu \
    --nodes=1 \
    --cpus-per-task=4 \
    --job-name=reveal.`basename $query`-${strategy} \
    $job
