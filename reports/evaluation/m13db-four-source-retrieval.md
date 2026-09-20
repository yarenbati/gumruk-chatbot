# M13D-B — Four-source retrieval baseline

Status: CLOSED — BASELINE FROZEN. No generation, no corpus embeddings, no
retrieval tuning. Retrieval and gold are unchanged from the accepted plan
in `m13db-execution-plan.md`.

Baseline: `fb4ee67f272fc2cda7c3063c8912d065d59ed034`.
Dataset: `evaluation/questions_gumruk_yonetmeligi.json`,
SHA256 `63d296bcf1a02f7494f6469fc3aff479f96ab7c8ce2725843e95e470c6577a08`, unchanged.
Production collection `gumruk_mevzuati`: 1266 vectors, unchanged
(5326=53, 4458=276, 5607=46, gumruk_yonetmeligi=891); all six production
storage file hashes recorded in `m13db-preflight.json` are unchanged.

30 questions, 1392 query-embedding tokens, 30 dense queries against the
existing `src.retrieve.retrieve` path, `text-embedding-3-small`, TOP_K=5.
Zero generation requests. Zero corpus embeddings.

## Results

Overall (30 questions):

| Metric | Value |
| --- | --- |
| Hit@1 | 0.6667 |
| Hit@3 | 0.8667 |
| Hit@5 | 0.9333 |
| MRR@5 | 0.7667 |
| recall@5 | 0.9000 |
| full_coverage@5 | 0.8667 |
| wrong-document slots | 17 / 150 |

Article (14 questions): Hit@5/full coverage 12/14. Misses: `gy-002`, `gy-011`.

Annex (10 questions): Hit@5/full coverage 10/10.

Mixed (6 questions): at least one expected source found in 6/6; both expected
sources found in 4/6. Partial: `gy-026`, `gy-027`.

## Failure notes

- `gy-002`: expected `gumruk_yonetmeligi/normal/3` absent from top-5.
- `gy-011`: expected `gumruk_yonetmeligi/normal/44` absent from top-5.
- `gy-026`: `gumruk_yonetmeligi/normal/330` rank 1; `gumruk_yonetmeligi/annex/62`
  absent from top-5; `4458_gumruk_kanunu/normal/94` occupies rank 2.
- `gy-027`: `gumruk_yonetmeligi/annex/63` rank 1; `gumruk_yonetmeligi/normal/334`
  absent from top-5; `4458_gumruk_kanunu/normal/161` occupies rank 2.

Both article misses (`gy-002`, `gy-011`) are same-document ranking failures:
the expected provision is outranked by other `gumruk_yonetmeligi` chunks, not
by a chunk from another source document.

Both mixed misses (`gy-026`, `gy-027`) are incomplete two-source coverage,
not zero-coverage failures: one of the two expected sources ranks first in
each case, and the second expected source is absent from the top five.

The annex benchmark achieved 10/10 top-5 coverage; all annex misses that
affect Hit@1/Hit@3 (`gy-015`, `gy-019`, `gy-020`) still land within the top 5.

In both partial mixed questions, a `4458_gumruk_kanunu` chunk ranks ahead of
the missing second expected source (rank 2 in both `gy-026` and `gy-027`).
This is cross-document semantic competition: the query embedding is closer
to a related provision in the customs-law document than to the second
expected `gumruk_yonetmeligi` source, at the shared distance scale used
across the four-document collection.

No optimization is performed in this milestone. Gold sources, retrieval
parameters, and the retrieval implementation were not touched.

## Artifacts

- `reports/evaluation/m13db-execution-plan.md`: accepted plan and scope.
- `reports/evaluation/m13db-preflight.json`: preflight fingerprints and plan.
- `reports/evaluation/m13db-four-source-retrieval.json`: plan, summary and
  all 30 per-question results.
- `reports/evaluation/m13db-four-source-retrieval.csv`: corresponding rows.
- `scripts/run_m13db_four_source.py`: runner (preflight + gated execution).
- `tests/test_m13db_four_source.py`: offline contract tests.

## Verification

- Production collection: 1266 vectors, unchanged distribution.
- Production storage file hashes: unchanged (6/6 match preflight record).
- Frozen dataset SHA256: unchanged.
- All 30 report rows present in JSON and CSV; 1392 total embedding tokens.
- `RUN_OPENAI_INTEGRATION_TESTS=0 python -m pytest -q`: 874 passed, 2 skipped.
- `python -m compileall -q src scripts tests`: PASS.
- `git diff --check`: PASS.
- Worktree contains only M13D-B files; no `data/processed` state included.
