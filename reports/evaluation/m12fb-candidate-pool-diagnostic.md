# M12F-B — Candidate Pool Completeness Diagnostic

M12F-B READY FOR REVIEW

Diagnostic only: no candidate, reranking, deduplication, hybrid retrieval, enrichment, filter, routing, chunking change or corpus re-embedding. No production adoption. All cutoffs are prefixes of ONE native L2 Top50 query per question.
Exact M12D loader and reviewed legacy adapter reused: 45 historical 5326, 30 historical 4458, 30 document-source-v1 5607; 105/105 full question records identical. Embeddings use raw original question bytes, text-embedding-3-small, 1536 dimensions, max_retries=0.

## Run accounting and immutability

```json
{
  "unique_embedding_inputs": 105,
  "requests": 1,
  "successful_embeddings": 105,
  "failures": 0,
  "prompt_tokens": 5205,
  "total_tokens": 5205,
  "generation_calls": 0
}
```
Chroma query operations: 105; saved ranked slots: 5250.
Byte-verified copy logical state: {'count': 375, 'distribution': {'5326_kabahatler_kanunu': 53, '4458_gumruk_kanunu': 276, '5607_kacakcilikla_mucadele_kanunu': 46}, 'dimensions': [1536], 'sha256': 'dae0145f680f0c724c0b446e7f8a63b92c59c2175bdbd95fe743f66c7ce72820'}. Production unchanged: True; copied logical state unchanged: True; frozen datasets, production code and M12D/M12E/M12F-A artifact hashes unchanged: True.
Full file manifests and logical fingerprints are saved in JSON; only the temporary copy was opened.

## Fresh Top5 versus accepted M12D

Distance tolerance: absolute 1e-07, relative 0. Slotwise distances and common-chunk distances are reported separately; missing common chunks are not assigned zero difference.
Fresh-versus-old drift is NOT candidate improvement. The fresh Top50 prefix can differ from historical K=5 retrieval due to query-vector changes or ANN behavior; this run cannot isolate those causes.

| Comparison | Mismatch count | IDs |
|---|---:|---|
| top5_chunk_ids_equal | 8 | q042, gk001, gk008, gk010, gk020, gk029, k5607-014, k5607-021 |
| metrics_equal | 2 | gk001, k5607-014 |
| slot_distances_equal | 102 | q001, q002, q003, q004, q005, q006, q007, q008, q009, q010, q011, q012, q013, q014, q015, q016, q017, q018, q020, q021, q022, q023, q024, q025, q026, q027, q028, q029, q030, q031, q032, q033, q034, q035, q036, q037, q038, q039, q040, q041, q042, q043, q044, q045, gk001, gk002, gk003, gk004, gk005, gk006, gk007, gk008, gk009, gk010, gk011, gk012, gk013, gk014, gk015, gk016, gk017, gk018, gk019, gk020, gk021, gk022, gk023, gk024, gk025, gk026, gk027, gk028, gk029, gk030, k5607-001, k5607-002, k5607-003, k5607-004, k5607-005, k5607-006, k5607-007, k5607-008, k5607-009, k5607-010, k5607-011, k5607-012, k5607-013, k5607-014, k5607-015, k5607-016, k5607-017, k5607-018, k5607-019, k5607-020, k5607-021, k5607-022, k5607-025, k5607-026, k5607-027, k5607-028, k5607-029, k5607-030 |
| common_chunk_distances_equal | 102 | q001, q002, q003, q004, q005, q006, q007, q008, q009, q010, q011, q012, q013, q014, q015, q016, q017, q018, q020, q021, q022, q023, q024, q025, q026, q027, q028, q029, q030, q031, q032, q033, q034, q035, q036, q037, q038, q039, q040, q041, q042, q043, q044, q045, gk001, gk002, gk003, gk004, gk005, gk006, gk007, gk008, gk009, gk010, gk011, gk012, gk013, gk014, gk015, gk016, gk017, gk018, gk019, gk020, gk021, gk022, gk023, gk024, gk025, gk026, gk027, gk028, gk029, gk030, k5607-001, k5607-002, k5607-003, k5607-004, k5607-005, k5607-006, k5607-007, k5607-008, k5607-009, k5607-010, k5607-011, k5607-012, k5607-013, k5607-014, k5607-015, k5607-016, k5607-017, k5607-018, k5607-019, k5607-020, k5607-021, k5607-022, k5607-025, k5607-026, k5607-027, k5607-028, k5607-029, k5607-030 |

## Coverage metrics

Document ALL means all expected documents appear, not that every slot is from the correct document. Intrusion is mean wrong-document slot fraction. No ranking is deduplicated. Single/multi-source groups are shown separately; empty groups are N/A.

