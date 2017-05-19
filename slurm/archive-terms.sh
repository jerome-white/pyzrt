#!/bin/bash

#SBATCH --mem=60G
#SBATCH --time=4:00:00
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=jsw7@nyu.edu
#SBATCH --nodes=1
#SBATCH --cpus-per-task=4
#SBATCH --job-name=archive

module load parallel/20161122

for i in $SCRATCH/zrt/wsj/${1}/pseudoterms/*; do
    j=`basename $i`
    cat <<EOF
tar \
    --create \
    --bzip2 \
    --file=$j.tar.bz \
    --directory=`dirname $i` \
    $j
EOF
done | parallel --no-notice
