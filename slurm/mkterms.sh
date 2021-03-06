#!/bin/bash

#SBATCH --mem=60G
#SBATCH --time=3:00:00
#SBATCH --mail-type=ALL
#SBATCH --mail-user=jsw7@nyu.edu
#SBATCH --nodes=1
#SBATCH --cpus-per-task=20
#SBATCH --job-name=index

#
# Usage:
#
#  $> sbatch $0 n path/to/toplevel version
#
# {1} n                 number of n-grams to work with
# {2} path/to/toplevel  path to the directory containing the trees
#                       ($output in $ZR_HOME/qsub/suffix.sh)
# {3} version           Tree format version (optional)
#

module load pbzip2/intel/1.1.13

ngrams=`printf "%02.f" ${1}`
tree=${2}/trees/${ngrams}.csv
if [ ${3} ]; then
    version="--version ${3}"

    case ${3} in
	1) ;; # find padding for Python-based suffix tree
	2)
	    padding=`cut --delimiter=',' --fields=2 $tree | \
		sort --parallel=$SLURM_CPUS_ON_NODE |
		uniq |
		wc --lines`
	    padding="--padding ${#padding}"
	    ;;
	*)
	    exit 1
	    ;;
    esac
fi

#
# Convert the suffix trees to term files
#

terms=$SLURM_JOBTMP/$ngrams
mkdir $terms

python3 -u $ZR_HOME/src/create/suffix2terms.py $version $padding \
  --suffix-tree $tree \
  --output $terms

#
# Archive the term files
#

pseudoterms=${2}/pseudoterms
mkdir --parents $pseudoterms

tar \
    --create \
    --use-compress-prog=pbzip2 \
    --file=$pseudoterms/$ngrams.tar.bz \
    --directory=`dirname $terms` \
    `basename $terms`
