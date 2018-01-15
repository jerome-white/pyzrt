#!/bin/bash

#
# symbol: non-punctuation non-alphanumeric removed
# lower: lower-cased
# alpha: non-alphanumeric removed
# space: whitespace regularization
# clobber: whitespace removed
# pause: punctuation regularized (as periods)
# phonetic: words translated to proununciation
#
strainers=(
    space:alpha:lower:symbol # standard (CIKM)
    clobber:alpha:lower:symbol
    pause:clobber:lower:symbol
    clobber:symbol:lower:phonetic:pause
)
documents=$HOME/etc/wsj/docs
workers=20

for i in ${strainers[@]}; do
    output=$BEEGFS/corpus/`sed -e's/:/_/g' <<< $i`

    job=`mktemp`
    cat <<EOF > $job
#!/bin/bash

rm --force --recursive $output
mkdir --parents $output

python $ZR_HOME/scripts/parse/parse.py \
        --parser wsj \
        --documents $documents \
        --workers $workers \
        --output $output \
        --strainer $i
EOF

    echo -n "$i $job "
    sbatch \
        --mem=60GB \
        --time=60 \
        --cpus-per-task=$workers \
        --nodes=1 \
        --job-name=$i \
        $job
done
