#!/bin/bash

models=(
    ua
    sa
    u1
    un
    uaw
    saw
)

unset action
while getopts "i:a:h" OPTION; do
    case $OPTION in
	i) indri=$OPTARG ;;
        a) action=$OPTARG ;;
	h)
	    cat<<EOF
$0
   -i indri term indexes (subdirectory of
      \$root in \$ZR_HOME/qsub/index.sh)
EOF
	    exit
	    ;;
        *) exit 1 ;;
    esac
done

rm --force jobs
for i in $indri/*; do
    job=`mktemp`
    echo $i $job

    #
    # Establish the variables within the script...
    #
    cat <<EOF > $job
root=`dirname $indri`
terms=`basename $i`
action=$action

for j in ${models[@]}; do
EOF
    #
    # ... so their variable form can be left to interpretation.
    #
    cat <<"EOF" >> $job
    echo $terms $j

    output=$root/queries/$action/$terms/$j
    rm --recursive --force $output
    mkdir --parents $output

    find $root/pseudoterms/$terms -name 'WSJQ*' | \
	python $ZR_HOME/src/term2query.py \
               --action $action \
               --output $output \
               --model $j
done
echo $terms DONE
EOF
    sbatch \
        --mem=60G \
        --time=6:00:00 \
        --mail-type=ALL \
	--mail-user=jsw7@nyu.edu \
        --nodes=1 \
        --cpus-per-task=20 \
        --job-name=query-$action \
        $job >> jobs
done
