#!/bin/bash

n=4
m=12
ppn=20

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

qsub=`mktemp`
cat <<EOF > $qsub
python3 -u $ZR_HOME/src/stree.py $existing \
    --input $corpus \
    --output $output \
    --min-gram $n \
    --max-gram $m \
    --prune 1 \
    --workers `expr $ppn / 2` \
    --incremental
EOF

qsub \
    -j oe \
    -l nodes=1:ppn=$ppn,mem=492GB,walltime=48:00:00 \
    -m abe \
    -M jsw7@nyu.edu \
    -N reveal-suffix \
    -V \
    $qsub

# leave a blank line at the end
