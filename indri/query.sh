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
    skip=$2
    unset q

    echo "<parameters>"
    sed -e's/[^[:alnum:][:space:]]//g' $1 | { \
	while read; do
	    if [ -z "$REPLY" ]; then
		if [ $skip -eq 0 ]; then
		    mkquery $n ${q[@]}
		    (( n++ ))
		fi
		skip=0
		unset q
	    else
		q=( ${q[@]} $REPLY )
	    fi
	done
	if [ ${#q[@]} -gt 0 ]; then
	    mkquery $n ${q[@]}
	fi
    }
    echo "</parameters>"
}

index=$HOME/data/pyzrt/indri
count=1000
with_topic=0
while getopts "i:q:c:t" OPTION; do
    case $OPTION in
        i) index=$OPTARG ;;
	q) queries=$OPTARG ;;
	c) count=$OPTARG ;;
	t) with_topic=1 ;; # include the topic description as a query
        *) exit 1 ;;
    esac
done

tmp=`mktemp`
mkqfile $queries $with_topic > $tmp
IndriRunQuery -count=$count -index=$index -trecFormat=true $tmp
rm $tmp