| Dataset | Group (n) | Metric | @1 | @3 | @5 | @10 | @20 | @50 |
|---|---|---|---:|---:|---:|---:|---:|---:|
| 5326 | overall (45) | source_any | 75.56% | 86.67% | 95.56% | 95.56% | 97.78% | 97.78% |
| 5326 | overall (45) | source_all | 64.44% | 82.22% | 88.89% | 95.56% | 97.78% | 97.78% |
| 5326 | overall (45) | document_hit | 97.78% | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% |
| 5326 | overall (45) | document_all | 97.78% | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% |
| 5326 | overall (45) | document_intrusion | 2.22% | 5.93% | 8.44% | 16.67% | 22.22% | 36.04% |
| 5326 | single_source (39) | source_any | 74.36% | 87.18% | 94.87% | 94.87% | 97.44% | 97.44% |
| 5326 | single_source (39) | source_all | 74.36% | 87.18% | 94.87% | 94.87% | 97.44% | 97.44% |
| 5326 | single_source (39) | document_hit | 97.44% | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% |
| 5326 | single_source (39) | document_all | 97.44% | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% |
| 5326 | single_source (39) | document_intrusion | 2.56% | 5.98% | 7.18% | 15.90% | 21.54% | 35.44% |
| 5326 | multi_source (6) | source_any | 83.33% | 83.33% | 100.00% | 100.00% | 100.00% | 100.00% |
| 5326 | multi_source (6) | source_all | 0.00% | 50.00% | 50.00% | 100.00% | 100.00% | 100.00% |
| 5326 | multi_source (6) | document_hit | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% |
| 5326 | multi_source (6) | document_all | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% |
| 5326 | multi_source (6) | document_intrusion | 0.00% | 5.56% | 16.67% | 21.67% | 26.67% | 40.00% |
| 4458 | overall (30) | source_any | 56.67% | 73.33% | 80.00% | 86.67% | 86.67% | 96.67% |
| 4458 | overall (30) | source_all | 46.67% | 66.67% | 76.67% | 83.33% | 83.33% | 90.00% |
| 4458 | overall (30) | document_hit | 93.33% | 93.33% | 93.33% | 96.67% | 100.00% | 100.00% |
| 4458 | overall (30) | document_all | 93.33% | 93.33% | 93.33% | 96.67% | 100.00% | 100.00% |
| 4458 | overall (30) | document_intrusion | 6.67% | 6.67% | 6.67% | 6.33% | 6.50% | 7.60% |
| 4458 | single_source (24) | source_any | 58.33% | 75.00% | 83.33% | 87.50% | 87.50% | 95.83% |
| 4458 | single_source (24) | source_all | 58.33% | 75.00% | 83.33% | 87.50% | 87.50% | 95.83% |
| 4458 | single_source (24) | document_hit | 95.83% | 95.83% | 95.83% | 95.83% | 100.00% | 100.00% |
| 4458 | single_source (24) | document_all | 95.83% | 95.83% | 95.83% | 95.83% | 100.00% | 100.00% |
| 4458 | single_source (24) | document_intrusion | 4.17% | 4.17% | 4.17% | 4.58% | 4.58% | 5.33% |
| 4458 | multi_source (6) | source_any | 50.00% | 66.67% | 66.67% | 83.33% | 83.33% | 100.00% |
| 4458 | multi_source (6) | source_all | 0.00% | 33.33% | 50.00% | 66.67% | 66.67% | 66.67% |
| 4458 | multi_source (6) | document_hit | 83.33% | 83.33% | 83.33% | 100.00% | 100.00% | 100.00% |
| 4458 | multi_source (6) | document_all | 83.33% | 83.33% | 83.33% | 100.00% | 100.00% | 100.00% |
| 4458 | multi_source (6) | document_intrusion | 16.67% | 16.67% | 16.67% | 13.33% | 14.17% | 16.67% |
| 5607 | overall (30) | source_any | 63.33% | 80.00% | 83.33% | 83.33% | 83.33% | 83.33% |
| 5607 | overall (30) | source_all | 53.33% | 80.00% | 80.00% | 80.00% | 80.00% | 80.00% |
| 5607 | overall (30) | document_hit | 80.00% | 83.33% | 83.33% | 83.33% | 83.33% | 86.67% |
| 5607 | overall (30) | document_all | 80.00% | 83.33% | 83.33% | 83.33% | 83.33% | 86.67% |
| 5607 | overall (30) | document_intrusion | 20.00% | 37.78% | 41.33% | 46.00% | 52.00% | 64.27% |
| 5607 | single_source (24) | source_any | 66.67% | 87.50% | 87.50% | 87.50% | 87.50% | 87.50% |
| 5607 | single_source (24) | source_all | 66.67% | 87.50% | 87.50% | 87.50% | 87.50% | 87.50% |
| 5607 | single_source (24) | document_hit | 83.33% | 87.50% | 87.50% | 87.50% | 87.50% | 87.50% |
| 5607 | single_source (24) | document_all | 83.33% | 87.50% | 87.50% | 87.50% | 87.50% | 87.50% |
| 5607 | single_source (24) | document_intrusion | 16.67% | 34.72% | 40.00% | 42.08% | 48.12% | 61.75% |
| 5607 | multi_source (6) | source_any | 50.00% | 50.00% | 66.67% | 66.67% | 66.67% | 66.67% |
| 5607 | multi_source (6) | source_all | 0.00% | 50.00% | 50.00% | 50.00% | 50.00% | 50.00% |
| 5607 | multi_source (6) | document_hit | 66.67% | 66.67% | 66.67% | 66.67% | 66.67% | 83.33% |
| 5607 | multi_source (6) | document_all | 66.67% | 66.67% | 66.67% | 66.67% | 66.67% | 83.33% |
| 5607 | multi_source (6) | document_intrusion | 33.33% | 50.00% | 46.67% | 61.67% | 67.50% | 74.33% |
| combined | overall (105) | source_any | 66.67% | 80.95% | 87.62% | 89.52% | 90.48% | 93.33% |
| combined | overall (105) | source_all | 56.19% | 77.14% | 82.86% | 87.62% | 88.57% | 90.48% |
| combined | overall (105) | document_hit | 91.43% | 93.33% | 93.33% | 94.29% | 95.24% | 96.19% |
| combined | overall (105) | document_all | 91.43% | 93.33% | 93.33% | 94.29% | 95.24% | 96.19% |
| combined | overall (105) | document_intrusion | 8.57% | 15.24% | 17.33% | 22.10% | 26.24% | 35.98% |
| combined | single_source (87) | source_any | 67.82% | 83.91% | 89.66% | 90.80% | 91.95% | 94.25% |
| combined | single_source (87) | source_all | 67.82% | 83.91% | 89.66% | 90.80% | 91.95% | 94.25% |
| combined | single_source (87) | document_hit | 93.10% | 95.40% | 95.40% | 95.40% | 96.55% | 96.55% |
| combined | single_source (87) | document_all | 93.10% | 95.40% | 95.40% | 95.40% | 96.55% | 96.55% |
| combined | single_source (87) | document_intrusion | 6.90% | 13.41% | 15.40% | 20.00% | 24.20% | 34.39% |
| combined | multi_source (18) | source_any | 61.11% | 66.67% | 77.78% | 83.33% | 83.33% | 88.89% |
| combined | multi_source (18) | source_all | 0.00% | 44.44% | 50.00% | 72.22% | 72.22% | 72.22% |
| combined | multi_source (18) | document_hit | 83.33% | 83.33% | 83.33% | 88.89% | 88.89% | 94.44% |
| combined | multi_source (18) | document_all | 83.33% | 83.33% | 83.33% | 88.89% | 88.89% | 94.44% |
| combined | multi_source (18) | document_intrusion | 16.67% | 24.07% | 26.67% | 32.22% | 36.11% | 43.67% |

## Critical accepted 5607 failure cohorts

These are fixed accepted M12D cohorts. Fresh @5 recovery, if present, is drift and is shown separately from deeper recovery.

