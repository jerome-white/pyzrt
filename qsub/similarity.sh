#!/bin/bash

OUTPUT=$SCRATCH/zrt/wsj

while getopts "n:m:t:ch" OPTION; do
    case $OPTION in
	c)
	    for i in ledger similarity; do
		j=$OUTPUT/$i
		rm --recursive --force $j
		mkdir --parents $j
	    done
	    ;;
        n) nodes=$OPTARG ;;
	m) memory=$OPTARG ;;
	t) hours=$OPTARG ;;
	h)
	    cat<<EOF
$0 [options]
     -n nodes
     -t hours
     -m memory
     -c (clean existing files?)
EOF
	    exit
	    ;;
        *) exit 1 ;;
    esac
done

block_size=4
mkdir --parents $OUTPUT/similarity
touch $OUTPUT/lock

for i in `seq $nodes`; do
    j=`expr $i - 1`
    tmp=`mktemp`
cat <<EOF > $tmp
python3 $HOME/src/pyzrt/src/similarity.py \
    --node $j \
    --total-nodes $nodes \
    --tokens $OUTPUT/tokens/${block_size}.csv \
    --corpus $OUTPUT/corpus \
    --ledger $OUTPUT/ledger \
    --barrier $OUTPUT/lock \
    --mmap $OUTPUT/similarity/$block_size \
    --compression 0.001
EOF

    qsub \
	-j oe \
	-l nodes=1:ppn=20,mem=${memory}GB,walltime=${hours}:00:00 \
	-m abe \
	-M jsw7@nyu.edu \
	-N similarity \
	-V \
	$tmp
done > jobs

# leave a blank line at the end
