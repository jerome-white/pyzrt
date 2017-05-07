#!/bin/bash

n=4
m=12
cpus=10

while getopts "c:m:n:h" OPTION; do
    case $OPTION in
        c) corpus=$OPTARG ;;
        m) m=$OPTARG ;;
        n) n=$OPTARG ;;
        h)
            cat <<EOF
$0 -c corpus (\$o3 in $ZR_HOME/qsub/corpus.sh)
   -m maximum n-gram length (default $m)
   -n minimum n-gram length (default $n)
EOF
            exit
            ;;
        *) exit 1 ;;
    esac
done

output=`dirname $corpus`/trees
if [ -e $output ]; then
    existing="--existing $output/`ls --sort=time $output | head --lines=1`"
else
    mkdir --parents $output
fi

job=`mktemp`
cat <<EOF > $job
python3 -u $ZR_HOME/src/stree.py $existing \
    --input $corpus \
    --output $output \
    --min-gram $n \
    --max-gram $m \
    --prune 1 \
    --workers $cpus \
    --incremental
EOF

sbatch \
    --mem=492G \
    --time=2-0 \
    --mail-type=ALL \
    --mail-user=jsw7@nyu.edu \
    --nodes=1 \
    --cpus-per-task=$cpus \
    --job-name=reveal-suffix \
    $job

# leave a blank line at the end
