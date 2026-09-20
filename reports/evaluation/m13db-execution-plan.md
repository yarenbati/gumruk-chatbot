# M13D-B — Four-source retrieval baseline: execution plan

Status: PREPARED OFFLINE — AWAITING USER APPROVAL FOR API EXECUTION.

Baseline: `fb4ee67f272fc2cda7c3063c8912d065d59ed034`.
The initial worktree was clean and HEAD equalled origin/main before runner files
were created. Execution rechecks this baseline and rejects unrelated changes.

Dataset: `evaluation/questions_gumruk_yonetmeligi.json`.
SHA256: `63d296bcf1a02f7494f6469fc3aff479f96ab7c8ce2725843e95e470c6577a08`.
Dataset bytes and expert_validated=false annotations are unchanged.

## Scope and accounting

- 30 regulation queries against the shared four-document production corpus.
- 14 article-only, 10 annex-only, 6 mixed questions.
- This run does not rerun the historical 5326/4458/5607 question sets.
- Collection: `gumruk_mevzuati`, 1266 vectors: 5326=53, 4458=276,
  5607=46, gumruk_yonetmeligi=891.
- Current `src.config`: text-embedding-3-small, TOP_K=5.
- Planned: 30 OpenAI query-embedding requests, one raw question per request;
  30 local dense collection queries; zero generation requests or corpus embeddings.
- SDK retries disabled for explicit accounting; errors stop the run. Persistent
  local attempt markers prevent automatic repeat requests after ambiguous errors.
- Actual API/network calls so far: zero. Only fake clients were used in tests.

## Unchanged retrieval and storage protection

Runner: `scripts/run_m13db_four_source.py`.
Calls the existing `src.retrieve.retrieve` function, which uses the existing
`embed.embed_texts` and `retrieve_by_embedding` path. Questions are not rewritten,
filtered, enriched or routed. No threshold, weight, model or TOP_K is changed.

Preflight reads production SQLite with `mode=ro&immutable=1`, refuses a WAL,
checks all 1266 metadata identities and expected source membership, and records
hashes of every production storage file. No production Chroma client is opened.

After approval, the runner will make and byte-verify an isolated temporary copy
of the entire existing production directory. Chroma opens only this copy;
its startup may maintain copy-local runtime files. No corpus add, update,
upsert, delete, reset, re-embedding or index-configuration operation is performed.
Production file hashes are checked again after execution, including on errors.

Article identities use DocumentSourceKey; annex identities use AnnexSourceKey
from document_id/annex_no/annex_subpart metadata and require equality with the
stored annex_source_key. Malformed provenance fails, with no chunk_id inference.

## Metric definitions

- Hit@1/3/5: any expected canonical source appears within those original chunk slots.
- MRR@5: macro mean of reciprocal rank of the first expected source; zero if
  none occurs in five. This is truncated MRR, not an unbounded corpus rank.
- Source recall@5: distinct expected sources found / distinct expected sources.
- Full expected-source coverage@5: all expected sources found; macro mean by group.
- Duplicate chunks of one provision retain their original slots and do not
  inflate recall or move another source to an earlier rank.
- Wrong-document results: total wrong-document slots, slot fraction, and number
  of affected questions. Another source in the regulation is a source miss,
  not a wrong-document result.
- Mixed: both-expected-sources flag/count, plus separate earliest rank (or null
  when absent from top-five) for each of the two expected sources.

All metrics are reported overall and separately for article/annex/mixed.
No gold keys are altered based on results.

## Outputs after approval only

- `reports/evaluation/m13db-four-source-retrieval.json`: plan, summary and all
  per-question IDs, types, exact questions, expected keys, original ranked keys,
  distances, expected-source ranks, requested metrics, usage and latency.
- `reports/evaluation/m13db-four-source-retrieval.csv`: corresponding question rows.
- Ignored `data/processed/m13db-retrieval/`: attempt and completed checkpoints.

Offline preparation: `python -B scripts/run_m13db_four_source.py`.
Real execution requires user approval followed by both `--execute` and
`RUN_OPENAI_INTEGRATION_TESTS=1`. It has NOT been run.

No commit is made in this phase.

## Offline validation

- Full suite with `RUN_OPENAI_INTEGRATION_TESTS=0`: 874 passed, 2 skipped.
- `python -m compileall -q src scripts tests`: PASS.
- `git diff --check`: PASS.
- Repeated preflight: dataset, 1266-record count and all production file hashes unchanged.
- Focused tests cover mixed partial/full coverage, duplicate slots, missing ranks,
  wrong-document counts, metadata-only annex identity, malformed provenance,
  API approval gates, exact unchanged query/model/TOP_K forwarding through the
  production retrieval implementation with fake external clients, and retry refusal.
