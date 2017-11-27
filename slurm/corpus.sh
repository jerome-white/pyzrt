#!/bin/bash

strainers=(
    space:lower:alpha # "standard"
    nospace:lower:alpha # no spaces
    pause:nospace:lower:alpha # no spaces, pauses as periods
)
documents=$HOME/etc/wsj/docs
workers=20

for i in ${strainers[@]}; do
    output=$BEEGFS/corpus/`sed -e's/:/_/g' <<< $i`

    jobs=`mktemp`
    cat <<EOF > $jobs
#!/bin/bash

rm --force --recursive $output
mkdir --parents $output

python $ZR_HOME/src/create/parse.py \
        --parser wsj \
        --documents $documents \
        --workers $workers \
        --output $output \
        --strainer $i
EOF
    sbatch \
        --mem=60GB \
        --time=60 \
        --cpus-per-task=$workers \
        --nodes=1 \
        --job-name=$i \
        $jobs
done
