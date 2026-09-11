# M12F-D — Implicit Document Centroid Routing Experiment

M12F-D READY FOR REVIEW — ROUTER NOT SUFFICIENT

Development-only diagnostic. No production retrieval, Chroma, chunking, corpus embedding, LLM router, title enrichment, BM25/RRF, supervised fitting or adoption.
A NEW UNSEEN HOLDOUT is mandatory before any future production adoption.

## Population and immutable scope

105 exact M12D questions: 5326=45, 4458=30, 5607=30; implicit=99, explicit=6. The M12F-A literal-law detector is used only for reporting subgroups and never for routing.
Centroids use all existing copy embeddings: 5326=53, 4458=276, 5607=46; 1536 dimensions; one arithmetic mean per document followed by L2 normalization. No document is weighted by chunk count.
B0 is saved historical M12F-B raw/global evidence; R1/R2 are fresh routed retrieval from one new query-embedding batch, so this is development evidence rather than a perfectly same-run causal comparison.

## Accounting

```json
{
  "api": {
    "unique_embedding_inputs": 105,
    "requests": 1,
    "successful_embeddings": 105,
    "failures": 0,
    "prompt_tokens": 5205,
    "total_tokens": 5205,
    "generation_calls": 0
  },
  "copy_query_operations": {
    "R1": 105,
    "R2": 105
  },
  "centroid_statistics": {
    "5326_kabahatler_kanunu": {
      "chunk_count": 53,
      "dimensions": 1536,
      "mean_vector_l2_norm": 0.8307996234863848,
      "normalized_centroid_l2_norm": 0.9999999999999994,
      "centroid_sha256": "4388b47dcae6fb54bf1af4c7240ecff71ea441933c62738e76c999c09de8489c"
    },
    "4458_gumruk_kanunu": {
      "chunk_count": 276,
      "dimensions": 1536,
      "mean_vector_l2_norm": 0.8063356541130507,
      "normalized_centroid_l2_norm": 1.0000000000000004,
      "centroid_sha256": "bbe4da46a503ab23024707108c65ede36c7876f4e8a336e2b2e79d5a946a50b8"
    },
    "5607_kacakcilikla_mucadele_kanunu": {
      "chunk_count": 46,
      "dimensions": 1536,
      "mean_vector_l2_norm": 0.8459584201623037,
      "normalized_centroid_l2_norm": 0.9999999999999991,
      "centroid_sha256": "0be06a071c98ecc1392fad32de85a05b986a3dc672a8363d2a04156cd14b55d8"
    }
  }
}
```

Production Chroma unchanged: True; copy logical state unchanged: True; protected inputs unchanged: True.

## Router-only accuracy

| Group | N | Top1 | Top2 |
|---|---:|---:|---:|
| all | 105 | 88 (83.81%) | 102 (97.14%) |
| implicit | 99 | 84 (84.85%) | 96 (96.97%) |
| explicit | 6 | 4 (66.67%) | 6 (100.00%) |

### Per-document accuracy

| Group | True document | N | Top1 | Top2 |
|---|---|---:|---:|---:|
| all | 5326_kabahatler_kanunu | 45 | 43 | 45 |
| all | 4458_gumruk_kanunu | 30 | 27 | 28 |
| all | 5607_kacakcilikla_mucadele_kanunu | 30 | 18 | 29 |
| implicit | 5326_kabahatler_kanunu | 45 | 43 | 45 |
| implicit | 4458_gumruk_kanunu | 30 | 27 | 28 |
| implicit | 5607_kacakcilikla_mucadele_kanunu | 24 | 14 | 23 |
| explicit | 5326_kabahatler_kanunu | 0 | 0 | 0 |
| explicit | 4458_gumruk_kanunu | 0 | 0 | 0 |
| explicit | 5607_kacakcilikla_mucadele_kanunu | 6 | 4 | 6 |

### Top1 confusion matrix

| True \ Predicted | 5326_kabahatler_kanunu | 4458_gumruk_kanunu | 5607_kacakcilikla_mucadele_kanunu |
|---|---:|---:|---:|
| 5326_kabahatler_kanunu | 43 | 1 | 1 |
| 4458_gumruk_kanunu | 3 | 27 | 0 |
| 5607_kacakcilikla_mucadele_kanunu | 1 | 11 | 18 |

Top1 routing errors: q030, q041, gk020, gk022, gk028, k5607-002, k5607-003, k5607-004, k5607-005, k5607-008, k5607-013, k5607-014, k5607-021, k5607-022, k5607-025, k5607-026, k5607-029.

## Margin analysis

```json
{
  "correct_top1": {
    "count": 88,
    "mean": 0.10629858771818898,
    "median": 0.09974146660613886,
    "min": 0.00015980451619246328,
    "max": 0.2429519247636398
  },
  "incorrect_top1": {
    "count": 17,
    "mean": 0.06796954166366129,
    "median": 0.07431288355430221,
    "min": 0.008482903512277984,
    "max": 0.15627297009550728
  },
  "interpretation": "Incorrect Top1 routes have lower mean and median margins than correct routes (0.067970/0.074313 versus 0.106299/0.099741); the distributions overlap and no production threshold is selected."
}
```