```json
{
  "six_complete_misses_any": {
    "total": 6,
    "by_cutoff": {
      "5": 1,
      "10": 1,
      "20": 1,
      "50": 1
    },
    "absent_or_incomplete_50": 5,
    "bands": {
      "1-5": [
        "k5607-014"
      ],
      "6-10": [],
      "11-20": [],
      "21-50": [],
      ">50": [
        "k5607-002",
        "k5607-003",
        "k5607-004",
        "k5607-025",
        "k5607-026"
      ]
    }
  },
  "seven_all_failures": {
    "total": 7,
    "by_cutoff": {
      "5": 1,
      "10": 1,
      "20": 1,
      "50": 1
    },
    "absent_or_incomplete_50": 6,
    "bands": {
      "1-5": [
        "k5607-014"
      ],
      "6-10": [],
      "11-20": [],
      "21-50": [],
      ">50": [
        "k5607-002",
        "k5607-003",
        "k5607-004",
        "k5607-025",
        "k5607-026",
        "k5607-029"
      ]
    }
  }
}
```

## Fresh failure recovery bands

ALL@5 failure bands: A=6–10, B=11–20, C=21–50, D=>50/incomplete. ANY@5 complete misses use first expected source. Null is censored beyond Top50, not absent from the corpus.

```json
{
  "source_all": {
    "total": 18,
    "by_cutoff": {
      "5": 0,
      "10": 5,
      "20": 6,
      "50": 8
    },
    "absent_or_incomplete_50": 10,
    "bands": {
      "1-5": [],
      "6-10": [
        "q032",
        "q033",
        "q035",
        "gk004",
        "gk022"
      ],
      "11-20": [
        "q042"
      ],
      "21-50": [
        "gk012",
        "gk014"
      ],
      ">50": [
        "q002",
        "gk019",
        "gk020",
        "gk028",
        "k5607-002",
        "k5607-003",
        "k5607-004",
        "k5607-025",
        "k5607-026",
        "k5607-029"
      ]
    }
  },
  "source_any": {
    "total": 13,
    "by_cutoff": {
      "5": 0,
      "10": 2,
      "20": 3,
      "50": 6
    },
    "absent_or_incomplete_50": 7,
    "bands": {
      "1-5": [],
      "6-10": [
        "gk004",
        "gk020"
      ],
      "11-20": [
        "q042"
      ],
      "21-50": [
        "gk012",
        "gk014",
        "gk019"
      ],
      ">50": [
        "q002",
        "gk028",
        "k5607-002",
        "k5607-003",
        "k5607-004",
        "k5607-025",
        "k5607-026"
      ]
    }
  },
  "multi_source_all": {
    "total": 9,
    "by_cutoff": {
      "5": 0,
      "10": 4,
      "20": 4,
      "50": 4
    },
    "absent_or_incomplete_50": 5,
    "bands": {
      "1-5": [],
      "6-10": [
        "q032",
        "q033",
        "q035",
        "gk022"
      ],
      "11-20": [],
      "21-50": [],
      ">50": [
        "gk019",
        "gk020",
        "k5607-025",
        "k5607-026",
        "k5607-029"
      ]
    }
  }
}
```

## First-correct-rank distribution

```json
{
  "first_expected_document_rank": {
    "1-5": [
      "q001",
      "q002",
      "q003",
      "q004",
      "q005",
      "q006",
      "q007",
      "q008",
      "q009",
      "q010",
      "q011",
      "q012",
      "q013",
      "q014",
      "q015",
      "q016",
      "q017",
      "q018",
      "q019",
      "q020",
      "q021",
      "q022",
      "q023",
      "q024",
      "q025",
      "q026",
      "q027",
      "q028",
      "q029",
      "q030",
      "q031",
      "q032",
      "q033",
      "q034",
      "q035",
      "q036",
      "q037",
      "q038",
      "q039",
      "q040",
      "q041",
      "q042",
      "q043",
      "q044",
      "q045",
      "gk001",
      "gk002",
      "gk003",
      "gk004",
      "gk005",
      "gk006",
      "gk007",
      "gk008",
      "gk009",
      "gk010",
      "gk011",
      "gk012",
      "gk013",
      "gk014",
      "gk015",
      "gk016",
      "gk017",
      "gk018",
      "gk019",
      "gk021",
      "gk022",
      "gk023",
      "gk024",
      "gk025",
      "gk026",
      "gk027",
      "gk029",
      "gk030",
      "k5607-001",
      "k5607-005",
      "k5607-006",
      "k5607-007",
      "k5607-008",
      "k5607-009",
      "k5607-010",
      "k5607-011",
      "k5607-012",
      "k5607-013",
      "k5607-014",
      "k5607-015",
      "k5607-016",
      "k5607-017",
      "k5607-018",
      "k5607-019",
      "k5607-020",
      "k5607-021",
      "k5607-022",
      "k5607-023",
      "k5607-024",
      "k5607-027",
      "k5607-028",
      "k5607-029",
      "k5607-030"
    ],
    "6-10": [
      "gk020"
    ],
    "11-20": [
      "gk028"
    ],
    "21-50": [
      "k5607-026"
    ],
    ">50": [
      "k5607-002",
      "k5607-003",
      "k5607-004",
      "k5607-025"
    ]
  },
  "first_expected_source_rank": {
    "1-5": [
      "q001",
      "q003",
      "q004",
      "q005",
      "q006",
      "q007",
      "q008",
      "q009",
      "q010",
      "q011",
      "q012",
      "q013",
      "q014",
      "q015",
      "q016",
      "q017",
      "q018",
      "q019",
      "q020",
      "q021",
      "q022",
      "q023",
      "q024",
      "q025",
      "q026",
      "q027",
      "q028",
      "q029",
      "q030",
      "q031",
      "q032",
      "q033",
      "q034",
      "q035",
      "q036",
      "q037",
      "q038",
      "q039",
      "q040",
      "q041",
      "q043",
      "q044",
      "q045",
      "gk001",
      "gk002",
      "gk003",
      "gk005",
      "gk006",
      "gk007",
      "gk008",
      "gk009",
      "gk010",
      "gk011",
      "gk013",
      "gk015",
      "gk016",
      "gk017",
      "gk018",
      "gk021",
      "gk022",
      "gk023",
      "gk024",
      "gk025",
      "gk026",
      "gk027",
      "gk029",
      "gk030",
      "k5607-001",
      "k5607-005",
      "k5607-006",
      "k5607-007",
      "k5607-008",
      "k5607-009",
      "k5607-010",
      "k5607-011",
      "k5607-012",
      "k5607-013",
      "k5607-014",
      "k5607-015",
      "k5607-016",
      "k5607-017",
      "k5607-018",
      "k5607-019",
      "k5607-020",
      "k5607-021",
      "k5607-022",
      "k5607-023",
      "k5607-024",
      "k5607-027",
      "k5607-028",
      "k5607-029",
      "k5607-030"
    ],
    "6-10": [
      "gk004",
      "gk020"
    ],
    "11-20": [
      "q042"
    ],
    "21-50": [
      "gk012",
      "gk014",
      "gk019"
    ],
    ">50": [
      "q002",
      "gk028",
      "k5607-002",
      "k5607-003",
      "k5607-004",
      "k5607-025",
      "k5607-026"
    ]
  },
  "all_expected_sources_recovered_by_rank": {
    "1-5": [
      "q001",
      "q003",
      "q004",
      "q005",
      "q006",
      "q007",
      "q008",
      "q009",
      "q010",
      "q011",
      "q012",
      "q013",
      "q014",
      "q015",
      "q016",
      "q017",
      "q018",
      "q019",
      "q020",
      "q021",
      "q022",
      "q023",
      "q024",
      "q025",
      "q026",
      "q027",
      "q028",
      "q029",
      "q030",
      "q031",
      "q034",
      "q036",
      "q037",
      "q038",
      "q039",
      "q040",
      "q041",
      "q043",
      "q044",
      "q045",
      "gk001",
      "gk002",
      "gk003",
      "gk005",
      "gk006",
      "gk007",
      "gk008",
      "gk009",
      "gk010",
      "gk011",
      "gk013",
      "gk015",
      "gk016",
      "gk017",
      "gk018",
      "gk021",
      "gk023",
      "gk024",
      "gk025",
      "gk026",
      "gk027",
      "gk029",
      "gk030",
      "k5607-001",
      "k5607-005",
      "k5607-006",
      "k5607-007",
      "k5607-008",
      "k5607-009",
      "k5607-010",
      "k5607-011",
      "k5607-012",
      "k5607-013",
      "k5607-014",
      "k5607-015",
      "k5607-016",
      "k5607-017",
      "k5607-018",
      "k5607-019",
      "k5607-020",
      "k5607-021",
      "k5607-022",
      "k5607-023",
      "k5607-024",
      "k5607-027",
      "k5607-028",
      "k5607-030"
    ],
    "6-10": [
      "q032",
      "q033",
      "q035",
      "gk004",
      "gk022"
    ],
    "11-20": [
      "q042"
    ],
    "21-50": [
      "gk012",
      "gk014"
    ],
    ">50": [
      "q002",
      "gk019",
      "gk020",
      "gk028",
      "k5607-002",
      "k5607-003",
      "k5607-004",
      "k5607-025",
      "k5607-026",
      "k5607-029"
    ]
  }
}
```

