#!/bin/bash

#SBATCH --mem=150GB
#SBATCH --time=60
#SBATCH --ntasks=4
#SBATCH --nodes=1
#SBATCH --job-name=pyzrt-cluster
#SBATCH --mail-type=ALL

path=$SCRATCH/zrt/wsj/2017_0118_020518
output=$path/cluster/04

mkdir --parents $output

python3 -u $ZR_HOME/src/cluster.py \
    --input $path/pseudoterms/04 \        
    --output $output/kmeans.csv
