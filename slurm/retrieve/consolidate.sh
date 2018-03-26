#!/bin/bash

#SBATCH --mem=60G
#SBATCH --time=1:00:00
#SBATCH --nodes=1
#SBATCH --cpus-per-task=20
#SBATCH --job-name=query

while getopts "r:h" OPTION; do
    case $OPTION in
        r) run=$OPTARG ;;
        *) exit 1 ;;
    esac
done

module try-load parallel/20171022

root=$run/evals
rm --recursive --force $root
mkdir --parents $root

for i in $run/trec/*; do
    ngrams=`basename $i`
    for j in $i/*; do
	info=( `basename $j | \
	    cut --delimiter='.' --fields=1- --output-delimiter=' '` )
	output=`mktemp --tmpdir=$root XXXXXX.csv`
	cat <<EOF
python $ZR_HOME/scripts/parse/trec.py \
    --query ${info[0]} \
    --model ${info[1]} \
    --ngrams $ngrams \
    < $j \
    > $output
EOF
    done
done | parallel --line-buffer