## B0 / R1 / R2 metrics

Coverage cells are fractions; document intrusion is the mean fraction of returned slots whose document is outside the gold document set.

### all

| Variant | Metric | @1 | @3 | @5 |
|---|---|---:|---:|---:|
| B0 | source_any | 66.67% | 80.95% | 87.62% |
| B0 | source_all | 56.19% | 77.14% | 82.86% |
| B0 | document_hit | 91.43% | 93.33% | 93.33% |
| B0 | document_all | 91.43% | 93.33% | 93.33% |
| B0 | document_intrusion | 8.57% | 15.24% | 17.33% |
| R1 | source_any | 60.95% | 73.33% | 78.10% |
| R1 | source_all | 51.43% | 70.48% | 75.24% |
| R1 | document_hit | 83.81% | 83.81% | 83.81% |
| R1 | document_all | 83.81% | 83.81% | 83.81% |
| R1 | document_intrusion | 16.19% | 16.19% | 16.19% |
| R2 | source_any | 65.71% | 80.00% | 86.67% |
| R2 | source_all | 55.24% | 76.19% | 81.90% |
| R2 | document_hit | 90.48% | 92.38% | 92.38% |
| R2 | document_all | 90.48% | 92.38% | 92.38% |
| R2 | document_intrusion | 9.52% | 15.24% | 17.33% |
### doc_5326

| Variant | Metric | @1 | @3 | @5 |
|---|---|---:|---:|---:|
| B0 | source_any | 75.56% | 86.67% | 95.56% |
| B0 | source_all | 64.44% | 82.22% | 88.89% |
| B0 | document_hit | 97.78% | 100.00% | 100.00% |
| B0 | document_all | 97.78% | 100.00% | 100.00% |
| B0 | document_intrusion | 2.22% | 5.93% | 8.44% |
| R1 | source_any | 73.33% | 84.44% | 91.11% |
| R1 | source_all | 62.22% | 80.00% | 84.44% |
| R1 | document_hit | 95.56% | 95.56% | 95.56% |
| R1 | document_all | 95.56% | 95.56% | 95.56% |
| R1 | document_intrusion | 4.44% | 4.44% | 4.44% |
| R2 | source_any | 75.56% | 86.67% | 95.56% |
| R2 | source_all | 64.44% | 82.22% | 88.89% |
| R2 | document_hit | 97.78% | 100.00% | 100.00% |
| R2 | document_all | 97.78% | 100.00% | 100.00% |
| R2 | document_intrusion | 2.22% | 5.19% | 8.44% |
### doc_4458

| Variant | Metric | @1 | @3 | @5 |
|---|---|---:|---:|---:|
| B0 | source_any | 56.67% | 73.33% | 80.00% |
| B0 | source_all | 46.67% | 66.67% | 76.67% |
| B0 | document_hit | 93.33% | 93.33% | 93.33% |
| B0 | document_all | 93.33% | 93.33% | 93.33% |
| B0 | document_intrusion | 6.67% | 6.67% | 6.67% |
| R1 | source_any | 53.33% | 70.00% | 76.67% |
| R1 | source_all | 46.67% | 66.67% | 76.67% |
| R1 | document_hit | 90.00% | 90.00% | 90.00% |
| R1 | document_all | 90.00% | 90.00% | 90.00% |
| R1 | document_intrusion | 10.00% | 10.00% | 10.00% |
| R2 | source_any | 56.67% | 73.33% | 80.00% |
| R2 | source_all | 46.67% | 66.67% | 76.67% |
| R2 | document_hit | 93.33% | 93.33% | 93.33% |
| R2 | document_all | 93.33% | 93.33% | 93.33% |
| R2 | document_intrusion | 6.67% | 6.67% | 6.67% |
### doc_5607

| Variant | Metric | @1 | @3 | @5 |
|---|---|---:|---:|---:|
| B0 | source_any | 63.33% | 80.00% | 83.33% |
| B0 | source_all | 53.33% | 80.00% | 80.00% |
| B0 | document_hit | 80.00% | 83.33% | 83.33% |
| B0 | document_all | 80.00% | 83.33% | 83.33% |
| B0 | document_intrusion | 20.00% | 37.78% | 41.33% |
| R1 | source_any | 50.00% | 60.00% | 60.00% |
| R1 | source_all | 40.00% | 60.00% | 60.00% |
| R1 | document_hit | 60.00% | 60.00% | 60.00% |
| R1 | document_all | 60.00% | 60.00% | 60.00% |
| R1 | document_intrusion | 40.00% | 40.00% | 40.00% |
| R2 | source_any | 60.00% | 76.67% | 80.00% |
| R2 | source_all | 50.00% | 76.67% | 76.67% |
| R2 | document_hit | 76.67% | 80.00% | 80.00% |
| R2 | document_all | 76.67% | 80.00% | 80.00% |
| R2 | document_intrusion | 23.33% | 38.89% | 41.33% |
### implicit

