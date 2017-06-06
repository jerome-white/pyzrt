#!/bin/bash

n=4
seed_size=1
zrt=$SCRATCH/zrt
metric=ndcg_cut.10
root=$zrt/wsj/2017_0118_020518
clusters=kmeans-mini.csv

unset ntopics
strategies=(
    direct
    nearest
    feedback
)
sieves=(
    cluster
    term
)
techniques=( entropy )

ngrams=`printf "%02.f" $n`

for i in $root/evals/single/$ngrams/*; do
    seed=( `python3 $ZR_HOME/src/support/top-terms.py \
            --metric $metric \
            --results $i \
            --non-zero | \
            head --lines=$seed_size` )
    if [ ! $seed ]; then
        continue
    fi
    seed=`sed -e's/ / --seed /g' <<< ${seed[@]}`

    topic=`python3 $ZR_HOME/src/support/query2topic.py --query $i`
    
    for strategy in ${strategies[@]}; do
        for technique in ${techniques[@]}; do
            for sieve in ${sieves[@]}; do
                path=$root/picker/$ngrams
                mkdir --parents $path
		output=`mktemp --tmpdir=$path $topic.XXXXX`

                job=`mktemp`
                cat <<EOF >> $job
#!/bin/bash

python3 -u $ZR_HOME/src/support/qrels.py \
    --input $HOME/etc/wsj/qrels.251-300.parts1-5.tar.gz \
    --output \$SLURM_JOBTMP \
    --topic $topic \
    --document-class WSJ \
    --count 1000 &

tar \
    --extract \
    --bzip \
    --directory=\$SLURM_JOBTMP \
    --file=$root/pseudoterms/$ngrams &

wait

python3 -u $ZR_HOME/src/select/pick.py \
    --index $root/indri/$ngrams \
    --qrels \$SLURM_JOBTMP/$topic \
    --documents \$SLURM_JOBTMP/$ngrams \
    --output $output \
    --strategy $strategy \
    --technique $technique \
    --sieve $sieve \
    --feedback-metric $metric \
    --clusters $root/cluster/$ngrams/$clusters \
    --seed $seed
EOF

                sbatch \
                    --mem=150G \
                    --time=12:00:00 \
                    --mail-type=END,FAIL \
                    --mail-user=jsw7@nyu.edu \
                    --nodes=1 \
                    --cpus-per-task=2 \
                    --job-name=pick-${strategy}_${sieve}_${topic} \
                    $job
            done
        done
    done

    if [ $ntopics ]; then
        (( ntopics-- ))
        if [ $ntopics -eq 0 ]; then
            break
        fi
    fi
done
