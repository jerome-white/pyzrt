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
        # mkdir --parents $corpus/1990-1992
        for i in `seq 1990 1992`; do
            output=$corpus/$i
            mkdir --parents $output

            ls $SCRATCH/WSJ/$i/WSJ_* | \
	        python3 $HOME/src/pyzrt/archive.py \
                        --output-directory $output \
                        --archive-type WSJ
            # (cd $corpus/1990-1992; ln --symbolic ../$i/*)
        done
        ;;
    fragment)
        for i in $SCRATCH/WSJ.fmt/*; do
            python3 $HOME/src/pyzrt/fragment.py \
                --corpus-directory $i > \
                $SCRATCH/fragments_`basename $i`.csv
        done
        ;;
    similarity)
        python3 -u $HOME/src/pyzrt/similarity-gen.py \
            --corpus-directory $corpus \
            --fragment-file $fragments > \
            $SCRATCH/similarity.csv
        ;;
    dots)
        python3 $HOME/src/pyzrt/dot-gen.py \
	    --png $SCRATCH/wsj.png < \
	    $SCRATCH/similarity.csv
        ;;
    *)
        exit 1
        ;;
esac
