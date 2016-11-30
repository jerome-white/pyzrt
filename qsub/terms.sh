#!/bin/bash

memory=60
hours=4

while getopts "r:fh" OPTION; do
    case $OPTION in
	r) root=$OPTARG ;;
	f) force=1 ;;
	h)
	    cat<<EOF
$0 [options]
     -r top level run directory (usually directory containing the
        directory of trees
     -f Force term creation even if output directory exists
EOF
	    exit
	    ;;
        *) exit 1 ;;
    esac
done

for i in $root/trees/*; do
    out=$root/pseudoterms/`basename $i .csv`
    if [ -d $out ] && [ ! $force ]; then
	continue
    fi
    mkdir --parents $out

    tmp=`mktemp`
cat <<EOF > $tmp
python3 $HOME/src/pyzrt/src/suffix2terms.py --suffix-tree $i --output $out
EOF
    qsub \
	-j oe \
	-l nodes=1:ppn=20,mem=${memory}GB,walltime=${hours}:00:00 \
	-m abe \
	-M jsw7@nyu.edu \
	-N pseudoterms \
	-V \
	$tmp
done > jobs

# leave a blank line at the end
