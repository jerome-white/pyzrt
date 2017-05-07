#!/bin/bash

#PBS -V
#PBS -l nodes=1:ppn=4,mem=150GB,walltime=1:00:00
#PBS -m abe
#PBS -M jsw7@nyu.edu
#PBS -N pyzrt-cluster
#PBS -j oe

path=$SCRATCH/zrt/wsj/2017_0118_020518
output=$path/cluster/04

mkdir --parents $output

python3 -u $ZR_HOME/src/cluster.py \
    --input $path/pseudoterms/04 \        
    --output $output/kmeans.csv
