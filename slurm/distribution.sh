#!/bin/bash

module load pbzip2/intel/1.1.13

while getopts "r:n:h" OPTION; do
    case $OPTION in
        n) normalize=--normalize ;;
        r) root=$OPTARG ;;
        h)
            exit
            ;;
        *) exit 1 ;;
    esac
done

#
# Extract the term files
#

for i in $root/pseudoterms/*.tar.bz; do
    ngrams=`basename --suffix=.tar.bz $i`
    
    output=$root/distributions
    mkdir --parents $output

    job=`mktemp`
    echo -n "$ngrams $job "
    
    cat <<EOF > $job
#!/bin/bash

tar \
    --extract \
    --use-compress-prog=pbzip2 \
    --directory=\$SLURM_JOBTMP \
    --file=$i

python $ZR_HOME/scripts/zrt/distribution.py $normalize \
       --creator simulator \
       --terms \$SLURM_JOBTMP/$ngrams \
       --save $output/$ngrams \
       --plot $output/$ngrams
EOF

    sbatch \
        --mem=60G \
        --time=60 \
        --nodes=1 \
        --cpus-per-task=20 \
        --job-name=dist-$ngrams \
        $job
done
