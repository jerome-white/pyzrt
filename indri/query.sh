#!/bin/bash
#
# http://lemur.sourceforge.net/indri/IndriRunQuery.html
#

mkquery() {
    echo "<parameters>"

    n=0
    for i in $@; do
	cat <<EOF
<query>
  <type>indri</type>
  <number>$n</number>
  <text>`cat $i`</text>
</query>
EOF
	(( n++ ))
    done

    echo "</parameters>"
}

data=$HOME/data/pyzrt/indri
count=1000
while getopts "d:q:c:" OPTION; do
    case $OPTION in
        d) data=$OPTARG ;;
	q) queries=( ${queries[@]} $OPTARG ) ;;
	c) count=$OPTARG ;;
        *) exit 1 ;;
    esac
done

tmp=`mktemp`
mkquery ${queries[@]} > $tmp
IndriRunQuery -count=$count -index=$data -trecFormat=true $tmp
rm $tmp
