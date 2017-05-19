#!/bin/bash

#SBATCH --mem=32G
#SBATCH --time=4:00:00
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=jsw7@nyu.edu
#SBATCH --nodes=1
#SBATCH --cpus-per-task=4
#SBATCH --job-name=archive

module load parallel/20161122

for i in $SCRATCH/zrt/wsj/${1}/pseudoterms/*; do
    cat <<EOF
tar \
    --create \
    --bzip2 \
    --file=`basename $i`.tar.bz \
    --directory=`dirname $i` \
    $i
EOF
done | parallel --no-notice
