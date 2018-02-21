#!/bin/bash

module try-load pbzip2/intel/1.1.13

workers=20
hours=1
while getopts "r:t:ch" OPTION; do
    case $OPTION in
	r) run=$OPTARG ;;
	t) hours=$OPTARG ;;
	c) clean=1 ;;
        h)
            exit
            ;;
        *) exit 1 ;;
    esac
done

models=(
    ua
    sa
    u1
    uaw
    saw
    un # Hardest last!
)

for i in $run/pseudoterms/*; do
    ngrams=`basename --suffix=.tar.bz $i`

    queries=$run/queries/$ngrams
    if [ $clean ]; then
	rm --recursive --force $queries
    fi
    mkdir --parents $queries

    job=`mktemp`
    cat <<EOF > $job
#!/bin/bash

tar \
    --extract \
    --use-compress-prog=pbzip2 \
    --file=$i \
    --directory=\$SLURM_JOBTMP

python3 $ZR_HOME/scripts/retrieve/make.py \
    --model `sed -e's/ / --model /g' <<< ${models[@]}` \
    --term-files \$SLURM_JOBTMP/$ngrams \
    --output $queries \
    --workers $workers
EOF

    echo -n "$ngrams $job "
    sbatch \
	--mem=60G \
	--time=$hours:00:00 \
	--nodes=1 \
	--cpus-per-task=$workers \
	--job-name=query-$ngrams \
	$job
done
