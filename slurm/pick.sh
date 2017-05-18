#!/bin/bash

n=4
seed_size=1
zrt=$SCRATCH/zrt
metric=ndcg_cut.10
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
                path=$root/picker/$ngrams/$strategy/$sieve
                mkdir --parents $path

                sequence=1
                while :; do
                    output=$path/WSJQ00${topic}-`printf "%04d" $sequence`
                    if [ ! -e $output ]; then
                        break
                    fi
                    (( sequence++ ))
                    if [ $sequence -gt 9999 ]; then
                        echo "ERROR: No more sequence numbers" >&2
                        exit 1
                    fi
                done

                job=`mktemp`
                cat <<EOF >> $job
#!/bin/bash

python3 -u $ZR_HOME/src/support/qrels.py \
    --input $zrt/qrels.251-300.parts1-5.tar.gz \
    --output \$SLURM_JOBTMP \
    --topic $topic \
    --document-class WSJ \
    --count 1000

python3 -u $ZR_HOME/src/select/pick.py \
    --index $root/indri/$ngrams \
    --documents $root/pseudoterms/$ngrams \
    --output $output \
    --qrels \$SLURM_JOBTMP/$topic \
    --strategy $strategy \
    --technique $technique \
    --sieve $sieve \
    --feedback-metric $metric \
    --clusters $root/cluster/04/kmeans-mini.csv \
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
