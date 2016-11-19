#!/bin/bash

count=1000
while getopts "q:t:c:r:" OPTION; do
    case $OPTION in
	q) qrels=$OPTARG ;;
	c) count=$OPTARG ;;
	r) results=$OPTARG ;;
        *) exit 1 ;;
    esac
done

trec_eval -q -c -M$count $qrels $results
