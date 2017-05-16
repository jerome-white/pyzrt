#!/bin/bash

n=4
seed_size=1
zrt=$SCRATCH/zrt
root=$zrt/wsj/2017_0118_020518

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

ngrams=`printf "%02d" $n`

for i in $root/evals/single/$ngrams/*; do
    seed=( `python3 $ZR_HOME/src/support/top-terms.py \
            --metric ndcg_cut.10 \
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

                output=$root/picker/$ngrams/$strategy/$sieve/$topic
                mkdir --parents $output

                job=`mktemp`
                cat <<EOF >> $job
python3 -u $ZR_HOME/src/support/qrels.py \
    --input $zrt/qrels.251-300.parts1-5.tar.gz \
    --output \$SLURM_JOBTMP \
    --topic $topic \
    --document-class WSJ \
    --count 1000

python3 -u $ZR_HOME/src/select/pick.py \
    --index $root/indri/$ngrams \
    --documents $root/pseudoterms/$ngrams \
    --output-directory $output \
    --qrels \$SLURM_JOBTMP/$topic \
    --strategy $strategy \
    --technique $technique \
    --sieve $sieve \
    --feedback-metric ndcg.cut_10 \
    --clusters $root/cluster/04/kmeans-mini.csv \
    --seed $seed
EOF

                sbatch \
                    --mem=150G \
                    --time=12:00:00 \
                    --mail-type=ALL \
                    --mail-user=jsw7@nyu.edu \
                    --nodes=1 \
                    --cpus-per-task=2 \
                    --job-name=pick_$strategy-$sieve-$topic \
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
