#!/bin/bash

#SBATCH --mem=300GB
#SBATCH --time=4:00:00
#SBATCH --cpus-per-task=4
#SBATCH --nodes=1
#SBATCH --job-name=pyzrt-cluster
#SBATCH --mail-type=ALL
#SBATCH --mail-user=jsw7@nyu.edu
#SBATCH --verbose
#SBATCH --verbose

path=$SCRATCH/zrt/wsj/2017_0118_020518
output=$path/cluster/04

mkdir --parents $output

python $ZR_HOME/src/support/cluster.py \
    --input $path/pseudoterms/04 \
    --output $output/kmeans-mini.csv
