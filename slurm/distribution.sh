#!/bin/bash

module load pbzip2/intel/1.1.13

workers=20
while getopts "r:h" OPTION; do
    case $OPTION in
        r) root=$OPTARG ;;
        h)
            exit
            ;;
        *) exit 1 ;;
    esac
done

output=$root/distributions
rm --recursive --force $output
mkdir --parents $output

for i in $root/pseudoterms/*.tar.bz; do
    ngrams=`basename --suffix=.tar.bz $i`
    job=`mktemp`

    echo -n "$ngrams $job "
    cat <<EOF > $job
#!/bin/bash

tar \
    --extract \
    --use-compress-prog=pbzip2 \
    --directory=\$SLURM_JOBTMP \
    --file=$i

python $ZR_HOME/scripts/zrt/distribution.py \
       --terms \$SLURM_JOBTMP/$ngrams \
       --output $output \
       --creator simulator \
       --version $ngrams \
       --workers $workers
EOF

    sbatch \
        --mem=60G \
        --time=60 \
        --nodes=1 \
        --cpus-per-task=$workers \
        --job-name=dist-$ngrams \
        $job
done
