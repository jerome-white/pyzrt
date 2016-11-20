#!/bin/bash
#
# http://lemur.sourceforge.net/indri/IndriRunQuery.html
#

mkquery() {
    cat <<EOF
<query>
  <type>indri</type>
  <number>$1</number>
  <text>${@:2}</text>
</query>
EOF
}

mkqfile() {
    n=0
    include=$2
    unset q

    echo "<parameters>"
    sed -e's/[^[:alnum:][:space:]]//g' $1 | { \
	while read; do
	    if [ -z "$REPLY" ]; then
		if [ $include -eq 1 ]; then
		    mkquery $n ${q[@]}
		    (( n++ ))
		fi
		include=1
		unset q
	    else
		q=( ${q[@]} $REPLY )
	    fi
	done
	
	if [ ${#q[@]} -gt 0 ] && [ $2 -eq 1 ]; then
	    mkquery $n ${q[@]}
	fi
    }
    echo "</parameters>"
}

index=$HOME/data/pyzrt/indri
count=1000
with_topic=0
while getopts "i:q:c:th" OPTION; do
    case $OPTION in
        i) index=$OPTARG ;;
	q) queries=$OPTARG ;;
	c) count=$OPTARG ;;
	t) with_topic=1 ;;
	h)
	    cat <<EOF
$0
  -i location of index
  -q location of queries
  -c count
  -t (include the topic description as a query)
EOF
	    exit
	    ;;
        *)
	    $0 -h
	    exit 1
	    ;;
    esac
done

# mkqfile $queries $with_topic

tmp=`mktemp`
mkqfile $queries $with_topic > $tmp
IndriRunQuery -count=$count -index=$index -trecFormat=true $tmp
rm $tmp