| Variant | Metric | @1 | @3 | @5 |
|---|---|---:|---:|---:|
| B0 | source_any | 66.67% | 80.81% | 87.88% |
| B0 | source_all | 55.56% | 76.77% | 82.83% |
| B0 | document_hit | 91.92% | 93.94% | 93.94% |
| B0 | document_all | 91.92% | 93.94% | 93.94% |
| B0 | document_intrusion | 8.08% | 13.80% | 15.56% |
| R1 | source_any | 61.62% | 73.74% | 78.79% |
| R1 | source_all | 51.52% | 70.71% | 75.76% |
| R1 | document_hit | 84.85% | 84.85% | 84.85% |
| R1 | document_all | 84.85% | 84.85% | 84.85% |
| R1 | document_intrusion | 15.15% | 15.15% | 15.15% |
| R2 | source_any | 65.66% | 79.80% | 86.87% |
| R2 | source_all | 54.55% | 75.76% | 81.82% |
| R2 | document_hit | 90.91% | 92.93% | 92.93% |
| R2 | document_all | 90.91% | 92.93% | 92.93% |
| R2 | document_intrusion | 9.09% | 13.80% | 15.76% |
### explicit

| Variant | Metric | @1 | @3 | @5 |
|---|---|---:|---:|---:|
| B0 | source_any | 66.67% | 83.33% | 83.33% |
| B0 | source_all | 66.67% | 83.33% | 83.33% |
| B0 | document_hit | 83.33% | 83.33% | 83.33% |
| B0 | document_all | 83.33% | 83.33% | 83.33% |
| B0 | document_intrusion | 16.67% | 38.89% | 46.67% |
| R1 | source_any | 50.00% | 66.67% | 66.67% |
| R1 | source_all | 50.00% | 66.67% | 66.67% |
| R1 | document_hit | 66.67% | 66.67% | 66.67% |
| R1 | document_all | 66.67% | 66.67% | 66.67% |
| R1 | document_intrusion | 33.33% | 33.33% | 33.33% |
| R2 | source_any | 66.67% | 83.33% | 83.33% |
| R2 | source_all | 66.67% | 83.33% | 83.33% |
| R2 | document_hit | 83.33% | 83.33% | 83.33% |
| R2 | document_all | 83.33% | 83.33% | 83.33% |
| R2 | document_intrusion | 16.67% | 38.89% | 43.33% |
### single_source

| Variant | Metric | @1 | @3 | @5 |
|---|---|---:|---:|---:|
| B0 | source_any | 67.82% | 83.91% | 89.66% |
| B0 | source_all | 67.82% | 83.91% | 89.66% |
| B0 | document_hit | 93.10% | 95.40% | 95.40% |
| B0 | document_all | 93.10% | 95.40% | 95.40% |
| B0 | document_intrusion | 6.90% | 13.41% | 15.40% |
| R1 | source_any | 62.07% | 75.86% | 80.46% |
| R1 | source_all | 62.07% | 75.86% | 80.46% |
| R1 | document_hit | 86.21% | 86.21% | 86.21% |
| R1 | document_all | 86.21% | 86.21% | 86.21% |
| R1 | document_intrusion | 13.79% | 13.79% | 13.79% |
| R2 | source_any | 66.67% | 82.76% | 88.51% |
| R2 | source_all | 66.67% | 82.76% | 88.51% |
| R2 | document_hit | 91.95% | 94.25% | 94.25% |
| R2 | document_all | 91.95% | 94.25% | 94.25% |
| R2 | document_intrusion | 8.05% | 13.41% | 15.40% |
### multi_source

| Variant | Metric | @1 | @3 | @5 |
|---|---|---:|---:|---:|
| B0 | source_any | 61.11% | 66.67% | 77.78% |
| B0 | source_all | 0.00% | 44.44% | 50.00% |
| B0 | document_hit | 83.33% | 83.33% | 83.33% |
| B0 | document_all | 83.33% | 83.33% | 83.33% |
| B0 | document_intrusion | 16.67% | 24.07% | 26.67% |
| R1 | source_any | 55.56% | 61.11% | 66.67% |
| R1 | source_all | 0.00% | 44.44% | 50.00% |
| R1 | document_hit | 72.22% | 72.22% | 72.22% |
| R1 | document_all | 72.22% | 72.22% | 72.22% |
| R1 | document_intrusion | 27.78% | 27.78% | 27.78% |
| R2 | source_any | 61.11% | 66.67% | 77.78% |
| R2 | source_all | 0.00% | 44.44% | 50.00% |
| R2 | document_hit | 83.33% | 83.33% | 83.33% |
| R2 | document_all | 83.33% | 83.33% | 83.33% |
| R2 | document_intrusion | 16.67% | 24.07% | 26.67% |

## Paired changes against saved B0 at @5

