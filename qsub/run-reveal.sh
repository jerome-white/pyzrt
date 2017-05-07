#!/bin/bash

strategies=(
    tf
    df
    random
    entropy
    relevance
    direct
    nearest
)

queries=( `seq 285 289` )
# queries=( 285 )

n=04
root=$SCRATCH/zrt/wsj/2017_0118_020518
for i in ${queries[@]}; do
    for j in ${strategies[@]}; do
	echo -n "$i $j "
	$ZR_HOME/qsub/reveal.sh \
	    -q $root/pseudoterms/$n/WSJQ00${i}-0000 \
	    -r $ZR_HOME/data/qrels.251-300.parts1-5.tar.gz \
	    -s $j \
	    -c 1000 \
	    -x ndcg_cut.10
    done
done
