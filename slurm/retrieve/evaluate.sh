#!/bin/bash

#SBATCH --mem=60G
#SBATCH --time=1:00:00
#SBATCH --nodes=1
#SBATCH --cpus-per-task=20
#SBATCH --job-name=query

count=1000
while getopts "r:c:h" OPTION; do
    case $OPTION in
        r) run=$OPTARG ;;
	c) count=$OPTARG ;;
        *) exit 1 ;;
    esac
done

module try-load parallel/20171022

root=$run/trec
rm --recursive --force $root
find $run/indri -size 0 -delete

for i in $run/indri/*; do
    ngrams=`basename $i`
    for j in $i/*; do
	stem=`basename $j`
	topic=`cut --delimiter='.' --fields=1 <<< $stem`
	qrels=$BEEGFS/qrels/ao/$topic

	if [ -e $qrels ]; then
	    echo $j 1>&2

	    output=$root/$ngrams
	    mkdir --parents $output

	    cat <<EOF
trec_eval -q -c -n -M$count -mall_trec $qrels $j > $output/$stem
EOF
	fi
    done
done | parallel --line-buffer

find $root -size 0 -delete
