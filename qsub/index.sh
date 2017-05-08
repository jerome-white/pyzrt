#!/bin/bash

install() {
    rm --recursive --force $1
    mkdir --parents $1
}

while getopts "t:fih" OPTION; do
    case $OPTION in
	t) trees=$OPTARG ;;
	f) mkterms=1 ;;
	i) mkindex=1 ;;
	h)
	    cat<<EOF
$0 -t trees (\$output in $ZR_HOME/qsub/suffix.sh)
   -f Generate term files from a suffix tree
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

root=`dirname $trees`

rm --force jobs
for i in $trees/*; do
    term=`basename $i .csv`
    echo $term

    unset path
    for j in pseudoterms documents indri; do
	path=( ${path[@]} $root/$j/$term )
    done

    job=`mktemp`

    #
    # Convert the suffix trees to term files
    #
    if [ $mkterms ]; then
	install ${path[0]}
	cat <<EOF >> $job
python3 $ZR_HOME/src/suffix2terms.py \
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
	cat <<EOF >> $job
find ${path[0]} -name 'WSJ*' -not -name 'WSJQ*' | \
  python3 $ZR_HOME/src/parse.py \
    --output ${path[1]} \
    --parser pt \
    --strainer trec \
    --consolidate

IndriBuildIndex \
  -corpus.path=${path[1]} \
  -corpus.class=trectext \
  -index=${path[2]}
EOF
    fi

    sbatch \
        --mem=60G \
        --time=4:00:00 \
        --mail-type=ALL \
	--mail-user=jsw7@nyu.edu \
        --nodes=1 \
        --cpus-per-task=20 \
        --job-name=index \
        $job >> jobs
done

# leave a blank line at the end