| Candidate | Metric | Improved | Unchanged | Regressed |
|---|---|---:|---:|---:|
| R1 | source_any | 0 | 95 | 10 |
| R1 | source_any improvement IDs | — | | |
| R1 | source_any regression IDs | | | q030, q041, gk022, k5607-005, k5607-008, k5607-013, k5607-014, k5607-021, k5607-022, k5607-029 |
| R1 | source_all | 0 | 97 | 8 |
| R1 | source_all improvement IDs | — | | |
| R1 | source_all regression IDs | | | q030, q041, k5607-005, k5607-008, k5607-013, k5607-014, k5607-021, k5607-022 |
| R1 | document_hit | 0 | 95 | 10 |
| R1 | document_hit improvement IDs | — | | |
| R1 | document_hit regression IDs | | | q030, q041, gk022, k5607-005, k5607-008, k5607-013, k5607-014, k5607-021, k5607-022, k5607-029 |
| R2 | source_any | 0 | 104 | 1 |
| R2 | source_any improvement IDs | — | | |
| R2 | source_any regression IDs | | | k5607-008 |
| R2 | source_all | 0 | 104 | 1 |
| R2 | source_all improvement IDs | — | | |
| R2 | source_all regression IDs | | | k5607-008 |
| R2 | document_hit | 0 | 104 | 1 |
| R2 | document_hit improvement IDs | — | | |
| R2 | document_hit regression IDs | | | k5607-008 |

## Router error cost

