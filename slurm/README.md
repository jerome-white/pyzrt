Bash scripts that submit Python jobs to sbatch (SLURM). Scripts go
from raw data to results.

## Create

1. `corpus.sh` Format various raw documents into a consistent TREC
   format and place them into a single location:
   1. Generate the queries based on the topic files.
   2. Put queries into TREC format.
   3. Builds the corpus by reading in TREC formatted data.
2. `suffix.sh` Build the suffix tree.
3. `index.sh` Build the Indri index:
   1. Convert the suffix trees to term files.
   2. Put term files into TREC format.
   3. Generate Indri indexes based on TREC formatted documents.
4. `query.sh` Build Indri-friendly queries from the TREC formatted
   queries (Step 1.2).

## Process

* `retrieve.sh` Run and evaluate queries over Indri index.
* `reveal.sh` Play the reveal game.
* `cluster.sh` Build document clusters to support document filtering