## Primary failures and successful controls

Statuses below are Source ANY / ALL. Per-source ranks are exact canonical DocumentSourceKeys; >50 means not found within saved Top50.

| ID | First expected document | Each required source: rank | ALL recovered rank | @5 ANY/ALL | @10 | @20 | @50 |
|---|---:|---|---:|---|---|---|---|
| gk001 | 1 | 4458_gumruk_kanunu/normal/210: 1 | 1 | 1/1 | 1/1 | 1/1 | 1/1 |
| k5607-002 | >50 | 5607_kacakcilikla_mucadele_kanunu/normal/2: >50 | >50 | 0/0 | 0/0 | 0/0 | 0/0 |
| k5607-003 | >50 | 5607_kacakcilikla_mucadele_kanunu/normal/3: >50 | >50 | 0/0 | 0/0 | 0/0 | 0/0 |
| k5607-004 | >50 | 5607_kacakcilikla_mucadele_kanunu/normal/3: >50 | >50 | 0/0 | 0/0 | 0/0 | 0/0 |
| k5607-014 | 1 | 5607_kacakcilikla_mucadele_kanunu/normal/12: 1 | 1 | 1/1 | 1/1 | 1/1 | 1/1 |
| k5607-017 | 1 | 5607_kacakcilikla_mucadele_kanunu/normal/16/a: 1 | 1 | 1/1 | 1/1 | 1/1 | 1/1 |
| k5607-023 | 1 | 5607_kacakcilikla_mucadele_kanunu/normal/23: 1 | 1 | 1/1 | 1/1 | 1/1 | 1/1 |
| k5607-025 | >50 | 5607_kacakcilikla_mucadele_kanunu/normal/3: >50; 5607_kacakcilikla_mucadele_kanunu/normal/4: >50 | >50 | 0/0 | 0/0 | 0/0 | 0/0 |
| k5607-026 | 45 | 5607_kacakcilikla_mucadele_kanunu/normal/3: >50; 5607_kacakcilikla_mucadele_kanunu/normal/5: >50 | >50 | 0/0 | 0/0 | 0/0 | 0/0 |
| k5607-028 | 1 | 5607_kacakcilikla_mucadele_kanunu/gecici/7: 1 | 1 | 1/1 | 1/1 | 1/1 | 1/1 |
| k5607-029 | 1 | 5607_kacakcilikla_mucadele_kanunu/gecici/10: 4; 5607_kacakcilikla_mucadele_kanunu/normal/3: >50 | >50 | 1/0 | 1/0 | 1/0 | 1/0 |
| k5607-030 | 1 | 5607_kacakcilikla_mucadele_kanunu/gecici/12: 1; 5607_kacakcilikla_mucadele_kanunu/normal/5: 2 | 2 | 1/1 | 1/1 | 1/1 | 1/1 |

### gk001

Gümrük uygulamasında "geri verme" ile "kaldırma" terimleri arasında ne fark vardır?
Gold complete in fresh Top5; historical failure, if any, is drift, not deeper-pool recovery
Distance gaps (within-query descriptive evidence; no global L2 correctness threshold):
```json
{
  "top1_distance": 0.7275918126106262,
  "first_gold_distance": 0.7275918126106262,
  "gold_minus_top1": 0.0,
  "cutoff_distances": {
    "5": 0.9307778477668762,
    "10": 0.9543179273605347,
    "20": 0.9933985471725464,
    "50": 1.04922354221344
  }
}
```
Repeated slots before each required source (censored rows count through Top50):
```json
{
  "4458_gumruk_kanunu/normal/210": {
    "gold_rank": 1,
    "censored": false,
    "total_slots": 0,
    "distinct_sources": 0,
    "repeated_slots": 0,
    "repeated_sources": {},
    "repeated_by_document": {}
  }
}
```

### k5607-002

