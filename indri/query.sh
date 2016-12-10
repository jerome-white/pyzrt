#!/bin/bash
#
# http://lemur.sourceforge.net/indri/IndriRunQuery.html
#

count=1000
while getopts "r:c:q:h" OPTION; do
    case $OPTION in
	r) root=$OPTARG ;;
	c) count=$OPTARG ;;
	q) qrels=$OPTARG ;;
	h)
	    cat <<EOF
$0
  -i index
  -q queries
  -c count (default $count)
  -r relevance judgements (QRELS)
EOF
	    exit
	    ;;
        *)
	    $0 -h
	    exit 1
	    ;;
    esac
done

for i in $root/queries/*; do
    j=`basename $i`
    echo $j

    a=$root/retrieved
    mkdir --parents $a
    IndriRunQuery -count=$count -index=$root/index -trecFormat=true $i > $a/$j

    if [ $qrels ]; then
	b=$root/evals
	mkdir --parents $b
	trec_eval -q -c -M$count $qrels/`basename $i` $a/$j > $b/$j
    fi
done
