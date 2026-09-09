# M10E-A storage forensics

The accepted single development benchmark is preserved: 75 dense calls and 3,205 query-embedding tokens. This inspection made one collection.get call, zero query/retrieval calls, zero OpenAI calls, and zero explicit collection mutation calls. No repair, restoration, reindex, holdout access, or commit was performed. Chroma itself changed physical bytes during the authorized read lifecycle.

## Logical persisted corpus integrity

All 329 embeddings were readable and finite, each dimension 1536. Counts: 5326=53; 4458=276. Sorted IDs, documents and canonical metadata match both original M10E PRE and POST snapshots. This is a new POST vector snapshot, not retrospective evidence of unchanged vectors.

- id_set_sha256: `3cc1f0c2cb4233d421c9651f5315f0bc2e5a7b769b5467e145dd9a0c80b1d429`
- document_metadata_sha256: `e85575a671dd0ab8a55ed15fd543e964d9e15f14389d88228510bfe0a5c96ee8`
- embedding_only_post_sha256: `7f6b9ea564919277cdc75f15305122c2dd6ae79ad055b235c3119360aa2693d3`
- full_logical_post_sha256: `8b164d939d25dd0c4a1739056e463c36e00878e855488e54ef5208e3f7a95c74`

Serialization is fully specified in [forensic JSON](m10e-storage-forensics.json) and implemented in [one-shot script](../../scripts/m10e_storage_forensics.py). Records sort by ID; metadata uses compact sorted-key UTF-8 JSON; vectors use explicit little-endian float32 C-order bytes. The full hash length-prefixes each record JSON and vector byte string with uint64 little-endian lengths. The embedding-only hash concatenates vectors in sorted-ID order; it is paired with the ID-set hash and shape. No raw text or vectors are exported.

## Earlier evidence search

No compatible earlier full embedding fingerprint was found. Inspected M10D JSON metadata and report/audit artifacts, the M10D audit at commit def6db6, the M10C indexing commit cf8bd76 and its reports/docs tree and indexing documentation change, and existing docs/report fingerprint references. M10D records counts and dataset hashes; its offline audit records physical-file equality, not a logical serialization of all 329 embeddings. M10C adds indexing compatibility but no full logical vector fingerprint. The 5326 metadata fixture is metadata-only and covers only that law. The M10E snapshot function explicitly requests only documents and metadatas.

**Direct PRE/POST embedding equality cannot be proven retrospectively from the available evidence: UNPROVEN.** No compatible comparison was performed. Physical file hashes cannot substitute for the missing logical vector fingerprint.

## Physical storage byte stability

Configured path: `C:\gumruk-chatbot\chroma`. Before hashes were taken before PersistentClient initialization; after hashes were taken immediately after its normal public client.close(). Only one logical get was performed, without filters or pagination, requesting documents, metadatas and embeddings. No count/query call was needed. Settings inspection was local. Telemetry was disabled and Python socket connection/DNS operations blocked. The script reserves its output exclusively before opening storage and refuses another execution.

The window covers initialization, get_collection, get and normal close together. It does not isolate their individual effects. No intermediate read or repeated trial was used to select an outcome. Both inventories contain five files; no files were added or removed. The three changed files are the same names observed during M10E, but these are new forensic before/after hashes.

- `448e5756-391d-4ede-87e8-7792e286ce3b/data_level0.bin`
  - Before: `20ccb38136aab1045c1dbd31ee292752355a95bc1e9e716d1b7e97358cebeda4`
  - After: `d4c2b22fe82c96e0e95d8e04e6a001e4ab6389d2e9b3fd1203ed948a1b9c3276`
  - Changed: **yes**
- `448e5756-391d-4ede-87e8-7792e286ce3b/header.bin`
  - Before: `b081be2c2276a57e995075c7de2f3cb25e903798aac36d98042045533ab28f7d`
  - After: `b081be2c2276a57e995075c7de2f3cb25e903798aac36d98042045533ab28f7d`
  - Changed: **no**
- `448e5756-391d-4ede-87e8-7792e286ce3b/length.bin`
  - Before: `1c18f71367d6809957499528a354b3bff1f592b4144f1791d6a8a14fa3ac5849`
  - After: `dce69fe0b66190d79c7847d28c6e2b9795abe6f8d5758e2715e9f409349f7809`
  - Changed: **yes**