5607 sayılı Kanunda “gümrüklenmiş değer” nasıl tanımlanır ve ithal ve ihraç eşyası bakımından hangi değerlerin toplamı esas alınır?
Expected document absent Top50; strong observed document-discrimination failure
Distance gaps (within-query descriptive evidence; no global L2 correctness threshold):
```json
{
  "top1_distance": 0.6854152083396912,
  "first_gold_distance": null,
  "gold_minus_top1": null,
  "cutoff_distances": {
    "5": 0.7031776905059814,
    "10": 0.7303980588912964,
    "20": 0.7503724098205566,
    "50": 0.794853687286377
  }
}
```
Repeated slots before each required source (censored rows count through Top50):
```json
{
  "5607_kacakcilikla_mucadele_kanunu/normal/2": {
    "gold_rank": null,
    "censored": true,
    "total_slots": 50,
    "distinct_sources": 49,
    "repeated_slots": 1,
    "repeated_sources": {
      "4458_gumruk_kanunu/normal/167": 1
    },
    "repeated_by_document": {
      "4458_gumruk_kanunu": 1
    }
  }
}
```

### k5607-003

Eşyanın gümrük işlemlerine tabi tutulmadan ülkeye sokulması hangi hapis ve adlî para cezasını gerektirir; eşya gümrük kapıları dışından sokulursa ceza nasıl değişir?
Expected document absent Top50; strong observed document-discrimination failure
Distance gaps (within-query descriptive evidence; no global L2 correctness threshold):
```json
{
  "top1_distance": 0.6469547152519226,
  "first_gold_distance": null,
  "gold_minus_top1": null,
  "cutoff_distances": {
    "5": 0.7066694498062134,
    "10": 0.7236261963844299,
    "20": 0.7776032090187073,
    "50": 0.8257532715797424
  }
}
```
Repeated slots before each required source (censored rows count through Top50):
```json
{
  "5607_kacakcilikla_mucadele_kanunu/normal/3": {
    "gold_rank": null,
    "censored": true,
    "total_slots": 50,
    "distinct_sources": 48,
    "repeated_slots": 2,
    "repeated_sources": {
      "4458_gumruk_kanunu/normal/235": 1,
      "4458_gumruk_kanunu/normal/241": 1
    },
    "repeated_by_document": {
      "4458_gumruk_kanunu": 2
    }
  }
}
```

### k5607-004

İhracat gerçekleşmediği hâlde gerçekleşmiş gibi gösterilmesi veya ihraç malının cins, miktar, evsaf ya da fiyatının değiştirilmesi hangi yaptırımla karşılanır; beyandaki fark yüzde onu aşmıyorsa hangi işlem uygulanır?
Expected document absent Top50; strong observed document-discrimination failure
Distance gaps (within-query descriptive evidence; no global L2 correctness threshold):
```json
{
  "top1_distance": 0.6974372267723083,
  "first_gold_distance": null,
  "gold_minus_top1": null,
  "cutoff_distances": {
    "5": 0.7180213928222656,
    "10": 0.758293628692627,
    "20": 0.7839323878288269,
    "50": 0.8612039685249329
  }
}
```
Repeated slots before each required source (censored rows count through Top50):
```json
{
  "5607_kacakcilikla_mucadele_kanunu/normal/3": {
    "gold_rank": null,
    "censored": true,
    "total_slots": 50,
    "distinct_sources": 48,
    "repeated_slots": 2,
    "repeated_sources": {
      "4458_gumruk_kanunu/normal/235": 1,
      "4458_gumruk_kanunu/normal/167": 1
    },
    "repeated_by_document": {
      "4458_gumruk_kanunu": 2
    }
  }
}
```

### k5607-014

Yabancı ülkeden gelen yasak eşya yükleme veya taşıma belgelerinde gösterilerek gümrüğe getirilmişse hangi güvenlik koşulları altında nereye gönderilebilir?
Gold complete in fresh Top5; historical failure, if any, is drift, not deeper-pool recovery
Distance gaps (within-query descriptive evidence; no global L2 correctness threshold):
```json
{
  "top1_distance": 0.6998095512390137,
  "first_gold_distance": 0.6998095512390137,
  "gold_minus_top1": 0.0,
  "cutoff_distances": {
    "5": 0.8782172203063965,
    "10": 0.9141654968261719,
    "20": 0.9414672255516052,
    "50": 0.9791988134384155
  }
}
```
Repeated slots before each required source (censored rows count through Top50):
```json
{
  "5607_kacakcilikla_mucadele_kanunu/normal/12": {
    "gold_rank": 1,
    "censored": false,
    "total_slots": 0,
    "distinct_sources": 0,
    "repeated_slots": 0,
    "repeated_sources": {},
    "repeated_by_document": {}
  }
}
```

### k5607-025

Eşyayı gümrük işlemlerine tabi tutmaksızın ülkeye sokan kişi için Madde 3 fıkra 1'deki temel yaptırım nedir; aynı suç örgüt faaliyeti çerçevesinde işlenirse ve eşya toplum sağlığını tehdit edecek nitelikteyse Madde 4 fıkra 1 ve 7 hangi ek sonuçları, hangi koşulla öngörür?
Expected document absent Top50; strong observed document-discrimination failure
Distance gaps (within-query descriptive evidence; no global L2 correctness threshold):
```json
{
  "top1_distance": 0.7140333652496338,
  "first_gold_distance": null,
  "gold_minus_top1": null,
  "cutoff_distances": {
    "5": 0.7738392949104309,
    "10": 0.8071574568748474,
    "20": 0.8299627304077148,
    "50": 0.8837611079216003
  }
}
```
Repeated slots before each required source (censored rows count through Top50):
```json
{
  "5607_kacakcilikla_mucadele_kanunu/normal/3": {
    "gold_rank": null,
    "censored": true,
    "total_slots": 50,
    "distinct_sources": 48,
    "repeated_slots": 2,
    "repeated_sources": {
      "4458_gumruk_kanunu/normal/167": 1,
      "4458_gumruk_kanunu/normal/235": 1
    },
    "repeated_by_document": {
      "4458_gumruk_kanunu": 2
    }
  },
  "5607_kacakcilikla_mucadele_kanunu/normal/4": {
    "gold_rank": null,
    "censored": true,
    "total_slots": 50,
    "distinct_sources": 48,
    "repeated_slots": 2,
    "repeated_sources": {
      "4458_gumruk_kanunu/normal/167": 1,
      "4458_gumruk_kanunu/normal/235": 1
    },
    "repeated_by_document": {
      "4458_gumruk_kanunu": 2
    }
  }
}
```

### k5607-026

