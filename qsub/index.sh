#!/bin/bash

memory=60
hours=4

install() {
    rm --recursive --force $1
    mkdir --parents $1
}

while getopts "r:tih" OPTION; do
    case $OPTION in
	r) root=$OPTARG ;;
	t) mkterms=1 ;;
	i) mkindex=1 ;;
	h)
	    cat<<EOF
$0 [options]
     -r top level run directory (usually directory containing the
        directory of trees)
     -t Generate term files from a suffix tree
     -i Generate Indri indexes from term files
EOF
	    exit
	    ;;
        *) exit 1 ;;
    esac
done

if [ ! $mkterms ] && [ ! $mkindex ]; then
    $0 -h
    exit 1
fi

rm --force jobs
for i in $root/trees/*; do
    term=`basename $i .csv`
    echo $term

    unset path
    for j in pseudoterms documents indri; do
	path=( ${path[@]} $root/$j/$term )
    done

    qsub=`mktemp`

    #
    # Convert the suffix trees to term files
    #
    if [ $mkterms ]; then
	install ${path[0]}
	cat <<EOF >> $qsub
python3 $HOME/src/pyzrt/src/suffix2terms.py \
  --suffix-tree $i \
  --output ${path[0]}
EOF
    fi
    
    #
    # Generate Indri indexes from term files
    #
    if [ $mkindex ]; then
	for j in ${path[@]:1}; do
	    install $j
	done
	cat <<EOF >> $qsub
find ${path[0]} -name 'WSJ*' -not -name 'WSJQ*' | \
  python3 $HOME/src/pyzrt/src/parse.py \
    --output-data ${path[1]} \
    --parser pt \
    --strainer trec \
    --consolidate

IndriBuildIndex \
  -corpus.path=${path[1]} \
  -corpus.class=trectext \
  -index=${path[2]}
EOF
    fi

    qsub \
	-j oe \
	-l nodes=1:ppn=20,mem=${memory}GB,walltime=${hours}:00:00 \
	-m abe \
	-M jsw7@nyu.edu \
	-N index \
	-V \
	$qsub >> jobs
done

# leave a blank line at the end