- `448e5756-391d-4ede-87e8-7792e286ce3b/link_lists.bin`
  - Before: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
  - After: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
  - Changed: **no**
- `chroma.sqlite3`
  - Before: `c27782299f2cb01ed54c76a84cf7e61d5d3864406e9c8223c93c92c1c2dc8d4c`
  - After: `e758c270221cb128f3df0fb08d2301733148450d7d73c98595281f02f3f7988c`
  - Changed: **yes**

## Installed implementation evidence and limits

Installed Chroma version: **1.5.9**; actual backend: `chromadb.api.rust.RustBindingsAPI`. Source paths below are relative to `C:/Users/yaren/AppData/Local/Programs/Python/Python311/Lib/site-packages/`.

| Operation | Installed evidence | Supported interpretation |
|---|---|---|
| PersistentClient initialization | `chromadb/api/shared_system_client.py:21-39` creates and starts a System; `chromadb/config.py:120,238` selects Rust and default migrations=apply; `chromadb/api/rust.py:96-128` passes SQLite path, MigrationMode.Apply and persistence path into native Bindings. | Initialization is not a filesystem read-only open contract; migration-capable initialization occurs without application mutation APIs. No specific migration is proven to have run. |
| get_collection | `chromadb/api/client.py:239-277` delegates to server get_collection; `chromadb/api/rust.py:266-283` delegates to bindings.get_collection. | No create fallback in this path. Native internal writes cannot be excluded from the wrapper. |
| collection.get | `chromadb/api/models/Collection.py:129-177` delegates to _get; `chromadb/api/rust.py:400-466` delegates to bindings.get and converts embeddings to NumPy arrays. | The requested API reads stored data. No explicit mutation in Python; native loading/maintenance effects are not exposed here. |
| collection.query | `chromadb/api/models/Collection.py:194-280` delegates to _query; `chromadb/api/rust.py:550-604` calls bindings.query. | M10E used this read/search API with supplied query embeddings. This forensic inspection never called it. Its wrapper does not establish physical byte stability. |
| Normal close/process shutdown | `chromadb/api/client.py:590-636` documents resource/database release; `chromadb/api/shared_system_client.py:115-128` stops the final shared system; `chromadb/api/rust.py:130-131` deletes Bindings. | Normal close releases native resources. Destruction-time physical persistence is not proven from these Python sources; the measurement includes close. Process-exit-specific effects were not separately tested. |
| SQLite/WAL/checkpoint | Native SQLite config is constructed in `chromadb/api/rust.py:96-128`; Python SQLite implementation `chromadb/db/impl/sqlite.py:97-120,232-245` initializes migrations, applies SQL and closes its pool. | Legacy Python SQLite is not proof of active Rust behavior. No WAL/SHM files existed at either endpoint. A subsequent raw 100-byte SQLite header read found read/write version bytes 1/1. There is no evidence establishing a WAL checkpoint as the cause or excluding transient journaling. No SQLite connection, PRAGMA, checkpoint, or vacuum was issued during this investigation. |
| HNSW persistence/maintenance | Legacy `chromadb/segment/impl/vector/local_persistent_hnsw.py:138-168` can migrate max_seq_id on load; `:238-281` calls persist_dirty, writes metadata and updates SQL at a sync threshold; `:530-545` manages persistent file handles. | Concrete evidence that installed persistence code supports maintenance writes, but this legacy Python segment is not the active Rust execution path and cannot establish the cause here. |

The installed `chromadb_rust_bindings` package contains a compiled `.pyd` and Python loader, without Rust source. No site-packages files were edited. File names alone do not identify vector-value changes: index storage contains more than the returned logical embedding values. The endpoint observation demonstrates physical changes during the read lifecycle; it neither proves harmlessness nor establishes corruption. No syscall trace, intermediate snapshots, or native-source causal proof is available.

**physical storage byte changes are reproducible/observed but exact internal cause remains unresolved.**

## Explicit application mutation API audit

