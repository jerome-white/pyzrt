#!/bin/bash

#SBATCH --mem=492G
#SBATCH --time=2-0
#SBATCH --mail-type=ALL
#SBATCH --mail-user=jsw7@nyu.edu
#SBATCH --nodes=1
#SBATCH --cpus-per-task=10
#SBATCH --job-name=reveal-suffix

#
# Usage:
#
#  $> sbatch $0 m n path/to/toplevel existing
#
# where m and n are the n-gram range (minimum and maximum,
# respectively), and path/to/toplevel is the path to the directory
# containing the corpus directory.
#

output=${3}/trees
mkdir --parents $output
if [ ${4} ]; then
    existing="--existing ${4}"
fi

python3 -u $ZR_HOME/src/create/stree.py $existing \
    --input $corpus \
    --output $output \
    --min-gram ${1} \
    --max-gram ${2} \
    --prune 1 \
    --workers $SLURM_CPUS_PER_TASK \
    --incremental

for i in $output/*.csv; do
    echo bzip2 $i
done | parallel --no-notice
