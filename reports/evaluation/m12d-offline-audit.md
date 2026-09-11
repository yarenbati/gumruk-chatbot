# M12D three-source offline audit

Status: completed

NO retrieval optimization was performed

Project human approval: Phase A APPROVED in task instruction. Legal expert validation is not asserted.
Frozen 5607 bytes are unchanged from the approved candidate; evaluator-only field projection occurs in memory.
Historical 5326/4458 use only existing loaders and the explicit reviewed legacy adapter; 5607 uses document-source-v1 directly. CURRENT_LEGACY_REGISTRY is unchanged.

## Frozen 5607

```json
{
  "size_bytes": 29724,
  "sha256": "30de79d0c7564bf67e7ef01c88e27077d530b50f4a47d3ce9f6df6d1d7b117a2",
  "question_count": 30,
  "source_identity_schema": "document-source-v1",
  "candidate_semantically_equal": true
}
```

## Dataset composition

```json
{
  "questions": 30,
  "distinct_keys": 24,
  "normal_keys": 21,
  "gecici_keys": 3,
  "suffixed_keys": 1,
  "multi_source_questions": 6,
  "gecici_questions": 3,
  "sections": [
    "Beşinci Bölüm",
    "Birinci Bölüm",
    "Dördüncü Bölüm",
    "Üçüncü Bölüm",
    "İkinci Bölüm"
  ],
  "duplicate_exact_questions": 0,
  "duplicate_expected_source_sets": 3,
  "replacement_characters": 0,
  "mojibake": 0,
  "question_mark_inside_words": 0,
  "malformed_source_keys": 0,
  "source_verified_false": 0
}
```

## Pre-run accounting

```json
{
  "5326": 45,
  "4458": 30,
  "5607": 30,
  "total": 105,
  "expected_query_embedding_calls": 105,
  "embedding_model": "text-embedding-3-small",
  "expected_dimensions": 1536,
  "TOP_K": 5,
  "copy_logical_count": 375
}
```

## Retrieval configuration

```json
{
  "model": "text-embedding-3-small",
  "dimensions": 1536,
  "top_k": 5,
  "distance_metric": "l2",
  "filter": null,
  "rerank": false,
  "query_expansion": false,
  "max_retries": 0,
  "bm25": false,
  "rrf": false,
  "experiments": [],
  "source_key_deduplication": false
}
```

## API accounting

```json
{
  "query_embedding_calls": 105,
  "successful_query_count": 105,
  "failed_query_count": 0,
  "generation_calls": 0,
  "prompt_tokens": 5205,
  "total_tokens": 5205
}
```

## Chroma copy-first verification

Production: `C:\gumruk-chatbot\chroma`. Temporary copy: `C:\Users\yaren\AppData\Local\Temp\m12d-chroma-copy-jhnlpxzb\chroma`.
All relative file names, sizes, and SHA-256 values were equal before opening the copy. Full manifests are in the JSON artifact.
Logical state before: `{"count": 375, "distribution": {"5326_kabahatler_kanunu": 53, "4458_gumruk_kanunu": 276, "5607_kacakcilikla_mucadele_kanunu": 46}, "dimensions": [1536], "sha256": "dae0145f680f0c724c0b446e7f8a63b92c59c2175bdbd95fe743f66c7ce72820"}`.
Post-run production bytes unchanged: True; copy logical state unchanged: True.

## 5326 metrics

Questions: 45; single-source: 39; multi-source: 6. All expected-document sets are single-document.

| Metric | @1 | @3 | @5 |
|---|---:|---:|---:|
| source_any | 75.56% | 86.67% | 95.56% |
| source_all | 64.44% | 82.22% | 88.89% |
| document_hit | 97.78% | 100.00% | 100.00% |
| document_all | 97.78% | 100.00% | 100.00% |
| document_intrusion | 2.22% | 5.93% | 8.44% |

Single-source and multi-source metrics are separately available in the JSON dataset summaries.

## 4458 metrics

Questions: 30; single-source: 24; multi-source: 6. All expected-document sets are single-document.

| Metric | @1 | @3 | @5 |
|---|---:|---:|---:|
| source_any | 53.33% | 70.00% | 76.67% |
| source_all | 43.33% | 63.33% | 73.33% |
| document_hit | 93.33% | 93.33% | 93.33% |
| document_all | 93.33% | 93.33% | 93.33% |
| document_intrusion | 6.67% | 6.67% | 6.67% |

Single-source and multi-source metrics are separately available in the JSON dataset summaries.

## 5607 metrics

Questions: 30; single-source: 24; multi-source: 6. All expected-document sets are single-document.

| Metric | @1 | @3 | @5 |
|---|---:|---:|---:|
| source_any | 60.00% | 76.67% | 80.00% |
| source_all | 50.00% | 76.67% | 76.67% |
| document_hit | 76.67% | 80.00% | 80.00% |
| document_all | 76.67% | 80.00% | 80.00% |
| document_intrusion | 23.33% | 38.89% | 42.00% |

Single-source and multi-source metrics are separately available in the JSON dataset summaries.

## combined metrics

Questions: 105; single-source: 87; multi-source: 18. All expected-document sets are single-document.

| Metric | @1 | @3 | @5 |
|---|---:|---:|---:|
| source_any | 64.76% | 79.05% | 85.71% |
| source_all | 54.29% | 75.24% | 80.95% |
| document_hit | 90.48% | 92.38% | 92.38% |
| document_all | 90.48% | 92.38% | 92.38% |
| document_intrusion | 9.52% | 15.56% | 17.52% |

