# M10E-A fixed experiment protocol

The strategy definitions and gates below were recorded before the real experiment.
The closure and future-storage policy sections were added after acceptance.
These 75 frozen M10D questions are a
development benchmark. No M10E-B holdout is created or inspected. These are
retrieval metrics, not legal-answer accuracy. Production adoption is deferred
to M10F after blind validation.

## Strategies fixed before measurement

- B0: read `reports/evaluation/m10d-two-law-retrieval.json`; never rerun B0.
- B1: in-memory BM25 on persisted `article_title`, `section_context` and
  document text, joined with newlines. No synthetic law/article labels, gold,
  stopword removal, stemming, rewriting or model-based processing.
  NFC normalization; map Turkish `I` to `ı` and `İ` to `i`, then Unicode
  lowercase and split into Unicode alphanumeric tokens (underscore splits).
  Query terms are unique. Score is the sum over query terms of
  `ln(1+(N-df+0.5)/(df+0.5)) * tf*(k1+1)/(tf+k1*(1-b+b*dl/avgdl))`.
  Fixed `k1=1.5`, `b=0.75`. Only positive-score candidates participate;
  no lexical overlap returns an empty list. Top-20 candidates, Top-5 output.
- B2: one original-query production dense Top-20 call per question, reused
  locally. Fuse dense and lexical Top-20 by `sum(1/(60+rank))`; absent
  membership contributes zero. Descending score, ascending chunk-ID ties.
- B3: deduplicate the entire B2 candidate list before taking Top-5, retaining
  the first chunk per existing M10D QualifiedSourceKey. Distinct laws,
  article numbers and article types remain distinct. This identity is scoped
  to M10D; future document identity is deferred to M11.
- B4: **skipped before measuring results**. Similar titles, sections and legal
  wording can identify complementary provisions. There is no independently
  justified similarity penalty for this corpus; adding one would introduce
  an arbitrary relevance/diversity tradeoff. No parameter search is performed.

Experiment constants live in `src/config.py` as fixed M10E-only values;
production settings and behavior are unchanged. All algorithm and orchestration
code is isolated in `src/evaluate_retrieval_experiments.py`.

## Gates and interpretation

Run `python -m pytest -q` with `RUN_OPENAI_INTEGRATION_TESTS=0` before real
collection. Any failure stops the experiment. The real CLI requires both
`OPENAI_API_KEY` (environment/.env only) and `RUN_OPENAI_INTEGRATION_TESTS=1`.
OpenAI SDK retries are disabled. There is one production `retrieve()` call
per original question, with `top_k=20` and no filters. No generation occurs.

The runner opens only the existing collection, reads IDs/documents/metadata,
and verifies 5326=53, 4458=276, total=329. Pre/post sorted ID sets and full
document/metadata hashes must match; hashes of every storage file additionally
measure physical byte stability of the storage files; they do not provide a
logical embedding fingerprint. The original snapshots did not request embeddings.
Every frozen input/report hash must remain unchanged. No collection mutation
API is used. Normal tests use synthetic records and frozen reports only.

The JSON is exclusively created before the first request and checkpointed
before/after each dense call. Existing output blocks a second real run,
including after interruption. Cached candidates contain IDs, keys, distances,
scores, usage and timing, never embeddings or corpus text. Failed runs stop
without automatic resumption or retry.

Prefix integrity separately compares ordered Top-5 chunk IDs and ordered
QualifiedSourceKeys to frozen B0. Exact ranking means chunk order, not bitwise
distance equality. Differences never replace B0.

For candidate selection, compare exact unrounded B0 rates (43/45 ANY@5 and
40/45 ALL@5 for 5326), not the rounded 95.6%/88.9% labels. Require both 5326
rates preserved, both 4458 Top-5 rates strictly improved, combined Top-1 law
hit at least 72/75, 4458 multi_part ALL@5 strictly improved, and 4458
single-source ANY@5 preserved. This conservatively treats any law-hit drop
as degradation. Among eligible strategies prefer 4458 ALL@5, then ANY@5,
then the simpler strategy. Report regressions as well as improvements.

Latency is descriptive: B0 comes from its historical run; B1 is local lexical
time; B2 sums shared dense time, lexical time and fusion; B3 adds deduplication.
Report index construction separately. Report I/O is excluded. Shared dense
tokens/time are attributed per variant for cost comparison but paid only once;
do not sum them across B2/B3. Final normal tests again disable integrations.

## Accepted M10E-A closure

M10E-A is closed as a **qualified development experiment**. The single real
run remains 75 dense calls and 3,205 query-embedding tokens; its authoritative
JSON/CSV, rankings and metrics are preserved unchanged. The historical storage
gate failure remains recorded; acceptance does not imply byte-level immutability
or establish that the production collection is corrupted.

```text
logical_record_integrity: PASS
stored_embeddings_post_snapshot: VERIFIED
embedding_vector_count: 329
embedding_dimension: 1536
pre_post_embedding_equality: UNPROVEN
reason: no compatible pre-M10E full embedding fingerprint exists
explicit_application_mutation_api_calls: 0
physical_storage_byte_stability: FAIL
changed_files_observed_during_read_lifecycle:
  - chroma.sqlite3
  - data_level0.bin
  - length.bin
physical_storage_change_cause: UNRESOLVED
```

Final strategy decisions:

- **B1: rejected** ? fails 5326 preservation / weaker law selection.
- **B2: qualified development candidate** ? no production adoption yet.
- **B3: not preferred** ? same aggregate retrieval metrics as B2, with
  additional deduplication complexity.
- **B4: intentionally skipped before measurement** ? remains skipped;
  no strategy is introduced after seeing results.

The combined non-expected-legislation share@5 increase from **6.93% to 8.27%**
is a **tradeoff, not a failure**: B2 improves exact-source retrieval substantially
while slightly increasing other-law presence deeper in Top-5.

Preserved development results (percentages):

| Metric | B0 | B2 |
|---|---:|---:|
| 5326 ANY@5 | 95.6 | 97.8 |
| 5326 ALL@5 | 88.9 | 97.8 |
| 4458 ANY@5 | 80.0 | 86.7 |
| 4458 ALL@5 | 76.7 | 86.7 |
| Combined ANY@5 | 89.3 | 93.3 |
| Combined ALL@5 | 84.0 | 93.3 |
| 4458 multi_part ALL@5 | 50.0 | 66.7 |
| Combined Legislation Hit@1 | 96.0 | 97.3 |
| Combined non-expected-legislation share@5 | 6.93 | 8.27 |

See the [experiment report](../reports/evaluation/m10e-retrieval-experiments.md)
and [forensic report](../reports/evaluation/m10e-storage-forensics.md).

## Experimental storage policy for future work

Because Chroma 1.5.9 was observed to change physical persistent-storage files
during a read-only client lifecycle, future evaluation experiments must not
operate directly on the production persistence directory. For M10E-B and later:

1. Create a byte-for-byte filesystem copy of the production Chroma directory
   before opening it with Chroma.
2. Verify the copy's file hashes equal the source at copy time.
3. Run all experimental retrieval against the copy.
4. Allow any internal Chroma housekeeping to affect only the copy.
5. Never infer production mutation from changes to the experimental copy.

Production adoption/indexing milestones may still use the production collection
explicitly when writes are intended. This policy does not authorize a new run,
copy creation, or M10E-B holdout creation during M10E-A closure. The historical
M10E-A runner and one-shot forensic script must not be rerun for future work;
future runners must implement this copy policy before evaluation.
