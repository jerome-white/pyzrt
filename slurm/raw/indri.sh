#!/bin/bash

#SBATCH --mem=60G
#SBATCH --time=1:00:00
#SBATCH --nodes=1
#SBATCH --cpus-per-task=20
#SBATCH --job-name=query

indri=`which IndriRunQuery`
count=1000
while getopts "r:i:h" OPTION; do
    case $OPTION in
        r) run=$OPTARG ;;
	i) indri=$OPTARG ;;
        *) exit 1 ;;
    esac
done

module try-load parallel/20171022

root=$run/indri
rm --recursive --force $root
find $run/queries -size 0 -delete

for i in $run/queries/*; do
    ngrams=`basename $i`

    output=$root/$ngrams
    mkdir --parents $output

    for j in $i/*; do
	echo $j 1>&2
	cat <<EOF
$indri -trecFormat=true -count=$count -index=$run/index/$ngrams $j > \
    $output/`basename $j`
EOF
    done
done | parallel --line-buffer
