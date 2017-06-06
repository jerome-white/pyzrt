#!/bin/bash

strategies=(
    tf
    df
    random
    entropy
    relevance
    direct
    nearest
    feedback
)

# queries=( `seq 285 289` )
queries=( 259 )

n=04
root=$SCRATCH/zrt/wsj/2017_0118_020518
for i in ${queries[@]}; do
    for j in ${strategies[@]}; do
	case $j in
	    direct|nearest|feedback) sieve=( cluster term ) ;;
	    *) sieve=( _ ) ;;
	esac

	for k in ${sieve[@]}; do
	    echo -n "$i $j $k "
	    $ZR_HOME/slurm/reveal.sh \
		-q $root/pseudoterms/$n/WSJQ00${i}-0000 \
		-r $HOME/etc/wsj/qrels.251-300.parts1-5.tar.gz \
		-s $j \
		-c 1000 \
		-x ndcg_cut.10 \
		-v $k
	done
    done
done
