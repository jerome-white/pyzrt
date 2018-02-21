#!/bin/bash

workers=20
count=1000

while getopts "r:t:c:h" OPTION; do
    case $OPTION in
	r) run=$OPTARG ;;
        w) workers=$OPTARG ;;
        c) count=$OPTARG ;;
        i) indri="--indri $OPTARG" ;;
        h)
            cat <<EOF
$0 options
 -r run
 -w workers (default $workers)
 -c count (default $count)
 -i indri (default `which IndriRunQuery`)
EOF
            exit
            ;;
        *) exit 1 ;;
    esac
done

for i in $run/queries/*; do
    ngrams=`basename $i`
    
    output=$run/trec/$ngrams
    # mkdir --parents $output

    job=`mktemp`
    cat <<EOF > $job
#!/bin/bash

python3 $ZR_HOME/scripts/retrieve/execute.py $indri \
  --index $run/indri/$ngrams \
  --qrels $BEEGFS/qrels/ao \
  --queries $i \
  --output $output \
  --ngrams $ngrams \
  --workers $workers
EOF

    echo -n "$ngrams $job "
    sbatch \
	--mem=60G \
	--time=2:00:00 \
	--nodes=1 \
	--cpus-per-task=$workers \
	--job-name=query-$ngrams \
	$job
done
