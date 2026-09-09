# M10D offline audit — 2026-09-08

The real 75-question retrieval benchmark was **not run**. No commit was made.

## Dataset freeze

- Candidate and final files were untracked at audit entry, so their empty `git diff` output was supplemented with a full JSON comparison.
- Candidate wording matches the pre-approval question-review CSV for all 30 questions.
- Final differs only in the `question` fields of **gk007, gk019, gk022**. All other fields, including every `expected_sources` value, are identical.
- Final has 30 questions, ordered gk001–gk030; every `expert_validated` is false and every `source_verified` is true. The strict dataset loader passes.
- Neither dataset nor the review CSV was edited during this audit.
- Final SHA-256: `bf81bb00f665435ace8ab28bbce274ba473074825501fcde0af34c98c45bb595`.

## Evaluator responsibilities

| Responsibility | Assessment |
|---|---|
| Qualified identity validation | Necessary: uses law, article type, and `evaluate.normalize_article_no(article_no)`. Law/type collisions remain distinct. Missing or invalid metadata now raises a data-contract error. |
| Frozen 5326 adapter | Necessary: wraps the existing M9B loader's article targets with explicit 5326/normal identity without editing legacy files. |
| Final 4458 validation | Necessary: validates schema, IDs, flags, duplicate questions/sources, and source coverage. The separate corpus-existence check reuses the existing parser and remains conditional on the local ignored paragraphs artifact being available. |
| Production retrieval orchestration | Necessary and already reused correctly: one `src.retrieve.retrieve` call site, once per question, original query unchanged, configured embedding model and `config.TOP_K`. Depth below five now fails before retrieval. |
| Pure metric helpers | Necessary: ANY uses intersection, ALL uses unique expected-source subset matching, law hit is independent, intrusion uses only retrieved Top-5, and confusion uses actual Top-1 metadata. |
| Aggregation and diagnostics | Necessary for subset, category, difficulty, failure-case, and Top-1 confusion outputs. These operate on stored results and do not retrieve again. |
| Historical PRE extraction | Necessary: ranked question results come only from `reports/evaluation/m9b-provisional.json`. Persisted chunk metadata resolves rank identity; no prose parsing, old-collection reconstruction, or inference from aggregate scores. |
| PRE/POST comparison | Necessary: computes ANY and ALL at 1/3/5 and changed-question lists. It now rejects mismatched/duplicate POST IDs rather than silently comparing an intersection. |
| JSON/CSV serialization and gated CLI | Necessary for reproducible outputs, dataset hashes, usage reporting, and explicit real-run opt-in. Collection counts are now checked by law as well as total before and after a future run. |

No competing retriever or duplicated embedding pipeline was found. No size-driven split or aesthetic refactor was necessary. The small changes address correctness and contract enforcement:

1. Reject missing, blank, or invalid qualified-source components rather than scoring them as ordinary misses.
2. Use `config.TOP_K` and reject insufficient evaluation depth.
3. Open an existing collection with `client.get_collection`; the previously used `index.get_collection` delegates to `get_or_create_collection` and could create one.
4. Reject unresolved historical chunk metadata and duplicate historical question IDs; reject partial PRE/POST joins.
5. Enforce the documented before/after per-law collection counts (5326: 53; 4458: 276) and unchanged total.
6. Add missing public helper docstrings and remove an unused import.

The suspicious-string search found only explanatory mutation names in the module docstring and two ordinary Python `set.add` calls for dataset duplicate detection. There are no collection add/upsert/delete/reset/create/rebuild calls, generation/RAG calls, query filters, query rewriting, reranking, or evaluator retry loops. Existing production retrieval internals were not altered. Importing the evaluator does not construct an API/Chroma client or run retrieval; the offline reload test also verifies this boundary.

## Offline verification

`python -m pytest -q`: **384 passed, 2 skipped in 16.88s**.

Real integration opt-in was disabled and Chroma telemetry disabled for the run. Normal-test guards block OpenAI constructors, socket connection/DNS calls, and opening the configured production Chroma path. Existing Chroma tests use temporary storage.

New tests cover normalized identity; cross-law and cross-type inequality; ANY and ALL including partial multi-source success; independent law hit at 1/3/5; Top-5-only count/share (including short/empty retrieval); Top-1 confusion; missing metadata failure; exactly one mocked retrieval call and no retry on failure; the frozen 5326 adapter; PRE extraction for all 45 actual historical rows; historical type collisions; dataset freeze; import safety; retrieval call-site restrictions; collection inventory; and insufficient depth.

The small historical test fixture contains only identity metadata copied from persisted 5326 chunks. It contains no legislation text and supplies no new retrieval results. Historical ranked results remain sourced from the frozen M9B artifact. The test independently compares qualified PRE outcomes with legacy normalized article matching at all six metrics for all 45 rows, proving equivalence for this frozen artifact.

## Immutability and stop point

- `git diff` is empty for `src/chunk.py`, `src/embed.py`, `src/index.py`, `src/retrieve.py`, `src/generate.py`, `src/rag.py`, `app.py`, and `src/ui.py`.
- Tracked frozen M9A/M9B datasets and evaluation artifacts have no diff.
- Before/after SHA-256 fingerprints of 16 dataset/report/storage files were identical, including all five files in the configured production `chroma` directory. The final dataset hash was recomputed after tests and is unchanged.
- No OpenAI call, network call, or production Chroma write occurred during this audit. Temporary test Chroma writes are isolated from production.
- Work stops here, before real retrieval benchmarking and without committing.
