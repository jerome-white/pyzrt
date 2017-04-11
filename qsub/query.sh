#!/bin/bash

models=(
    ua
    sa
    u1
    un
    uaw
    saw
)

while getopts "r:c:h" OPTION; do
    case $OPTION in
	i) indri=$OPTARG ;;
	h)
	    cat<<EOF
$0 -i indri term indexes (subdirectory of \$root in \$ZR_HOME/qsub/index.sh)
EOF
	    exit
	    ;;
        *) exit 1 ;;
    esac
done

rm --force jobs
for i in $indri/*; do
    qsub=`mktemp`
    echo $i $qsub

    #
    # Establish the variables within the script...
    #
    cat <<EOF > $qsub
root=`dirname $indri`
terms=`basename $i`
for j in ${models[@]}; do
EOF
    #
    # ... so their variable form can be left to interpretation.
    #
    cat <<"EOF" >> $qsub
    echo $terms $j

    queries=$root/queries/$terms/$j
    rm --recursive --force $queries
    mkdir --parents $queries

    find $root/pseudoterms/$terms -name 'WSJQ*' | \
	python $ZR_HOME/src/term2query.py --output $queries --model $j
done
echo $terms DONE
EOF
    qsub \
	-j oe \
	-l nodes=1:ppn=20,mem=60GB,walltime=6:00:00 \
	-m abe \
	-M jsw7@nyu.edu \
	-N query \
	-V \
	$qsub >> jobs
done
