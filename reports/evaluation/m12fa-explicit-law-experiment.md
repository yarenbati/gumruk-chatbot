# M12F-A — Explicit-Law Signal Experiment

M12F-A READY FOR REVIEW

The intervention was designed after inspecting M12D/M12E development failures. Its scores are development evidence only.
A NEW UNSEEN HOLDOUT is mandatory before production adoption. No production winner is selected. M10E B2 remains NOT VALIDATED.

## Offline detector and scope

Exact M12D loader/adapter reused; 105/105 full question records match. Eligible: 6/105 (5.71%); breakdown {'5326': 0, '4458': 0, '5607': 6}; ambiguous 0; no explicit law 99. Gold contradictions and false activations: 0.
Detector reads only question text with Unicode word boundaries; repeated mentions of one number are one law. Gold is consulted only for the post-detection safety check and scoring.
Eligible IDs: k5607-001, k5607-002, k5607-006, k5607-015, k5607-018, k5607-021
Scope ceiling: 1/6 complete 5607 misses; 1/10 accepted wrong-document Top1 failures. Eligible failure IDs: ['k5607-002']. This is not a recovery forecast.
Untouched complete misses: k5607-003, k5607-004, k5607-014, k5607-025, k5607-026
Untouched wrong-document Top1 failures: q028, gk020, gk028, k5607-003, k5607-004, k5607-009, k5607-014, k5607-025, k5607-026

## Configuration and accounting

