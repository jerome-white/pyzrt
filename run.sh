#!/bin/bash

while getopts "t:c:f:" OPTION; do
    case $OPTION in
        t) task=$OPTARG ;;
        c) corpus=$OPTARG ;;
        f) fragments=$OPTARG ;;
        *) exit 1 ;;
    esac
done

case $task in
    archive)
        for i in `seq 1990 1992`; do
            output=$SCRATCH/WSJ.fmt/$year
            mkdir --parents $output
            ls $SCRATCH/WSJ/$i/WSJ_* | \
	        python3 archive.py \
                        --output-directory $output \
                        --archive-type WSJ
        done
        ;;
    fragment)
        python3 fragment.py \
                --corpus-directory $SCRATCH/WSJ.fmt/1990 > \
                $SCRATCH/fragments.csv
        ;;
    similarity)
        python3 similarity_gen.py \
                --corpus-directory $corpus \
                --fragment-file $SCRATCH/fragments.csv
        ;;
    *)
        exit 1
        ;;
esac