Single-source and multi-source metrics are separately available in the JSON dataset summaries.

## Wrong-document Top1

q028, gk020, gk028, k5607-002, k5607-003, k5607-004, k5607-009, k5607-014, k5607-025, k5607-026

```json
{
  "5326": {
    "5326_kabahatler_kanunu": 44,
    "4458_gumruk_kanunu": 1,
    "5607_kacakcilikla_mucadele_kanunu": 0
  },
  "4458": {
    "5326_kabahatler_kanunu": 2,
    "4458_gumruk_kanunu": 28,
    "5607_kacakcilikla_mucadele_kanunu": 0
  },
  "5607": {
    "5326_kabahatler_kanunu": 0,
    "4458_gumruk_kanunu": 7,
    "5607_kacakcilikla_mucadele_kanunu": 23
  }
}
```

## Top-5 source failures (overlap retained)

A: no expected source. B: some but not all required sources. C: source coverage fails while the expected document is present. D: any wrong-document Top-5 slot, even if all sources are covered. C overlaps A/B; D may overlap any category. Intrusion is diagnostic, not a legal-error judgment.

- A_complete_top5_miss: q002, q042, gk001, gk004, gk012, gk014, gk019, gk020, gk028, k5607-002, k5607-003, k5607-004, k5607-014, k5607-025, k5607-026
- B_partial_multi_source_miss: q032, q033, q035, gk022, k5607-029
- C_correct_document_wrong_articles: q002, q032, q033, q035, q042, gk001, gk004, gk012, gk014, gk019, gk022, k5607-029
- D_wrong_document_intrusion: q021, q023, q026, q028, q030, q031, q034, q036, q037, q039, q041, q044, gk020, gk028, k5607-001, k5607-002, k5607-003, k5607-004, k5607-005, k5607-008, k5607-009, k5607-010, k5607-013, k5607-014, k5607-018, k5607-021, k5607-022, k5607-025, k5607-026, k5607-028, k5607-029, k5607-030

## 5607: Madde 16/A, Geçici, multi-source, Madde 3/23

Cutoffs retain repeated source slots. Source coverage naturally uses sets; the ranking is never deduplicated.

| ID | Expected sources | ANY @1/3/5 | ALL @1/3/5 | Missing @5 | Madde 3 slots | Madde 23 slots |
|---|---|---|---|---|---|---|
| k5607-003 | normal/3 | 0/0/0 | 0/0/0 | 5607_kacakcilikla_mucadele_kanunu/normal/3 | [] | [] |
| k5607-004 | normal/3 | 0/0/0 | 0/0/0 | 5607_kacakcilikla_mucadele_kanunu/normal/3 | [] | [] |
| k5607-005 | normal/3 | 1/1/1 | 1/1/1 | None | [1, 2] | [] |
| k5607-006 | normal/3 | 1/1/1 | 1/1/1 | None | [1] | [] |
| k5607-012 | normal/10, normal/13 | 1/1/1 | 0/1/1 | None | [] | [] |
| k5607-017 | normal/16/a | 1/1/1 | 1/1/1 | None | [] | [] |
| k5607-023 | normal/23 | 1/1/1 | 1/1/1 | None | [] | [1] |
| k5607-025 | normal/3, normal/4 | 0/0/0 | 0/0/0 | 5607_kacakcilikla_mucadele_kanunu/normal/3, 5607_kacakcilikla_mucadele_kanunu/normal/4 | [] | [] |
| k5607-026 | normal/3, normal/5 | 0/0/0 | 0/0/0 | 5607_kacakcilikla_mucadele_kanunu/normal/3, 5607_kacakcilikla_mucadele_kanunu/normal/5 | [] | [] |
| k5607-027 | normal/11, normal/16 | 1/1/1 | 0/1/1 | None | [] | [] |
| k5607-028 | gecici/7 | 1/1/1 | 1/1/1 | None | [] | [] |
| k5607-029 | gecici/10, normal/3 | 0/0/1 | 0/0/0 | 5607_kacakcilikla_mucadele_kanunu/normal/3 | [] | [] |
| k5607-030 | gecici/12, normal/5 | 1/1/1 | 0/1/1 | None | [5] | [] |

### Multi-chunk slot duplication across all 105 questions

Madde 3: `{"q041": [4, 5], "k5607-005": [1, 2]}`

Madde 23: `{}`

## Offline verification

```json
{
  "saved_rank_slots": 525,
  "saved_question_metrics_recomputed": true,
  "production_bytes_rechecked": true,
  "frozen_and_historical_hashes_rechecked": true,
  "pytest": "744 passed, 2 skipped in 15.40s",
  "RUN_OPENAI_INTEGRATION_TESTS": "0",
  "git_diff_check": "passed",
  "committed": false,
  "files_changed_this_phase": [
    "evaluation/questions_5607.json",
    "reports/evaluation/m12d-5607-question-review.csv",
    "reports/evaluation/m12d-three-source-retrieval.json",
    "reports/evaluation/m12d-three-source-retrieval.csv",
    "reports/evaluation/m12d-offline-audit.md",
    "scripts/run_m12d_three_source.py",
    "tests/test_m12d_runner.py"
  ],
  "preexisting_untracked_unchanged": [
    "evaluation/questions_5607.candidate.json",
    "scripts/build_m12d_5607_candidate.py"
  ]
}
```