Eşyayı gümrük işlemlerine tabi tutmaksızın ülkeye sokmanın Madde 3 fıkra 1'deki temel yaptırımı nedir; Madde 5 kapsamında etkin pişmanlıkla ödeme yapılırsa ödeme tutarı, soruşturma ve kovuşturma evrelerindeki indirimler ve bu imkândan yararlanamayan hâller nelerdir?
Expected document first appears below Top5; document competition observed, provision selection may also contribute
Distance gaps (within-query descriptive evidence; no global L2 correctness threshold):
```json
{
  "top1_distance": 0.6664212942123413,
  "first_gold_distance": null,
  "gold_minus_top1": null,
  "cutoff_distances": {
    "5": 0.6961438655853271,
    "10": 0.7177428007125854,
    "20": 0.7440258860588074,
    "50": 0.8130285143852234
  }
}
```
Repeated slots before each required source (censored rows count through Top50):
```json
{
  "5607_kacakcilikla_mucadele_kanunu/normal/3": {
    "gold_rank": null,
    "censored": true,
    "total_slots": 50,
    "distinct_sources": 47,
    "repeated_slots": 3,
    "repeated_sources": {
      "4458_gumruk_kanunu/normal/235": 1,
      "4458_gumruk_kanunu/normal/241": 1,
      "4458_gumruk_kanunu/normal/167": 1
    },
    "repeated_by_document": {
      "4458_gumruk_kanunu": 3
    }
  },
  "5607_kacakcilikla_mucadele_kanunu/normal/5": {
    "gold_rank": null,
    "censored": true,
    "total_slots": 50,
    "distinct_sources": 47,
    "repeated_slots": 3,
    "repeated_sources": {
      "4458_gumruk_kanunu/normal/235": 1,
      "4458_gumruk_kanunu/normal/241": 1,
      "4458_gumruk_kanunu/normal/167": 1
    },
    "repeated_by_document": {
      "4458_gumruk_kanunu": 3
    }
  }
}
```

### k5607-029

Madde 3 fıkra 2 hangi fiili ve yaptırımı düzenler; gümrük vergilerinin kısmen eksik ödenmesi nedeniyle açılmış kamu davalarında, Geçici Madde 10'un yürürlüğünden önce elkonulan ve müsadere kararı verilmemiş kara taşıtlarının iadesi için bu geçici hüküm hangi başvuru, ödeme ve tasfiye koşullarını arar?
Expected document present in Top5 but gold incomplete; within-document provision selection observed
Distance gaps (within-query descriptive evidence; no global L2 correctness threshold):
```json
{
  "top1_distance": 0.6584870219230652,
  "first_gold_distance": 0.704149603843689,
  "gold_minus_top1": 0.04566258192062378,
  "cutoff_distances": {
    "5": 0.7236523628234863,
    "10": 0.7672156691551208,
    "20": 0.808016300201416,
    "50": 0.8659300804138184
  }
}
```
Repeated slots before each required source (censored rows count through Top50):
```json
{
  "5607_kacakcilikla_mucadele_kanunu/gecici/10": {
    "gold_rank": 4,
    "censored": false,
    "total_slots": 3,
    "distinct_sources": 3,
    "repeated_slots": 0,
    "repeated_sources": {},
    "repeated_by_document": {}
  },
  "5607_kacakcilikla_mucadele_kanunu/normal/3": {
    "gold_rank": null,
    "censored": true,
    "total_slots": 50,
    "distinct_sources": 50,
    "repeated_slots": 0,
    "repeated_sources": {},
    "repeated_by_document": {}
  }
}
```

## Duplicate-source capacity

Distinct counts are summed per query, not deduplicated globally. Repeated slots = slots minus distinct canonical provisions. This measures occupied capacity, not counterfactual gold recovery.

| K | Total slots | Distinct sources summed | Repeated slots | Questions with repeats | Repeated slots by document |
|---|---:|---:|---:|---:|---|
| 5 | 525 | 519 | 6 | 6 | {'5607_kacakcilikla_mucadele_kanunu': 2, '4458_gumruk_kanunu': 4} |
| 10 | 1050 | 1041 | 9 | 9 | {'5607_kacakcilikla_mucadele_kanunu': 4, '4458_gumruk_kanunu': 5} |
| 20 | 2100 | 2066 | 34 | 26 | {'4458_gumruk_kanunu': 18, '5607_kacakcilikla_mucadele_kanunu': 16} |
| 50 | 5250 | 5122 | 128 | 61 | {'4458_gumruk_kanunu': 79, '5607_kacakcilikla_mucadele_kanunu': 49} |

## Madde 3 / Madde 23 across all 30 5607 questions

Accepted corpus has 3 chunks for 5607 Madde 3 and 2 for Madde 23. These are their observed Top50 ranks; missing chunks are censored. JSON records chunk IDs and ranks before EACH required gold source, including censored cases.

| ID | Madde 3 ranks | Madde 23 ranks | More than one before a required gold source (Article: source) |
|---|---|---|---|
| k5607-001 | [18] | [] | None |
| k5607-002 | [] | [] | None |
| k5607-003 | [] | [] | None |
| k5607-004 | [] | [] | None |
| k5607-005 | [1, 2, 16] | [40] | None |
| k5607-006 | [1, 36] | [] | None |
| k5607-007 | [1, 16, 30] | [] | None |
| k5607-008 | [29, 44] | [] | None |
| k5607-009 | [10, 22] | [] | None |
| k5607-010 | [16, 48] | [] | None |
| k5607-011 | [8, 15, 16] | [] | None |
| k5607-012 | [12, 47, 49] | [] | None |
| k5607-013 | [] | [] | None |
| k5607-014 | [] | [] | None |
| k5607-015 | [42] | [] | None |
| k5607-016 | [2, 14, 17] | [33] | None |
| k5607-017 | [8, 12, 40] | [17, 39] | None |
| k5607-018 | [9] | [] | None |
| k5607-019 | [10, 36, 48] | [50] | None |
| k5607-020 | [2, 28, 36] | [] | None |
| k5607-021 | [] | [] | None |
| k5607-022 | [] | [] | None |
| k5607-023 | [18] | [1, 9] | None |
| k5607-024 | [7, 25, 37] | [] | None |
| k5607-025 | [] | [] | None |
| k5607-026 | [] | [] | None |
| k5607-027 | [31, 50] | [] | None |
| k5607-028 | [46] | [] | None |
| k5607-029 | [] | [] | None |
| k5607-030 | [5] | [18] | None |

