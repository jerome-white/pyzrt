#!/bin/bash

#SBATCH --mem=60G
#SBATCH --time=8:00:00
#SBATCH --nodes=1
#SBATCH --cpus-per-task=20
#SBATCH --job-name=query

while getopts "r:n:h" OPTION; do
    case $OPTION in
        r) run=$OPTARG ;;
	n) ngrams=$OPTARG ;;
        *) exit 1 ;;
    esac
done

module try-load pbzip2/intel/1.1.13
module try-load parallel/20171022

models=(
    ua
    sa
    u1
    uaw
    saw
    un # Hardest last!
)

output=$run/queries/$ngrams
if [ -d $output ]; then
    find $output -size 0 -delete 2> /dev/null
else
    mkdir --parents $output
fi

tar \
    --extract \
    --use-compress-prog=pbzip2 \
    --file=$run/pseudoterms/$ngrams.tar.bz \
    --directory=$SLURM_JOBTMP

for i in ${models[@]}; do
    for j in $SLURM_JOBTMP/$ngrams/*; do
	doc=`basename $j`
	if [ ${doc:0:1} == 'Q' ]; then
	    out=$output/$doc.$i
	    if  [ ! -e $out ]; then
		cat <<EOF
python3 $ZR_HOME/scripts/retrieve/mkquery.py \
    --model $i \
    --document $j \
    --number ${doc:1} > $out
EOF
	    fi
	fi
    done
done | parallel --line-buffer
