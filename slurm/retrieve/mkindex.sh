#!/bin/bash

workers=20
indri=`which IndriBuildIndex`

while getopts "r:i:w:h" OPTION; do
    case $OPTION in
	r) run=$OPTARG ;;
	i) indri=$OPTARG ;;
	w) workers=$OPTARG ;;
        h)
            exit
            ;;
        *) exit 1 ;;
    esac
done

module load pbzip2/intel/1.1.13

tmp=`mktemp --directory --tmpdir=$BEEGFS`
rm --recursive --force $run/index

for i in $run/pseudoterms/*; do
    ngrams=`basename --suffix=.tar.bz $i`

    documents=$tmp/$ngrams
    index=$run/index/$ngrams

    for j in $documents $index; do
	mkdir --parents $j
    done

    job=`mktemp`

    cat <<EOF > $job
#!/bin/bash

tar \
    --extract \
    --use-compress-prog=pbzip2 \
    --directory=\$SLURM_JOBTMP \
    --file=$run/pseudoterms/${ngrams}.tar.bz

find \$SLURM_JOBTMP/$ngrams -regextype posix-awk -regex '.*/[0-9]{4}' | \
  python3 $ZR_HOME/scripts/parse/to-indri.py \
    --output $documents \
    --workers $workers \
    --consolidate

$indri \
  -corpus.path=$documents \
  -corpus.class=trectext \
  -index=$index

rm --recursive --force $documents
EOF

    echo -n "$ngrams $job "
    sbatch \
	--mem=60G \
	--time=4:00:00 \
	--nodes=1 \
	--cpus-per-task=$workers \
	--job-name=index-$ngrams \
	$job
done