Association by fresh ALL@5 outcome; counts are descriptive and confounded by query topic and gold breadth. Censored gold cases count observed chunks before the Top50 boundary, not a known gold rank.
```json
{
  "3": {
    "fresh_all5_success": {
      "count": 24,
      "two_or_more_before_any_required_gold_ids": []
    },
    "fresh_all5_failure": {
      "count": 6,
      "two_or_more_before_any_required_gold_ids": []
    }
  },
  "23": {
    "fresh_all5_success": {
      "count": 24,
      "two_or_more_before_any_required_gold_ids": []
    },
    "fresh_all5_failure": {
      "count": 6,
      "two_or_more_before_any_required_gold_ids": []
    }
  }
}
```

## gk001 historical and fresh completeness

Historical cause remains unresolved. Fresh-versus-old changes are not a candidate improvement; no causal attribution to 5607.

| Snapshot | Rank | Chunk | DocumentSourceKey / historical Article | Distance |
|---|---:|---|---|---:|
| M10D | 1 | 4458-madde-210-chunk-001 |  | 0.7273410558700562 |
| M10D | 2 | 4458-madde-215-chunk-001 |  | 0.8435425758361816 |
| M10D | 3 | 4458-madde-216-chunk-001 |  | 0.9153351187705994 |
| M10D | 4 | 4458-madde-214-chunk-001 |  | 0.9260653853416443 |
| M10D | 5 | 4458-madde-168-chunk-001 |  | 0.930628776550293 |
| M12D | 1 | 4458-madde-215-chunk-001 | 4458_gumruk_kanunu/normal/215 | 0.8435425758361816 |
| M12D | 2 | 4458-madde-216-chunk-001 | 4458_gumruk_kanunu/normal/216 | 0.9153351187705994 |
| M12D | 3 | 4458-madde-214-chunk-001 | 4458_gumruk_kanunu/normal/214 | 0.9260653853416443 |
| M12D | 4 | 4458-madde-168-chunk-001 | 4458_gumruk_kanunu/normal/168 | 0.930628776550293 |
| M12D | 5 | 4458-madde-121-chunk-001 | 4458_gumruk_kanunu/normal/121 | 0.9368858337402344 |
| Fresh Top50 | 1 | 4458-madde-210-chunk-001 | 4458_gumruk_kanunu/normal/210 | 0.7275918126106262 |
| Fresh Top50 | 2 | 4458-madde-215-chunk-001 | 4458_gumruk_kanunu/normal/215 | 0.8437895178794861 |
| Fresh Top50 | 3 | 4458-madde-216-chunk-001 | 4458_gumruk_kanunu/normal/216 | 0.9155938029289246 |
| Fresh Top50 | 4 | 4458-madde-214-chunk-001 | 4458_gumruk_kanunu/normal/214 | 0.9264019727706909 |
| Fresh Top50 | 5 | 4458-madde-168-chunk-001 | 4458_gumruk_kanunu/normal/168 | 0.9307778477668762 |
| Fresh Top50 | 6 | 4458-madde-121-chunk-001 | 4458_gumruk_kanunu/normal/121 | 0.9372764229774475 |
| Fresh Top50 | 7 | 4458-madde-78-chunk-001 | 4458_gumruk_kanunu/normal/78 | 0.9422639608383179 |
| Fresh Top50 | 8 | 4458-madde-211-chunk-001 | 4458_gumruk_kanunu/normal/211 | 0.948152482509613 |
| Fresh Top50 | 9 | 4458-madde-213-chunk-001 | 4458_gumruk_kanunu/normal/213 | 0.9508370757102966 |
| Fresh Top50 | 10 | 4458-madde-117-chunk-001 | 4458_gumruk_kanunu/normal/117 | 0.9543179273605347 |
| Fresh Top50 | 11 | 4458-madde-184-chunk-001 | 4458_gumruk_kanunu/normal/184 | 0.9560678601264954 |
| Fresh Top50 | 12 | 4458-madde-181-chunk-001 | 4458_gumruk_kanunu/normal/181 | 0.9638807773590088 |
| Fresh Top50 | 13 | 4458-madde-3-chunk-001 | 4458_gumruk_kanunu/normal/3 | 0.9651229381561279 |
| Fresh Top50 | 14 | 4458-madde-113-chunk-001 | 4458_gumruk_kanunu/normal/113 | 0.9732986092567444 |
| Fresh Top50 | 15 | 4458-madde-3-chunk-002 | 4458_gumruk_kanunu/normal/3 | 0.9794971942901611 |
| Fresh Top50 | 16 | 4458-madde-183-chunk-001 | 4458_gumruk_kanunu/normal/183 | 0.9806180000305176 |
| Fresh Top50 | 17 | 4458-madde-135-chunk-001 | 4458_gumruk_kanunu/normal/135 | 0.9851980805397034 |
| Fresh Top50 | 18 | 4458-madde-161-chunk-001 | 4458_gumruk_kanunu/normal/161 | 0.9927518367767334 |
| Fresh Top50 | 19 | 4458-madde-108-chunk-001 | 4458_gumruk_kanunu/normal/108 | 0.9933346509933472 |
| Fresh Top50 | 20 | 4458-madde-197-chunk-001 | 4458_gumruk_kanunu/normal/197 | 0.9933985471725464 |
| Fresh Top50 | 21 | 4458-madde-231-chunk-001 | 4458_gumruk_kanunu/normal/231 | 0.9986851215362549 |
| Fresh Top50 | 22 | 4458-madde-186-chunk-001 | 4458_gumruk_kanunu/normal/186 | 0.9998480677604675 |
| Fresh Top50 | 23 | 4458-madde-109-chunk-001 | 4458_gumruk_kanunu/normal/109 | 1.0013625621795654 |
| Fresh Top50 | 24 | 4458-madde-232-chunk-001 | 4458_gumruk_kanunu/normal/232 | 1.0014982223510742 |
| Fresh Top50 | 25 | 4458-madde-37-chunk-001 | 4458_gumruk_kanunu/normal/37 | 1.0058510303497314 |
| Fresh Top50 | 26 | 4458-madde-185-chunk-001 | 4458_gumruk_kanunu/normal/185 | 1.0058962106704712 |
| Fresh Top50 | 27 | 4458-madde-79-chunk-001 | 4458_gumruk_kanunu/normal/79 | 1.007079005241394 |
| Fresh Top50 | 28 | 4458-madde-212-chunk-001 | 4458_gumruk_kanunu/normal/212 | 1.007472038269043 |
| Fresh Top50 | 29 | 4458-madde-187-chunk-001 | 4458_gumruk_kanunu/normal/187 | 1.0127363204956055 |
| Fresh Top50 | 30 | 4458-madde-189-chunk-001 | 4458_gumruk_kanunu/normal/189 | 1.0130831003189087 |
| Fresh Top50 | 31 | 4458-madde-234-chunk-001 | 4458_gumruk_kanunu/normal/234 | 1.013700246810913 |
| Fresh Top50 | 32 | 4458-madde-165-b-chunk-001 | 4458_gumruk_kanunu/normal/165/b | 1.0173940658569336 |
| Fresh Top50 | 33 | 4458-madde-123-chunk-001 | 4458_gumruk_kanunu/normal/123 | 1.0175845623016357 |
| Fresh Top50 | 34 | 4458-madde-10-chunk-001 | 4458_gumruk_kanunu/normal/10 | 1.0228549242019653 |
| Fresh Top50 | 35 | 4458-madde-235-chunk-002 | 4458_gumruk_kanunu/normal/235 | 1.0231553316116333 |
| Fresh Top50 | 36 | 4458-madde-119-chunk-001 | 4458_gumruk_kanunu/normal/119 | 1.0298992395401 |
| Fresh Top50 | 37 | 4458-madde-48-chunk-001 | 4458_gumruk_kanunu/normal/48 | 1.030369520187378 |
| Fresh Top50 | 38 | 4458-madde-235-chunk-001 | 4458_gumruk_kanunu/normal/235 | 1.0319201946258545 |
| Fresh Top50 | 39 | 4458-madde-182-chunk-001 | 4458_gumruk_kanunu/normal/182 | 1.032529592514038 |
| Fresh Top50 | 40 | 4458-madde-114-chunk-001 | 4458_gumruk_kanunu/normal/114 | 1.0339019298553467 |
| Fresh Top50 | 41 | 4458-madde-170-chunk-001 | 4458_gumruk_kanunu/normal/170 | 1.03448486328125 |
| Fresh Top50 | 42 | 4458-madde-116-chunk-001 | 4458_gumruk_kanunu/normal/116 | 1.0376055240631104 |
| Fresh Top50 | 43 | 4458-madde-188-chunk-001 | 4458_gumruk_kanunu/normal/188 | 1.0387300252914429 |
| Fresh Top50 | 44 | 4458-madde-236-chunk-001 | 4458_gumruk_kanunu/normal/236 | 1.0393389463424683 |
| Fresh Top50 | 45 | 4458-madde-142-chunk-001 | 4458_gumruk_kanunu/normal/142 | 1.0405343770980835 |
| Fresh Top50 | 46 | 4458-madde-194-chunk-001 | 4458_gumruk_kanunu/normal/194 | 1.0409486293792725 |
| Fresh Top50 | 47 | 4458-madde-52-chunk-001 | 4458_gumruk_kanunu/normal/52 | 1.0409903526306152 |
| Fresh Top50 | 48 | 4458-madde-100-chunk-001 | 4458_gumruk_kanunu/normal/100 | 1.0425310134887695 |
| Fresh Top50 | 49 | 4458-madde-242-chunk-001 | 4458_gumruk_kanunu/normal/242 | 1.0450116395950317 |
| Fresh Top50 | 50 | 4458-madde-124-chunk-001 | 4458_gumruk_kanunu/normal/124 | 1.04922354221344 |

