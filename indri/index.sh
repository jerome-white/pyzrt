#!/bin/bash
#
# http://lemur.sourceforge.net/indri/IndriIndexer.html
#

data=$HOME/data/pyzrt
while getopts "d:" OPTION; do
    case $OPTION in
        d) data=$OPTARG ;;
        *) exit 1 ;;
    esac
done

index=$data/indri
rm --recursive --force $index
mkdir --parents $index

IndriBuildIndex \
    -corpus.path=$data/raw \
    -corpus.class=trectext \
    -index=$index