B0 uses original raw text. A1 uses the admitted official display title, one blank line, then unchanged original text. A2 shares B0's vector and adds detected-document equality filtering; A3 shares A1's vector and adds that filter. K=5, native L2, no reranking, deduplication, lexical retrieval or corpus re-embedding.
Query embeddings use text-embedding-3-small, 1536 dimensions; SDK max_retries=0. [Official embedding API documentation](https://developers.openai.com/api/docs/guides/embeddings).

```json
{
  "eligible_questions": 6,
  "unique_embedding_inputs": 12,
  "requests": 1,
  "successful_embeddings": 12,
  "failures": 0,
  "prompt_tokens": 688,
  "total_tokens": 688,
  "generation_calls": 0
}
```

Copy verified byte-for-byte before opening. Logical state: {'count': 375, 'distribution': {'5326_kabahatler_kanunu': 53, '4458_gumruk_kanunu': 276, '5607_kacakcilikla_mucadele_kanunu': 46}, 'dimensions': [1536], 'sha256': 'dae0145f680f0c724c0b446e7f8a63b92c59c2175bdbd95fe743f66c7ce72820'}. Production bytes unchanged: True; copy logical state unchanged: True; frozen inputs/code unchanged: True.
Only the copy was opened; full before-copy file hashes and input fingerprints are in JSON.

## Metrics

Eligible-subset scores below are not 105-question system scores. The accepted full M12D baseline is reported separately; excluded questions were not rerun or intervened upon.

| Population / candidate | Metric | @1 | @3 | @5 |
|---|---|---:|---:|---:|
| Eligible n=6 / B0 | source_any | 66.67% | 83.33% | 83.33% |
| Eligible n=6 / B0 | source_all | 66.67% | 83.33% | 83.33% |
| Eligible n=6 / B0 | document_hit | 83.33% | 83.33% | 83.33% |
| Eligible n=6 / B0 | document_all | 83.33% | 83.33% | 83.33% |
| Eligible n=6 / B0 | document_intrusion | 16.67% | 38.89% | 46.67% |
| Eligible n=6 / A1 | source_any | 50.00% | 66.67% | 83.33% |
| Eligible n=6 / A1 | source_all | 50.00% | 66.67% | 83.33% |
| Eligible n=6 / A1 | document_hit | 100.00% | 100.00% | 100.00% |
| Eligible n=6 / A1 | document_all | 100.00% | 100.00% | 100.00% |
| Eligible n=6 / A1 | document_intrusion | 0.00% | 0.00% | 0.00% |
| Eligible n=6 / A2 | source_any | 66.67% | 83.33% | 83.33% |
| Eligible n=6 / A2 | source_all | 66.67% | 83.33% | 83.33% |
| Eligible n=6 / A2 | document_hit | 100.00% | 100.00% | 100.00% |
| Eligible n=6 / A2 | document_all | 100.00% | 100.00% | 100.00% |
| Eligible n=6 / A2 | document_intrusion | 0.00% | 0.00% | 0.00% |
| Eligible n=6 / A3 | source_any | 50.00% | 66.67% | 83.33% |
| Eligible n=6 / A3 | source_all | 50.00% | 66.67% | 83.33% |
| Eligible n=6 / A3 | document_hit | 100.00% | 100.00% | 100.00% |
| Eligible n=6 / A3 | document_all | 100.00% | 100.00% | 100.00% |
| Eligible n=6 / A3 | document_intrusion | 0.00% | 0.00% | 0.00% |
| M12D accepted n=105 | source_any | 64.76% | 79.05% | 85.71% |
| M12D accepted n=105 | source_all | 54.29% | 75.24% | 80.95% |
| M12D accepted n=105 | document_hit | 90.48% | 92.38% | 92.38% |
| M12D accepted n=105 | document_all | 90.48% | 92.38% | 92.38% |
| M12D accepted n=105 | document_intrusion | 9.52% | 15.56% | 17.52% |

## Paired changes versus fresh B0

At each cutoff and each binary coverage metric: false to true = improved; true to false = regressed; same flag = unchanged. Source ANY/ALL and Document Hit/ALL reported separately; no cross-cutoff aggregate hides tradeoffs. Intrusion is a slot fraction, reported separately.

| Candidate | Metric | K | Improved | Unchanged | Regressed |
|---|---|---:|---:|---:|---:|
| A1 | source_any | 1 | 0 | 5 | 1 |
| A1 | source_any | 3 | 1 | 3 | 2 |
| A1 | source_any | 5 | 1 | 4 | 1 |
| A1 | source_all | 1 | 0 | 5 | 1 |
| A1 | source_all | 3 | 1 | 3 | 2 |
| A1 | source_all | 5 | 1 | 4 | 1 |
| A1 | document_hit | 1 | 1 | 5 | 0 |
| A1 | document_hit | 3 | 1 | 5 | 0 |
| A1 | document_hit | 5 | 1 | 5 | 0 |
| A1 | document_all | 1 | 1 | 5 | 0 |
| A1 | document_all | 3 | 1 | 5 | 0 |
| A1 | document_all | 5 | 1 | 5 | 0 |
| A2 | source_any | 1 | 0 | 6 | 0 |
| A2 | source_any | 3 | 0 | 6 | 0 |
| A2 | source_any | 5 | 0 | 6 | 0 |
| A2 | source_all | 1 | 0 | 6 | 0 |
| A2 | source_all | 3 | 0 | 6 | 0 |
| A2 | source_all | 5 | 0 | 6 | 0 |
| A2 | document_hit | 1 | 1 | 5 | 0 |
| A2 | document_hit | 3 | 1 | 5 | 0 |
| A2 | document_hit | 5 | 1 | 5 | 0 |
| A2 | document_all | 1 | 1 | 5 | 0 |
| A2 | document_all | 3 | 1 | 5 | 0 |
| A2 | document_all | 5 | 1 | 5 | 0 |
| A3 | source_any | 1 | 0 | 5 | 1 |
| A3 | source_any | 3 | 1 | 3 | 2 |
| A3 | source_any | 5 | 1 | 4 | 1 |
| A3 | source_all | 1 | 0 | 5 | 1 |
| A3 | source_all | 3 | 1 | 3 | 2 |
| A3 | source_all | 5 | 1 | 4 | 1 |
| A3 | document_hit | 1 | 1 | 5 | 0 |
| A3 | document_hit | 3 | 1 | 5 | 0 |
| A3 | document_hit | 5 | 1 | 5 | 0 |
| A3 | document_all | 1 | 1 | 5 | 0 |
| A3 | document_all | 3 | 1 | 5 | 0 |
| A3 | document_all | 5 | 1 | 5 | 0 |

A2/A3 wrong-document returned slots: {'A2': 0, 'A3': 0}. Zero intrusion is mechanically expected from filtering; it is not evidence by itself of better Article coverage.

## Every eligible paired ranking

### k5607-001

5607 sayılı Kanunun amacı nedir; hangi fiilleri, yaptırımları ve hangi usul ve esasları belirlemeyi hedefler?

Expected: 5607_kacakcilikla_mucadele_kanunu/normal/1
Detected law: 5607; accepted complete miss: False; accepted wrong-document Top1: False.

| Candidate | Rank | Chunk | DocumentSourceKey | L2 |
|---|---:|---|---|---:|
| B0 | 1 | 5607-madde-1-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/normal/1 | 0.658989191 |
| B0 | 2 | 4458-madde-1-chunk-001 | 4458_gumruk_kanunu/normal/1 | 0.821346521 |
| B0 | 3 | 5326-madde-4-chunk-001 | 5326_kabahatler_kanunu/normal/4 | 0.833090842 |
| B0 | 4 | 5326-madde-1-chunk-001 | 5326_kabahatler_kanunu/normal/1 | 0.848129511 |
| B0 | 5 | 5607-madde-19-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/normal/19 | 0.871200204 |
| A1 | 1 | 5607-madde-1-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/normal/1 | 0.309188128 |
| A1 | 2 | 5607-gecici-madde-7-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/gecici/7 | 0.517588913 |
| A1 | 3 | 5607-gecici-madde-1-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/gecici/1 | 0.523388088 |
| A1 | 4 | 5607-madde-27-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/normal/27 | 0.556764424 |
| A1 | 5 | 5607-gecici-madde-5-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/gecici/5 | 0.562735975 |
| A2 | 1 | 5607-madde-1-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/normal/1 | 0.658989191 |
| A2 | 2 | 5607-madde-19-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/normal/19 | 0.871200204 |
| A2 | 3 | 5607-madde-27-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/normal/27 | 0.924537241 |
| A2 | 4 | 5607-madde-4-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/normal/4 | 0.940049291 |
| A2 | 5 | 5607-gecici-madde-3-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/gecici/3 | 0.945686460 |
| A3 | 1 | 5607-madde-1-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/normal/1 | 0.309188128 |
| A3 | 2 | 5607-gecici-madde-7-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/gecici/7 | 0.517588913 |
| A3 | 3 | 5607-gecici-madde-1-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/gecici/1 | 0.523388088 |
| A3 | 4 | 5607-madde-27-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/normal/27 | 0.556764424 |
| A3 | 5 | 5607-gecici-madde-5-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/gecici/5 | 0.562735975 |

Source ANY @1/@3/@5: B0=1/1/1; A1=1/1/1; A2=1/1/1; A3=1/1/1

### k5607-002

5607 sayılı Kanunda “gümrüklenmiş değer” nasıl tanımlanır ve ithal ve ihraç eşyası bakımından hangi değerlerin toplamı esas alınır?

Expected: 5607_kacakcilikla_mucadele_kanunu/normal/2
Detected law: 5607; accepted complete miss: True; accepted wrong-document Top1: True.

| Candidate | Rank | Chunk | DocumentSourceKey | L2 |
|---|---:|---|---|---:|
| B0 | 1 | 4458-madde-25-chunk-001 | 4458_gumruk_kanunu/normal/25 | 0.685515821 |
| B0 | 2 | 4458-madde-235-chunk-001 | 4458_gumruk_kanunu/normal/235 | 0.693084478 |
| B0 | 3 | 4458-madde-126-chunk-001 | 4458_gumruk_kanunu/normal/126 | 0.696084857 |
| B0 | 4 | 4458-madde-143-chunk-001 | 4458_gumruk_kanunu/normal/143 | 0.703128994 |
| B0 | 5 | 4458-madde-26-chunk-001 | 4458_gumruk_kanunu/normal/26 | 0.703281224 |
| A1 | 1 | 5607-madde-15-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/normal/15 | 0.488652289 |
| A1 | 2 | 5607-madde-2-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/normal/2 | 0.552850902 |
| A1 | 3 | 5607-madde-9-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/normal/9 | 0.615230918 |
| A1 | 4 | 5607-gecici-madde-2-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/gecici/2 | 0.620779455 |
| A1 | 5 | 5607-gecici-madde-5-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/gecici/5 | 0.627201021 |
| A2 | 1 | 5607-madde-15-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/normal/15 | 0.765885890 |
| A2 | 2 | 5607-madde-16-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/normal/16 | 0.815049767 |
| A2 | 3 | 5607-madde-11-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/normal/11 | 0.867792010 |
| A2 | 4 | 5607-gecici-madde-6-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/gecici/6 | 0.882754326 |
| A2 | 5 | 5607-madde-23-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/normal/23 | 0.893930256 |
| A3 | 1 | 5607-madde-15-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/normal/15 | 0.488652289 |
| A3 | 2 | 5607-madde-2-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/normal/2 | 0.552850902 |
| A3 | 3 | 5607-madde-9-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/normal/9 | 0.615230918 |
| A3 | 4 | 5607-gecici-madde-2-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/gecici/2 | 0.620779455 |
| A3 | 5 | 5607-gecici-madde-5-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/gecici/5 | 0.627201021 |

Source ANY @1/@3/@5: B0=0/0/0; A1=0/1/1; A2=0/0/0; A3=0/1/1

### k5607-006

Kaçakçılık suçunun teşebbüs aşamasında kalması hâlinde 5607 sayılı Kanun bakımından nasıl cezalandırma yapılır?

Expected: 5607_kacakcilikla_mucadele_kanunu/normal/3
Detected law: 5607; accepted complete miss: False; accepted wrong-document Top1: False.

| Candidate | Rank | Chunk | DocumentSourceKey | L2 |
|---|---:|---|---|---:|
| B0 | 1 | 5607-madde-3-chunk-003 | 5607_kacakcilikla_mucadele_kanunu/normal/3 | 0.629781485 |
| B0 | 2 | 5607-gecici-madde-2-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/gecici/2 | 0.648367584 |
| B0 | 3 | 5607-gecici-madde-12-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/gecici/12 | 0.652404785 |
| B0 | 4 | 5607-madde-13-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/normal/13 | 0.675166547 |
| B0 | 5 | 5607-madde-5-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/normal/5 | 0.691018462 |
| A1 | 1 | 5607-gecici-madde-7-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/gecici/7 | 0.583181202 |
| A1 | 2 | 5607-gecici-madde-2-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/gecici/2 | 0.591193318 |
| A1 | 3 | 5607-gecici-madde-5-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/gecici/5 | 0.592535973 |
| A1 | 4 | 5607-madde-18-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/normal/18 | 0.595742702 |
| A1 | 5 | 5607-madde-17-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/normal/17 | 0.600033045 |
| A2 | 1 | 5607-madde-3-chunk-003 | 5607_kacakcilikla_mucadele_kanunu/normal/3 | 0.629781485 |
| A2 | 2 | 5607-gecici-madde-2-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/gecici/2 | 0.648367584 |
| A2 | 3 | 5607-gecici-madde-12-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/gecici/12 | 0.652404785 |
| A2 | 4 | 5607-madde-13-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/normal/13 | 0.675166547 |
| A2 | 5 | 5607-madde-5-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/normal/5 | 0.691018462 |
| A3 | 1 | 5607-gecici-madde-7-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/gecici/7 | 0.583181202 |
| A3 | 2 | 5607-gecici-madde-2-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/gecici/2 | 0.591193318 |
| A3 | 3 | 5607-gecici-madde-5-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/gecici/5 | 0.592535973 |
| A3 | 4 | 5607-madde-18-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/normal/18 | 0.595742702 |
| A3 | 5 | 5607-madde-17-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/normal/17 | 0.600033045 |

Source ANY @1/@3/@5: B0=1/1/1; A1=0/0/0; A2=1/1/1; A3=0/0/0

### k5607-015

Kaçak eşya taşımasında bilerek kullanılan bir taşıtın müsadere edilebilmesi için 5607 sayılı Kanunda öngörülen koşullardan hangileri vardır?

Expected: 5607_kacakcilikla_mucadele_kanunu/normal/13
Detected law: 5607; accepted complete miss: False; accepted wrong-document Top1: False.

| Candidate | Rank | Chunk | DocumentSourceKey | L2 |
|---|---:|---|---|---:|
| B0 | 1 | 5607-madde-10-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/normal/10 | 0.633339703 |
| B0 | 2 | 5607-madde-13-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/normal/13 | 0.639113784 |
| B0 | 3 | 5607-gecici-madde-5-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/gecici/5 | 0.664871395 |
| B0 | 4 | 5607-madde-6-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/normal/6 | 0.695599794 |
| B0 | 5 | 5607-madde-21-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/normal/21 | 0.697101831 |
| A1 | 1 | 5607-gecici-madde-5-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/gecici/5 | 0.463022292 |
| A1 | 2 | 5607-madde-6-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/normal/6 | 0.508113861 |
| A1 | 3 | 5607-madde-9-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/normal/9 | 0.555016994 |
| A1 | 4 | 5607-madde-13-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/normal/13 | 0.568595827 |
| A1 | 5 | 5607-madde-7-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/normal/7 | 0.574099720 |
| A2 | 1 | 5607-madde-10-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/normal/10 | 0.633339703 |
| A2 | 2 | 5607-madde-13-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/normal/13 | 0.639113784 |
| A2 | 3 | 5607-gecici-madde-5-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/gecici/5 | 0.664871395 |
| A2 | 4 | 5607-madde-6-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/normal/6 | 0.695599794 |
| A2 | 5 | 5607-madde-21-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/normal/21 | 0.697101831 |
| A3 | 1 | 5607-gecici-madde-5-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/gecici/5 | 0.463022292 |
| A3 | 2 | 5607-madde-6-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/normal/6 | 0.508113861 |
| A3 | 3 | 5607-madde-9-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/normal/9 | 0.555016994 |
| A3 | 4 | 5607-madde-13-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/normal/13 | 0.568595827 |
| A3 | 5 | 5607-madde-7-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/normal/7 | 0.574099720 |

Source ANY @1/@3/@5: B0=0/1/1; A1=0/0/1; A2=0/1/1; A3=0/0/1

### k5607-018

5607 sayılı Kanun kapsamındaki suçlar nedeniyle açılan davalara hangi mahkemeler bakar; resmî belgede sahtecilik bağlantısı varsa görevli mahkeme nasıl değişir?

Expected: 5607_kacakcilikla_mucadele_kanunu/normal/17
Detected law: 5607; accepted complete miss: False; accepted wrong-document Top1: False.

| Candidate | Rank | Chunk | DocumentSourceKey | L2 |
|---|---:|---|---|---:|
| B0 | 1 | 5607-madde-17-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/normal/17 | 0.774527669 |
| B0 | 2 | 5607-madde-18-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/normal/18 | 0.825117707 |
| B0 | 3 | 5607-gecici-madde-12-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/gecici/12 | 0.844929874 |
| B0 | 4 | 5326-madde-23-chunk-001 | 5326_kabahatler_kanunu/normal/23 | 0.856855273 |
| B0 | 5 | 5326-madde-43-a-chunk-001 | 5326_kabahatler_kanunu/normal/43/a | 0.858736873 |
| A1 | 1 | 5607-madde-17-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/normal/17 | 0.492356062 |
| A1 | 2 | 5607-madde-18-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/normal/18 | 0.535305440 |
| A1 | 3 | 5607-gecici-madde-7-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/gecici/7 | 0.592330635 |
| A1 | 4 | 5607-gecici-madde-2-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/gecici/2 | 0.599063754 |
| A1 | 5 | 5607-gecici-madde-12-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/gecici/12 | 0.602869153 |
| A2 | 1 | 5607-madde-17-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/normal/17 | 0.774527669 |
| A2 | 2 | 5607-madde-18-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/normal/18 | 0.825117707 |
| A2 | 3 | 5607-gecici-madde-12-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/gecici/12 | 0.844929874 |
| A2 | 4 | 5607-madde-5-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/normal/5 | 0.861289322 |
| A2 | 5 | 5607-gecici-madde-2-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/gecici/2 | 0.890532136 |
| A3 | 1 | 5607-madde-17-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/normal/17 | 0.492356062 |
| A3 | 2 | 5607-madde-18-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/normal/18 | 0.535305440 |
| A3 | 3 | 5607-gecici-madde-7-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/gecici/7 | 0.592330635 |
| A3 | 4 | 5607-gecici-madde-2-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/gecici/2 | 0.599063754 |
| A3 | 5 | 5607-gecici-madde-12-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/gecici/12 | 0.602869153 |

Source ANY @1/@3/@5: B0=1/1/1; A1=1/1/1; A2=1/1/1; A3=1/1/1

### k5607-021

5607 sayılı Kanun çerçevesindeki kontrollü teslimat işlemlerini hangi kurumlar yürütür?

Expected: 5607_kacakcilikla_mucadele_kanunu/normal/21
Detected law: 5607; accepted complete miss: False; accepted wrong-document Top1: False.

| Candidate | Rank | Chunk | DocumentSourceKey | L2 |
|---|---:|---|---|---:|
| B0 | 1 | 5607-madde-21-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/normal/21 | 0.596848011 |
| B0 | 2 | 4458-madde-225-chunk-001 | 4458_gumruk_kanunu/normal/225 | 0.802581966 |
| B0 | 3 | 4458-madde-10-a-chunk-001 | 4458_gumruk_kanunu/normal/10/a | 0.802653790 |
| B0 | 4 | 4458-madde-73-chunk-001 | 4458_gumruk_kanunu/normal/73 | 0.826399148 |
| B0 | 5 | 4458-madde-91-chunk-001 | 4458_gumruk_kanunu/normal/91 | 0.836592495 |
| A1 | 1 | 5607-madde-21-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/normal/21 | 0.377878726 |
| A1 | 2 | 5607-madde-27-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/normal/27 | 0.593178272 |
| A1 | 3 | 5607-madde-24-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/normal/24 | 0.641192079 |
| A1 | 4 | 5607-madde-18-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/normal/18 | 0.658783793 |
| A1 | 5 | 5607-gecici-madde-5-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/gecici/5 | 0.667005301 |
| A2 | 1 | 5607-madde-21-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/normal/21 | 0.596848011 |
| A2 | 2 | 5607-madde-24-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/normal/24 | 0.909969211 |
| A2 | 3 | 5607-madde-11-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/normal/11 | 0.910545945 |
| A2 | 4 | 5607-madde-27-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/normal/27 | 0.979757190 |
| A2 | 5 | 5607-gecici-madde-11-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/gecici/11 | 0.981694043 |
| A3 | 1 | 5607-madde-21-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/normal/21 | 0.377878726 |
| A3 | 2 | 5607-madde-27-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/normal/27 | 0.593178272 |
| A3 | 3 | 5607-madde-24-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/normal/24 | 0.641192079 |
| A3 | 4 | 5607-madde-18-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/normal/18 | 0.658783793 |
| A3 | 5 | 5607-gecici-madde-5-chunk-001 | 5607_kacakcilikla_mucadele_kanunu/gecici/5 | 0.667005301 |

Source ANY @1/@3/@5: B0=1/1/1; A1=1/1/1; A2=1/1/1; A3=1/1/1

## Interpretation boundary

The eligible population is six 5607 questions only. k5607-002 is the only eligible accepted wrong-document/complete-miss case. The remaining five complete 5607 misses cannot be affected by this strategy. Same-run B0 is the comparator; saved M12D is historical context, and per-question B0 drift checks are in JSON.
No corpus re-embedding is needed for these query-side candidates. No production code, index or frozen dataset was changed. No commit or adoption. A new unseen holdout is mandatory.