```json
[
  {
    "id": "q030",
    "true_document": [
      "5326_kabahatler_kanunu"
    ],
    "predicted_document": "4458_gumruk_kanunu",
    "second_document": "5326_kabahatler_kanunu",
    "similarity_gap": 0.016919907133241874,
    "B0_source_any_5": true,
    "B0_source_all_5": true,
    "R1_source_any_5": false,
    "R1_source_all_5": false,
    "R2_source_any_5": true,
    "R2_source_all_5": true,
    "classification": [
      "A R1 catastrophic regression",
      "B R2 recovers the error"
    ]
  },
  {
    "id": "q041",
    "true_document": [
      "5326_kabahatler_kanunu"
    ],
    "predicted_document": "5607_kacakcilikla_mucadele_kanunu",
    "second_document": "5326_kabahatler_kanunu",
    "similarity_gap": 0.029322375788254584,
    "B0_source_any_5": true,
    "B0_source_all_5": true,
    "R1_source_any_5": false,
    "R1_source_all_5": false,
    "R2_source_any_5": true,
    "R2_source_all_5": true,
    "classification": [
      "A R1 catastrophic regression",
      "B R2 recovers the error"
    ]
  },
  {
    "id": "gk020",
    "true_document": [
      "4458_gumruk_kanunu"
    ],
    "predicted_document": "5326_kabahatler_kanunu",
    "second_document": "5607_kacakcilikla_mucadele_kanunu",
    "similarity_gap": 0.08109251331918088,
    "B0_source_any_5": false,
    "B0_source_all_5": false,
    "R1_source_any_5": false,
    "R1_source_all_5": false,
    "R2_source_any_5": false,
    "R2_source_all_5": false,
    "classification": [
      "C B0 was already wrong",
      "D no retrieval impact"
    ]
  },
  {
    "id": "gk022",
    "true_document": [
      "4458_gumruk_kanunu"
    ],
    "predicted_document": "5326_kabahatler_kanunu",
    "second_document": "4458_gumruk_kanunu",
    "similarity_gap": 0.013909192532598258,
    "B0_source_any_5": true,
    "B0_source_all_5": false,
    "R1_source_any_5": false,
    "R1_source_all_5": false,
    "R2_source_any_5": true,
    "R2_source_all_5": false,
    "classification": [
      "A R1 catastrophic regression",
      "B R2 recovers the error"
    ]
  },
  {
    "id": "gk028",
    "true_document": [
      "4458_gumruk_kanunu"
    ],
    "predicted_document": "5326_kabahatler_kanunu",
    "second_document": "5607_kacakcilikla_mucadele_kanunu",
    "similarity_gap": 0.03776463180230161,
    "B0_source_any_5": false,
    "B0_source_all_5": false,
    "R1_source_any_5": false,
    "R1_source_all_5": false,
    "R2_source_any_5": false,
    "R2_source_all_5": false,
    "classification": [
      "C B0 was already wrong",
      "D no retrieval impact"
    ]
  },
  {
    "id": "k5607-002",
    "true_document": [
      "5607_kacakcilikla_mucadele_kanunu"
    ],
    "predicted_document": "4458_gumruk_kanunu",
    "second_document": "5607_kacakcilikla_mucadele_kanunu",
    "similarity_gap": 0.12543659954036923,
    "B0_source_any_5": false,
    "B0_source_all_5": false,
    "R1_source_any_5": false,
    "R1_source_all_5": false,
    "R2_source_any_5": false,
    "R2_source_all_5": false,
    "classification": [
      "C B0 was already wrong",
      "D no retrieval impact"
    ]
  },
  {
    "id": "k5607-003",
    "true_document": [
      "5607_kacakcilikla_mucadele_kanunu"
    ],
    "predicted_document": "4458_gumruk_kanunu",
    "second_document": "5607_kacakcilikla_mucadele_kanunu",
    "similarity_gap": 0.13246751304658677,
    "B0_source_any_5": false,
    "B0_source_all_5": false,
    "R1_source_any_5": false,
    "R1_source_all_5": false,
    "R2_source_any_5": false,
    "R2_source_all_5": false,
    "classification": [
      "C B0 was already wrong",
      "D no retrieval impact"
    ]
  },
  {
    "id": "k5607-004",
    "true_document": [
      "5607_kacakcilikla_mucadele_kanunu"
    ],
    "predicted_document": "4458_gumruk_kanunu",
    "second_document": "5607_kacakcilikla_mucadele_kanunu",
    "similarity_gap": 0.15627297009550728,
    "B0_source_any_5": false,
    "B0_source_all_5": false,
    "R1_source_any_5": false,
    "R1_source_all_5": false,
    "R2_source_any_5": false,
    "R2_source_all_5": false,
    "classification": [
      "C B0 was already wrong",
      "D no retrieval impact"
    ]
  },
  {
    "id": "k5607-005",
    "true_document": [
      "5607_kacakcilikla_mucadele_kanunu"
    ],
    "predicted_document": "4458_gumruk_kanunu",
    "second_document": "5607_kacakcilikla_mucadele_kanunu",
    "similarity_gap": 0.008482903512277984,
    "B0_source_any_5": true,
    "B0_source_all_5": true,
    "R1_source_any_5": false,
    "R1_source_all_5": false,
    "R2_source_any_5": true,
    "R2_source_all_5": true,
    "classification": [
      "A R1 catastrophic regression",
      "B R2 recovers the error"
    ]
  },
  {
    "id": "k5607-008",
    "true_document": [
      "5607_kacakcilikla_mucadele_kanunu"
    ],
    "predicted_document": "5326_kabahatler_kanunu",
    "second_document": "4458_gumruk_kanunu",
    "similarity_gap": 0.047339960886675636,
    "B0_source_any_5": true,
    "B0_source_all_5": true,
    "R1_source_any_5": false,
    "R1_source_all_5": false,
    "R2_source_any_5": false,
    "R2_source_all_5": false,
    "classification": [
      "A R1 catastrophic regression"
    ]
  },
  {
    "id": "k5607-013",
    "true_document": [
      "5607_kacakcilikla_mucadele_kanunu"
    ],
    "predicted_document": "4458_gumruk_kanunu",
    "second_document": "5607_kacakcilikla_mucadele_kanunu",
    "similarity_gap": 0.020367124175962648,
    "B0_source_any_5": true,
    "B0_source_all_5": true,
    "R1_source_any_5": false,
    "R1_source_all_5": false,
    "R2_source_any_5": true,
    "R2_source_all_5": true,
    "classification": [
      "A R1 catastrophic regression",
      "B R2 recovers the error"
    ]
  },
  {
    "id": "k5607-014",
    "true_document": [
      "5607_kacakcilikla_mucadele_kanunu"
    ],
    "predicted_document": "4458_gumruk_kanunu",
    "second_document": "5607_kacakcilikla_mucadele_kanunu",
    "similarity_gap": 0.08587651830565673,
    "B0_source_any_5": true,
    "B0_source_all_5": true,
    "R1_source_any_5": false,
    "R1_source_all_5": false,
    "R2_source_any_5": true,
    "R2_source_all_5": true,
    "classification": [
      "A R1 catastrophic regression",
      "B R2 recovers the error"
    ]
  },
  {
    "id": "k5607-021",
    "true_document": [
      "5607_kacakcilikla_mucadele_kanunu"
    ],
    "predicted_document": "4458_gumruk_kanunu",
    "second_document": "5607_kacakcilikla_mucadele_kanunu",
    "similarity_gap": 0.05121842924394315,
    "B0_source_any_5": true,
    "B0_source_all_5": true,
    "R1_source_any_5": false,
    "R1_source_all_5": false,
    "R2_source_any_5": true,
    "R2_source_all_5": true,
    "classification": [
      "A R1 catastrophic regression",
      "B R2 recovers the error"
    ]
  },
  {
    "id": "k5607-022",
    "true_document": [
      "5607_kacakcilikla_mucadele_kanunu"
    ],
    "predicted_document": "4458_gumruk_kanunu",
    "second_document": "5607_kacakcilikla_mucadele_kanunu",
    "similarity_gap": 0.07748840771249232,
    "B0_source_any_5": true,
    "B0_source_all_5": true,
    "R1_source_any_5": false,
    "R1_source_all_5": false,
    "R2_source_any_5": true,
    "R2_source_all_5": true,
    "classification": [
      "A R1 catastrophic regression",
      "B R2 recovers the error"
    ]
  },
  {
    "id": "k5607-025",
    "true_document": [
      "5607_kacakcilikla_mucadele_kanunu"
    ],
    "predicted_document": "4458_gumruk_kanunu",
    "second_document": "5607_kacakcilikla_mucadele_kanunu",
    "similarity_gap": 0.07939171337844153,
    "B0_source_any_5": false,
    "B0_source_all_5": false,
    "R1_source_any_5": false,
    "R1_source_all_5": false,
    "R2_source_any_5": false,
    "R2_source_all_5": false,
    "classification": [
      "C B0 was already wrong",
      "D no retrieval impact"
    ]
  },
  {
    "id": "k5607-026",
    "true_document": [
      "5607_kacakcilikla_mucadele_kanunu"
    ],
    "predicted_document": "4458_gumruk_kanunu",
    "second_document": "5607_kacakcilikla_mucadele_kanunu",
    "similarity_gap": 0.11781856425444914,
    "B0_source_any_5": false,
    "B0_source_all_5": false,
    "R1_source_any_5": false,
    "R1_source_all_5": false,
    "R2_source_any_5": false,
    "R2_source_all_5": false,
    "classification": [
      "C B0 was already wrong",
      "D no retrieval impact"
    ]
  },
  {
    "id": "k5607-029",
    "true_document": [
      "5607_kacakcilikla_mucadele_kanunu"
    ],
    "predicted_document": "4458_gumruk_kanunu",
    "second_document": "5607_kacakcilikla_mucadele_kanunu",
    "similarity_gap": 0.07431288355430221,
    "B0_source_any_5": true,
    "B0_source_all_5": false,
    "R1_source_any_5": false,
    "R1_source_all_5": false,
    "R2_source_any_5": true,
    "R2_source_all_5": false,
    "classification": [
      "A R1 catastrophic regression",
      "B R2 recovers the error"
    ]
  }
]
```

