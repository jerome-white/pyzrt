#!/bin/bash

basic=lower:symbol
standard=space:alpha:$basic
strainers=(
    $standard # "standard"
    clobber:$standard # no spaces
    pause:clobber:$basic # no spaces, pauses as periods
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
