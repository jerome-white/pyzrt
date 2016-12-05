#!/bin/bash

memory=60
hours=4

while getopts "r:fh" OPTION; do
    case $OPTION in
	r) root=$OPTARG ;;
	h)
	    cat<<EOF
$0 [options]
     -r top level run directory (usually directory containing the
        directory of trees
EOF
	    exit
	    ;;
        *) exit 1 ;;
    esac
done

for i in $root/trees/*; do
    index=$root/indri/`basename $i .csv`
    rm --recursive --force $index
    mkdir --parents $index

    tmp=`mktemp`
    for j in `seq 2`; do
	tmp=( ${tmp[@]} `mktemp --directory` )
    done

    cat <<EOF > ${tmp[0]}
python3 $HOME/src/pyzrt/src/suffix2terms.py \
  --suffix-tree $i \
  --output ${tmp[1]} \
  --documents-only

python3 $HOME/src/pyzrt/src/parse.py \
  --raw-data ${tmp[1]} \
  --output-data ${tmp[2]} \
  --parser pt \
  --strainer trec

IndriBuildIndex \
  -corpus.path=${tmp[2]} \
  -corpus.class=trectext \
  -index=$index

for i in ${tmp[@]}; do rm --recursive --force $i; done
EOF
    qsub \
	-j oe \
	-l nodes=1:ppn=20,mem=${memory}GB,walltime=${hours}:00:00 \
	-m abe \
	-M jsw7@nyu.edu \
	-N index \
	-V \
	$qsub
done > jobs

# leave a blank line at the end
