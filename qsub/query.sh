#!/bin/bash

memory=60
hours=6
count=1000
models=(
    ua
    sa
    u1
    un
    uaw
    saw
)

while getopts "r:h" OPTION; do
    case $OPTION in
	r) root=$OPTARG ;;
	h)
	    cat<<EOF
$0 [options]
     -r top level run directory (usually directory containing the
        directory of trees)
EOF
	    exit
	    ;;
        *) exit 1 ;;
    esac
done

rm --force jobs
for i in $root/indri/*; do
    qsub=`mktemp`
    echo $i $qsub
    cat <<EOF > $qsub
root=$root
terms=`basename $i`
for j in ${models[@]}; do
EOF
    cat <<"EOF" >> $qsub
    echo $terms $j

    queries=$root/queries/$terms/$j
    rm --recursive --force $queries
    mkdir --parents $queries

    find $root/pseudoterms/$terms -name 'WSJQ*' | \
	python $HOME/src/pyzrt/src/term2query.py \
	--output $queries \
	--model $j
done
echo $terms DONE
EOF
    qsub \
	-j oe \
	-l nodes=1:ppn=20,mem=${memory}GB,walltime=${hours}:00:00 \
	-m abe \
	-M jsw7@nyu.edu \
	-N query \
	-V \
	$qsub >> jobs
done
