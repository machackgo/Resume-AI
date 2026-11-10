# Lakeside NLP Lab — retrieval project notes (synthetic)

## Retrieval pipeline
I built a hybrid retrieval pipeline for a community forum: BM25 keyword search plus sentence-embedding search,
merged with reciprocal rank fusion. The index covers 4,000 forum posts. Every generated answer cites the post
and the character span it quotes, so a grader can open the exact source.

## Evaluation
I wrote an evaluation harness with 120 hand-labelled questions. It reports recall@5 and citation accuracy for
each retrieval configuration, so changes to chunk size or fusion weights are compared on the same questions.
