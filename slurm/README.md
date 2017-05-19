Bash scripts that submit Python jobs to sbatch (SLURM). Scripts go
from raw data to results.

## Create

1. `corpus.sh` Format various raw documents into a consistent TREC
   format and place them into a single location:
   1. Generate queries based on topic files.
   2. Put queries into TREC format.
   3. Build corpus from TREC formatted data.
2. `suffix.sh` Build the suffix tree.
3. `index.sh` Build the Indri index:
   1. Convert suffix trees to term files.
   2. Put term files into TREC format.
   3. Generate Indri indexes based on TREC formatted documents.

## Process

* `cluster.sh` Build document clusters to support document filtering
* `reveal.sh` Search for terms in the corpus that correspond to a
  given "hidden" query.
* `pick.sh` Generate queries based on interactive analysis with the
  corpus.