## Primary and control cases

### k5607-002

Routing: 1 4458_gumruk_kanunu=0.693198205; 2 5607_kacakcilikla_mucadele_kanunu=0.567761605; 3 5326_kabahatler_kanunu=0.518900296
True document rank: 2

- B0 Top5: 4458-madde-25-chunk-001, 4458-madde-235-chunk-001, 4458-madde-126-chunk-001, 4458-madde-143-chunk-001, 4458-madde-26-chunk-001; expected source ranks: 5607_kacakcilikla_mucadele_kanunu/normal/2=MISS
- R1 Top5: 4458-madde-25-chunk-001, 4458-madde-235-chunk-001, 4458-madde-126-chunk-001, 4458-madde-143-chunk-001, 4458-madde-26-chunk-001; expected source ranks: 5607_kacakcilikla_mucadele_kanunu/normal/2=MISS
- R2 Top5: 4458-madde-25-chunk-001, 4458-madde-235-chunk-001, 4458-madde-126-chunk-001, 4458-madde-143-chunk-001, 4458-madde-26-chunk-001; expected source ranks: 5607_kacakcilikla_mucadele_kanunu/normal/2=MISS

### k5607-003

Routing: 1 4458_gumruk_kanunu=0.660749901; 2 5607_kacakcilikla_mucadele_kanunu=0.528282388; 3 5326_kabahatler_kanunu=0.465495223
True document rank: 2

- B0 Top5: 4458-madde-236-chunk-001, 4458-madde-235-chunk-001, 4458-madde-239-chunk-001, 4458-madde-57-chunk-001, 4458-madde-186-chunk-001; expected source ranks: 5607_kacakcilikla_mucadele_kanunu/normal/3=MISS
- R1 Top5: 4458-madde-236-chunk-001, 4458-madde-235-chunk-001, 4458-madde-239-chunk-001, 4458-madde-57-chunk-001, 4458-madde-186-chunk-001; expected source ranks: 5607_kacakcilikla_mucadele_kanunu/normal/3=MISS
- R2 Top5: 4458-madde-236-chunk-001, 4458-madde-235-chunk-001, 4458-madde-239-chunk-001, 4458-madde-57-chunk-001, 4458-madde-186-chunk-001; expected source ranks: 5607_kacakcilikla_mucadele_kanunu/normal/3=MISS

### k5607-004

Routing: 1 4458_gumruk_kanunu=0.634213870; 2 5607_kacakcilikla_mucadele_kanunu=0.477940900; 3 5326_kabahatler_kanunu=0.439046182
True document rank: 2

- B0 Top5: 4458-madde-141-chunk-001, 4458-madde-179-chunk-001, 4458-madde-27-chunk-001, 4458-madde-25-chunk-001, 4458-madde-24-chunk-001; expected source ranks: 5607_kacakcilikla_mucadele_kanunu/normal/3=MISS
- R1 Top5: 4458-madde-141-chunk-001, 4458-madde-179-chunk-001, 4458-madde-27-chunk-001, 4458-madde-25-chunk-001, 4458-madde-24-chunk-001; expected source ranks: 5607_kacakcilikla_mucadele_kanunu/normal/3=MISS
- R2 Top5: 4458-madde-141-chunk-001, 4458-madde-179-chunk-001, 4458-madde-27-chunk-001, 4458-madde-25-chunk-001, 4458-madde-24-chunk-001; expected source ranks: 5607_kacakcilikla_mucadele_kanunu/normal/3=MISS

### k5607-025

Routing: 1 4458_gumruk_kanunu=0.641478005; 2 5607_kacakcilikla_mucadele_kanunu=0.562086291; 3 5326_kabahatler_kanunu=0.486821455
True document rank: 2