The real path in `src/evaluate_retrieval_experiments.py:307` calls `index.get_client().get_collection(..., embedding_function=None)` directly. Its snapshot uses get/count. Its dense collector calls `retrieve.retrieve`, which embeds the original query then calls `retrieve_by_embedding`; `src/retrieve.py:297` uses collection.query. Local BM25/RRF/dedup and report writes operate on in-memory records or report files.

`src/index.py` does contain get_or_create_collection in its get_collection helper and upsert in index_chunks, but neither helper is called by this experiment. Importing the module does not run its CLI. No executed application path calls collection add, upsert, update, delete, reset, delete_collection, create_collection, get_or_create_collection, reindex or rebuild. Ordinary dict.update/set.add calls are not Chroma mutations.

**Explicit application-level collection mutation API calls: 0**, supported by static analysis of the completed run's path and saved completion evidence, not a retroactively invented runtime trace. This does not mean underlying storage files were byte-identical.

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

## Preserved recommendation and experimental evidence

B2 remains the **metric-based development candidate**, qualified by unresolved physical integrity and unproven PRE/POST embedding equality. No production adoption is implied.

| Development metric | B0 | B2 |
|---|---:|---:|
| 5326 ANY@5 | 95.6 | 97.8 |
| 5326 ALL@5 | 88.9 | 97.8 |
| 4458 ANY@5 | 80.0 | 86.7 |
| 4458 ALL@5 | 76.7 | 86.7 |
| Combined ANY@5 | 89.3 | 93.3 |
| Combined ALL@5 | 84.0 | 93.3 |
| 4458 multi_part ALL@5 | 50.0 | 66.7 |
| Combined Legislation Hit@1 | 96.0 | 97.3 |
| Combined non-expected-legislation share@5 | 6.93% | 8.27% |

B2 improves exact-source retrieval substantially but slightly increases other-law presence deeper in Top-5. B3 has no aggregate advantage over B2; prefer B2 for simplicity. B4 was intentionally skipped before measurement and remains skipped. No post-result strategy was introduced.

Authoritative experiment JSON and CSV are byte-identical to the entry hashes recorded in the forensic JSON; all cached rankings, B0/B1/B2/B3 results, metrics and token/call counts are therefore unchanged. Only explanatory integrity prose was added to the experiment Markdown; the original metrics and historical snapshots remain intact.

## Validation and git status

`RUN_OPENAI_INTEGRATION_TESTS=0 python -m pytest -q`: **398 passed, 2 skipped in 21.17s**. Existing autouse guards block OpenAI constructors, network sockets/DNS and the configured production Chroma path; Chroma test mutations use temporary stores. No retrieval benchmark, network/OpenAI request, holdout creation/inspection or commit occurred.

Git status is recorded below after the report updates. Pre-existing config/experiment work is preserved.

```text
 M src/config.py
?? docs/m10e-experiment-protocol.md
?? reports/evaluation/m10e-retrieval-experiments.csv
?? reports/evaluation/m10e-retrieval-experiments.json
?? reports/evaluation/m10e-retrieval-experiments.md
?? reports/evaluation/m10e-storage-forensics.json
?? reports/evaluation/m10e-storage-forensics.md
?? scripts/m10e_storage_forensics.py
?? src/evaluate_retrieval_experiments.py
?? tests/test_evaluate_retrieval_experiments.py
```

`git diff --check` passed. No commit was made.

Future experiments must follow the [storage-copy policy](../../docs/m10e-experiment-protocol.md#experimental-storage-policy-for-future-work). Production Chroma was not reopened during the documentation closing step.

## Closing-step verification

With `RUN_OPENAI_INTEGRATION_TESTS=0`, `python -m pytest -q` completed with **398 passed, 2 skipped in 17.53s**. `git diff --check` passed using the repository line-ending configuration. The three updated Markdown documents also passed explicit trailing-whitespace and classification-consistency checks.

The commit boundary is exactly the 10 files in the git-status block above. All nine protected production behavior files have no diff against HEAD. Frozen datasets and M10D results have no diff; all seven frozen input/report SHA-256 values match the original experiment snapshot. Authoritative experiment JSON/CSV remain byte-identical to the accepted hashes. Only the three Markdown documents were edited during closure. No production Chroma open, retrieval run, OpenAI/network request, holdout creation, staging or commit occurred.
