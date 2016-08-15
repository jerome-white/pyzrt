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
        for i in `seq 1990 1992`; do
            python3 fragment.py \
                    --corpus-directory $SCRATCH/WSJ.fmt/$i > \
                    $SCRATCH/fragments-$i.csv
        done
        ;;
    similarity)
        python3 -u similarity-gen.py \
                --corpus-directory $corpus \
                --fragment-file $SCRATCH/fragments.csv >\
                $SCRATCH/similarity.csv
        ;;
    dots)
        python3 dot-gen.py --png $SCRATCH/wsj.png < $SCRATCH/similarity.csv
        ;;
    *)
        exit 1
        ;;
esac
