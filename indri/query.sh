#!/bin/bash
#
# http://lemur.sourceforge.net/indri/IndriRunQuery.html
#

count=1000
while getopts "i:q:c:r:o:h" OPTION; do
    case $OPTION in
        i) index=$OPTARG ;;
	q) queries=$OPTARG ;;
	c) count=$OPTARG ;;
	r) qrels=$OPTARG ;;
	o) output=$OPTARG ;;
	h)
	    cat <<EOF
$0
  -i index
  -q queries
  -c count (default $count)
  -r relevance judgements (QRELS)
  -o output
EOF
	    exit
	    ;;
        *)
	    $0 -h
	    exit 1
	    ;;
    esac
done

for i in $queries; do
    results=$i.trec
    IndriRunQuery -count=$count -index=$index -trecFormat=true $i > $results
    if $qrels; then
	trec_eval -q -c -M$count $qrels $results
    fi
done