- B0 Top5: 4458-madde-57-chunk-001, 4458-madde-167-chunk-002, 4458-madde-235-chunk-002, 4458-madde-235-chunk-001, 4458-madde-236-chunk-001; expected source ranks: 5607_kacakcilikla_mucadele_kanunu/normal/3=MISS, 5607_kacakcilikla_mucadele_kanunu/normal/4=MISS
- R1 Top5: 4458-madde-57-chunk-001, 4458-madde-167-chunk-002, 4458-madde-235-chunk-002, 4458-madde-235-chunk-001, 4458-madde-236-chunk-001; expected source ranks: 5607_kacakcilikla_mucadele_kanunu/normal/3=MISS, 5607_kacakcilikla_mucadele_kanunu/normal/4=MISS
- R2 Top5: 4458-madde-57-chunk-001, 4458-madde-167-chunk-002, 4458-madde-235-chunk-002, 4458-madde-235-chunk-001, 4458-madde-236-chunk-001; expected source ranks: 5607_kacakcilikla_mucadele_kanunu/normal/3=MISS, 5607_kacakcilikla_mucadele_kanunu/normal/4=MISS

### k5607-026

Routing: 1 4458_gumruk_kanunu=0.688540311; 2 5607_kacakcilikla_mucadele_kanunu=0.570721746; 3 5326_kabahatler_kanunu=0.532733560
True document rank: 2

- B0 Top5: 4458-madde-57-chunk-001, 4458-madde-24-chunk-001, 4458-madde-187-chunk-001, 4458-madde-235-chunk-002, 4458-madde-234-chunk-001; expected source ranks: 5607_kacakcilikla_mucadele_kanunu/normal/3=MISS, 5607_kacakcilikla_mucadele_kanunu/normal/5=MISS
- R1 Top5: 4458-madde-57-chunk-001, 4458-madde-24-chunk-001, 4458-madde-187-chunk-001, 4458-madde-235-chunk-002, 4458-madde-234-chunk-001; expected source ranks: 5607_kacakcilikla_mucadele_kanunu/normal/3=MISS, 5607_kacakcilikla_mucadele_kanunu/normal/5=MISS
- R2 Top5: 4458-madde-57-chunk-001, 4458-madde-24-chunk-001, 4458-madde-187-chunk-001, 4458-madde-235-chunk-002, 4458-madde-234-chunk-001; expected source ranks: 5607_kacakcilikla_mucadele_kanunu/normal/3=MISS, 5607_kacakcilikla_mucadele_kanunu/normal/5=MISS

### k5607-029

Routing: 1 4458_gumruk_kanunu=0.643221372; 2 5607_kacakcilikla_mucadele_kanunu=0.568908489; 3 5326_kabahatler_kanunu=0.548778947
True document rank: 2

- B0 Top5: 5607-gecici-madde-11-chunk-001, 4458-gecici-madde-9-chunk-001, 4458-gecici-madde-10-chunk-001, 5607-gecici-madde-10-chunk-001, 4458-madde-180-chunk-001; expected source ranks: 5607_kacakcilikla_mucadele_kanunu/gecici/10=4, 5607_kacakcilikla_mucadele_kanunu/normal/3=MISS
- R1 Top5: 4458-gecici-madde-9-chunk-001, 4458-gecici-madde-10-chunk-001, 4458-madde-180-chunk-001, 4458-madde-216-chunk-001, 4458-madde-238-chunk-001; expected source ranks: 5607_kacakcilikla_mucadele_kanunu/gecici/10=MISS, 5607_kacakcilikla_mucadele_kanunu/normal/3=MISS
- R2 Top5: 5607-gecici-madde-11-chunk-001, 4458-gecici-madde-9-chunk-001, 4458-gecici-madde-10-chunk-001, 5607-gecici-madde-10-chunk-001, 4458-madde-180-chunk-001; expected source ranks: 5607_kacakcilikla_mucadele_kanunu/gecici/10=4, 5607_kacakcilikla_mucadele_kanunu/normal/3=MISS

### k5607-014

Routing: 1 4458_gumruk_kanunu=0.568196559; 2 5607_kacakcilikla_mucadele_kanunu=0.482320040; 3 5326_kabahatler_kanunu=0.399174950
True document rank: 2

- B0 Top5: 5607-madde-12-chunk-001, 4458-madde-56-chunk-001, 4458-madde-235-chunk-001, 4458-madde-175-chunk-001, 4458-madde-10-a-chunk-001; expected source ranks: 5607_kacakcilikla_mucadele_kanunu/normal/12=1
- R1 Top5: 4458-madde-56-chunk-001, 4458-madde-235-chunk-001, 4458-madde-175-chunk-001, 4458-madde-10-a-chunk-001, 4458-madde-48-chunk-001; expected source ranks: 5607_kacakcilikla_mucadele_kanunu/normal/12=MISS
- R2 Top5: 5607-madde-12-chunk-001, 4458-madde-56-chunk-001, 4458-madde-235-chunk-001, 4458-madde-175-chunk-001, 4458-madde-10-a-chunk-001; expected source ranks: 5607_kacakcilikla_mucadele_kanunu/normal/12=1

### k5607-017

Routing: 1 5607_kacakcilikla_mucadele_kanunu=0.444827294; 2 4458_gumruk_kanunu=0.369438900; 3 5326_kabahatler_kanunu=0.305863203
True document rank: 1

