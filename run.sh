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
        mkdir --parents $corpus/1990-1992
        for i in `seq 1990 1992`; do
            output=$corpus/$year
            mkdir --parents $output
            ls WSJ/$i/WSJ_* | \
	        python3 archive.py \
                        --output-directory $output \
                        --archive-type WSJ
            (cd $corpus/1990-1992; ln --symbolic ../$year/*)
        done
        ;;
    fragment)
        for i in $SCRATCH/WSJ.fmt/*; do
            python3 fragment.py \
                    --corpus-directory $i > \
                    $SCRATCH/fragments-`basename $i`.csv
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
