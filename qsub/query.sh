#!/bin/bash

models=(
    ua
    sa
    u1
    un
    uaw
    saw
)

while getopts "i:ph" OPTION; do
    case $OPTION in
	i) indri=$OPTARG ;;
        p) progressive=--progressive ;;
	h)
	    cat<<EOF
$0
   -i indri term indexes (subdirectory of
      \$root in \$ZR_HOME/qsub/index.sh)
   -p generate progressive queries
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
prog=$progressive

for j in ${models[@]}; do
EOF
    #
    # ... so their variable form can be left to interpretation.
    #
    cat <<"EOF" >> $qsub
    echo $terms $j

    output=$root/queries${prog}/$terms/$j
    rm --recursive --force $output
    mkdir --parents $output

    find $root/pseudoterms/$terms -name 'WSJQ*' | \
	python $ZR_HOME/src/term2query.py $prog --output $output --model $j
done
echo $terms DONE
EOF
    qsub \
	-j oe \
	-l nodes=1:ppn=20,mem=60GB,walltime=6:00:00 \
	-m abe \
	-M jsw7@nyu.edu \
	-N query$progressive \
	-V \
	$qsub >> jobs
done
