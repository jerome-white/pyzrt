#!/bin/bash

#SBATCH --mem=60G
#SBATCH --time=4:00:00
#SBATCH --mail-type=ALL
#SBATCH --mail-user=jsw7@nyu.edu
#SBATCH --nodes=1
#SBATCH --cpus-per-task=20
#SBATCH --job-name=index

module load pbzip2/intel/1.1.13

#
# Usage:
#
#  $> sbatch $0 path/to/toplevel $file
#
# where
#    - path/to/toplevel is the path to the directory containing the
#      trees
#    - file to aquire
#

output=$BEEGFS/`basename --suffix='.sh' ${0}`/${2}

for i in ${1}/*.bz; do
    ngrams=`basename --suffix='.tar.bz' $i`
    echo $ngrams

    mkdir --parents $output
    tar \
	--extract \
	--use-compress-prog=pbzip2 \
	--directory=$output/$ngrams \
	--file=$i \
	$ngrams/${2}
done