- B0 Top5: 5607-madde-16-a-chunk-001, 5607-madde-11-chunk-001, 5607-gecici-madde-15-chunk-001, 5607-madde-16-chunk-001, 5607-gecici-madde-6-chunk-001; expected source ranks: 5607_kacakcilikla_mucadele_kanunu/normal/16/a=1
- R1 Top5: 5607-madde-16-a-chunk-001, 5607-madde-11-chunk-001, 5607-gecici-madde-15-chunk-001, 5607-madde-16-chunk-001, 5607-gecici-madde-6-chunk-001; expected source ranks: 5607_kacakcilikla_mucadele_kanunu/normal/16/a=1
- R2 Top5: 5607-madde-16-a-chunk-001, 5607-madde-11-chunk-001, 5607-gecici-madde-15-chunk-001, 5607-madde-16-chunk-001, 5607-gecici-madde-6-chunk-001; expected source ranks: 5607_kacakcilikla_mucadele_kanunu/normal/16/a=1

### k5607-023

Routing: 1 5607_kacakcilikla_mucadele_kanunu=0.574813748; 2 4458_gumruk_kanunu=0.521751774; 3 5326_kabahatler_kanunu=0.515582617
True document rank: 1

- B0 Top5: 5607-madde-23-chunk-001, 5607-madde-16-chunk-001, 5607-madde-10-chunk-001, 5607-madde-13-chunk-001, 5607-madde-5-chunk-001; expected source ranks: 5607_kacakcilikla_mucadele_kanunu/normal/23=1
- R1 Top5: 5607-madde-23-chunk-001, 5607-madde-16-chunk-001, 5607-madde-10-chunk-001, 5607-madde-13-chunk-001, 5607-madde-5-chunk-001; expected source ranks: 5607_kacakcilikla_mucadele_kanunu/normal/23=1
- R2 Top5: 5607-madde-23-chunk-001, 5607-madde-16-chunk-001, 5607-madde-10-chunk-001, 5607-madde-13-chunk-001, 5607-madde-5-chunk-001; expected source ranks: 5607_kacakcilikla_mucadele_kanunu/normal/23=1

### k5607-028

Routing: 1 5607_kacakcilikla_mucadele_kanunu=0.528292307; 2 4458_gumruk_kanunu=0.478720656; 3 5326_kabahatler_kanunu=0.453142308
True document rank: 1

- B0 Top5: 5607-gecici-madde-7-chunk-001, 4458-gecici-madde-7-chunk-001, 5607-gecici-madde-14-chunk-001, 5607-madde-26-chunk-001, 5607-gecici-madde-15-chunk-001; expected source ranks: 5607_kacakcilikla_mucadele_kanunu/gecici/7=1
- R1 Top5: 5607-gecici-madde-7-chunk-001, 5607-gecici-madde-14-chunk-001, 5607-madde-26-chunk-001, 5607-gecici-madde-15-chunk-001, 5607-gecici-madde-10-chunk-001; expected source ranks: 5607_kacakcilikla_mucadele_kanunu/gecici/7=1
- R2 Top5: 5607-gecici-madde-7-chunk-001, 4458-gecici-madde-7-chunk-001, 5607-gecici-madde-14-chunk-001, 5607-madde-26-chunk-001, 5607-gecici-madde-15-chunk-001; expected source ranks: 5607_kacakcilikla_mucadele_kanunu/gecici/7=1

### k5607-030

Routing: 1 5607_kacakcilikla_mucadele_kanunu=0.581260874; 2 5326_kabahatler_kanunu=0.563416124; 3 4458_gumruk_kanunu=0.519111544
True document rank: 1

- B0 Top5: 5607-gecici-madde-12-chunk-001, 5607-madde-5-chunk-001, 5326-madde-27-chunk-001, 5607-gecici-madde-11-chunk-001, 5607-madde-3-chunk-003; expected source ranks: 5607_kacakcilikla_mucadele_kanunu/gecici/12=1, 5607_kacakcilikla_mucadele_kanunu/normal/5=2
- R1 Top5: 5607-gecici-madde-12-chunk-001, 5607-madde-5-chunk-001, 5607-gecici-madde-11-chunk-001, 5607-madde-3-chunk-003, 5607-gecici-madde-2-chunk-001; expected source ranks: 5607_kacakcilikla_mucadele_kanunu/gecici/12=1, 5607_kacakcilikla_mucadele_kanunu/normal/5=2
- R2 Top5: 5607-gecici-madde-12-chunk-001, 5607-madde-5-chunk-001, 5326-madde-27-chunk-001, 5607-gecici-madde-11-chunk-001, 5607-madde-3-chunk-003; expected source ranks: 5607_kacakcilikla_mucadele_kanunu/gecici/12=1, 5607_kacakcilikla_mucadele_kanunu/normal/5=2

## Interpretation

003/004 are evaluated as document-discrimination cases when the router predicts 5607 and retrieval improves; 026/029 remain separate within-document provision-selection tests if either expected source remains outside Top5. 025 remains a multi-source composite test.

The fixed unsupervised centroid router is diagnostic only. No benchmark-label fitting, production change, candidate adoption or routing implementation occurred.

Next experiment: Run one development-only LLM-based question-only document-router comparison, without gold document input; continue separate multi-source provision coverage tracking. A NEW UNSEEN HOLDOUT is required before adoption.

No candidate is adopted. No commit is part of this milestone.
