QSUB scripts for running the various Python scripts that go from raw
data to results.

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
5. Process:
   o `retrieve.sh` Run and evaluate queries over Indri index.
   o `reveal.sh` Play the reveal game.
