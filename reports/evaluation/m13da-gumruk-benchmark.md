# M13D-A — Gümrük Yönetmeliği retrieval benchmark

Status: READY FOR REVIEW — BENCHMARK DATASET PREPARED.

Baseline: `a31459fb03f90974b40ab645133ce9f3768bb19f`.
Initial worktree was clean; HEAD equalled origin/main.

## Frozen dataset

- File: `evaluation/questions_gumruk_yonetmeligi.json`.
- Current evidence-remediated UTF-8 / LF-normalized SHA256: `63d296bcf1a02f7494f6469fc3aff479f96ab7c8ce2725843e95e470c6577a08`.
- 30 questions, IDs `gy-001` through `gy-030`.
- 14 article-only, 10 annex-only, 6 article + annex questions.
- 6 multi-source questions; 36 expected-source occurrences, 32 distinct keys.
- 20 distinct article keys and 12 distinct annex keys.
- Difficulty: 10 easy, 14 medium, 6 hard.
- Includes definitions, exceptions, ambiguous near-neighbor concepts/forms,
  a source-version repeal marker, and six explicit article-to-annex links.
- Frozen for review, not expert-approved. Review CSV fields remain pending.

The M10/M12 conventions are retained: versioned JSON questions with stable IDs,
structured expected sources, category/difficulty, source verification, evidence
notes, and a separate pending human-review CSV under `reports/evaluation/`.
The new `document-annex-source-v1` schema explicitly extends the article-only
format for this dataset. Article objects use `DocumentSourceKey`; annex objects
use `AnnexSourceKey` with `source_type=annex`, numeric `annex_no`, and nullable
`annex_subpart`. `expected_source_keys` contains their canonical serializations.
Every question has `document_id=gumruk_yonetmeligi`; 4458 is never its identity.
Existing article-only evaluation loaders are not changed and must not be used
to silently reinterpret annex keys. Any future retrieval runner needs explicit
support for this mixed source schema; no retrieval run is part of M13D-A.

## Source and identity validation

`python -B scripts/audit_gumruk_benchmark.py` reads production SQLite using
`mode=ro&immutable=1`, refuses a WAL, and creates no Chroma or API client.
It checks all 530 article chunks and all 361 annex chunks, representing
528 article keys and 98 annex keys. Indexed annex key strings must exactly
match keys reconstructed from indexed metadata. No 4458 identity fallback is
allowed. The entire collection remains 1266 records.

All 891 regulation chunk texts match reconstruction from the admitted DOCX
and ZIP plus the existing normalization manifest. Every expected key exists
in the indexed corpus, and every per-source evidence excerpt occurs literally
in its indexed text. Raw source hashes and read-only database checksum are
recorded in `m13da-gumruk-benchmark-audit.json`.

Question selection was based on inspected source text, not retrieval scores.
The dataset contains no generated legal answers. Statements and historical
dates are scoped to the admitted source snapshot, not an assertion about
current law. Main-document table extraction and provision boundaries were
not changed; selected article questions use text under their own indexed
article heading, not an adjacent provision absorbed into a chunk.

## Artifacts and scope

- `evaluation/questions_gumruk_yonetmeligi.json`: frozen questions and evidence.
- `reports/evaluation/m13da-gumruk-question-review.csv`: pending human review.
- `reports/evaluation/m13da-gumruk-benchmark-audit.json`: machine-readable audit.
- `scripts/audit_gumruk_benchmark.py`: reproducible source/key validation.
- `tests/test_gumruk_benchmark.py`: preserved-question contract, missing-source, unsupported-evidence,
  annex-mismatch, wrong-document-identity, and namespace checks.

No OpenAI calls, embedding computation, production Chroma writes, retrieval
changes, generation changes, app changes, or commits were made.

## Validation

- `RUN_OPENAI_INTEGRATION_TESTS=0 python -m pytest -q`: 870 passed, 2 skipped.
- `python -m compileall -q src scripts tests`: PASS.
- `git diff --check`: PASS.
- Source/key audit and Turkish-text encoding check: PASS.
- Production SQLite checksum unchanged after the test suite.

## Evidence-only remediation

All 30 evidence mappings (`gy-001` through `gy-030`) were expanded using
contiguous, verbatim indexed-source passages, including all 14 specifically
requested review items. Mixed questions retain separate evidence per canonical
source key. No question, ID, classification, expected source, or other dataset
field changed. No source text disproved the existing gold sources.

The prior dataset status label is retained; this remediation performs no new
freeze or approval. The test preserves the original non-evidence fields by
their pre-remediation digest instead of pinning editable evidence to a new
freeze hash. The current checksum above identifies the review revision only.