Fresh expected-source ranks: {"first_expected_document_rank": 1, "first_expected_source_rank": 1, "all_expected_sources_recovered_by_rank": 1, "expected_source_ranks": {"4458_gumruk_kanunu/normal/210": 1}}
If Madde 210 is absent Top50, larger-K through 50 did not recover it and cannot explain the historical omission. If present, the exact observed rank above establishes accessibility in this run only.

## Decision boundary

No oracle reranker or candidate performance is calculated. Presence by a deeper cutoff establishes only access to gold for a future scorer, not its ability to select it. The review conclusion must distinguish accepted-cohort recovery, fresh failure bands and historical drift.
Any future candidate informed by this diagnostic requires a NEW UNSEEN HOLDOUT before adoption. No production candidate is selected; no commit or adoption.

## Observed conclusion and next experiment

CATEGORY 3 - Representation/discrimination problem for the primary 5607 failure population; CATEGORY 2 - Mixed across the full benchmark.
Among the six accepted 5607 complete misses, ANY recovery is 1/6 at 10, 20 and 50, entirely k5607-014 already at fresh rank 1; five remain absent Top50. Among the seven accepted ALL failures, 1/7 is complete at 10, 20 and 50; six remain incomplete. No accepted 5607 failure first recovers gold in ranks 6-50. In the full fresh failure population, 8/18 ALL failures recover by 50 (6/18 by 20), while 10 remain incomplete. Thus deeper pools provide access for some historical-law failures but do not resolve the principal 5607 group. These are observations from native ANN rankings, not proof of an embedding cause or exact global nearest-neighbor ranks.

4458 Madde 210 is fresh rank 1 (0.7275918126106262), versus M10D rank 1 and absence from M12D Top5. It is available by 10/20/50 in this run, but not a rank 6-50 recovery. Changing requested K and possible query-vector differences are confounded; the historical omission remains unresolved. No evidence proves 5607 displacement.

At Top50 the still-complete-miss 5607 cases contain only 1, 2, 2, 2 and 3 repeated slots out of 50 for 002, 003, 004, 025 and 026 respectively. k5607-029 has zero repeats despite remaining incomplete. Repeats measurably consume 2-6% of those complete-miss pools, but no material recovery effect is demonstrated and they cannot alone establish why gold is absent. No deduplication or counterfactual ranking was performed.

Across 30 questions, Madde 3 appears in 20 Top50 lists and has multiple chunks in 14; Madde 23 appears in six and has multiple chunks in two. Neither Article has multiple chunks before any required gold source in any question, including censored gold cases. Neither appears anywhere in the six fresh 5607 ALL@5 failure lists. Direct multi-chunk slot consumption is therefore not observed as an explanation of these failures; representation breadth remains untested.

Top5 IDs differ in eight questions; metrics differ only for gk001 and k5607-014. Distances differ beyond absolute 1e-7 (relative 0) in 102 questions, both slotwise and for common chunk IDs. Do not credit any of this drift as intervention improvement.
Recommend one development-only question-representation experiment targeted at implicit-law discrimination, retaining all 105 raw-query controls and separately tracking the within-document k5607-029 miss. A2 in M12F-A showed that filtering alone did not fix even its eligible source miss, so routing alone should not be presumed sufficient. Prioritize representation evidence over a general larger-K reranker for the 5607 cohort. The historical-law cases that do recover deeper form a separate pool-accessible subgroup; no reranker is implemented or scored here. Any future adoption requires a NEW UNSEEN HOLDOUT.
