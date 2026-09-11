# M12F-C — Oracle Retrieval Decomposition Diagnostic

M12F-C READY FOR REVIEW

Oracle-filter performance is a decomposition diagnostic, not deployable retrieval performance.
The correct document is supplied from frozen gold solely to diagnose failure. It is not information available to the real chatbot and is not a proposed router. No production candidate is selected.
Any future adopted candidate requires a NEW UNSEEN HOLDOUT. No production code, index, corpus embeddings, chunking or frozen datasets changed.

## Population, variants and accounting

30 frozen 5607 document-source-v1 records, loaded through the exact reviewed M12D path. Full records match M12D/M12F-B; frozen bytes are fingerprinted. No Article information, answer text or expected-source text is added to queries.
Official manifest display title: 5607 Sayılı Kaçakçılıkla Mücadele Kanunu
G0 uses saved M12F-B raw vectors/rankings; O1 raw vectors are newly embedded as authorized. Possible temporal/numerical query-vector drift is not isolated. O3 versus O1 is same-run; no fresh raw/global control was run.

- G0: Saved M12F-B raw original query + global corpus, Top50; NOT rerun
- O1: Fresh raw query + oracle 5607 document, all 46 chunks
- O2: Document-title-enriched query + global corpus, Top50
- O3: Same enriched vector as O2 + oracle 5607 document, all 46 chunks

```json
{
  "api": {
    "unique_embedding_inputs": 60,
    "requests": 1,
    "successful_embeddings": 60,
    "failures": 0,
    "prompt_tokens": 4510,
    "total_tokens": 4510,
    "generation_calls": 0
  },
  "query_operations": {
    "G0": 0,
    "O1": 30,
    "O2": 30,
    "O3": 30
  },
  "saved_rank_counts": {
    "G0": 1500,
    "O1": 1380,
    "O2": 1500,
    "O3": 1380
  },
  "oracle_validation": {
    "exhaustive_rankings": 60,
    "expected_chunks_each": 46,
    "missing_gold_sources": 0,
    "wrong_document_slots": 0
  }
}
```
Copy byte equality verified before opening; logical corpus {'count': 375, 'distribution': {'5326_kabahatler_kanunu': 53, '4458_gumruk_kanunu': 276, '5607_kacakcilikla_mucadele_kanunu': 46}, 'dimensions': [1536], 'sha256': 'dae0145f680f0c724c0b446e7f8a63b92c59c2175bdbd95fe743f66c7ce72820'}. Production bytes unchanged: True; copy logical state unchanged: True; protected inputs unchanged: True.

## Diagnostic coverage (not production accuracy)

O1/O3 @50 means all 46 available chunks. Complete coverage there is an exhaustive-corpus sanity check. Rankings are not deduplicated.

| Variant | Metric | @1 | @3 | @5 | @10 | @20 | @50 |
|---|---|---:|---:|---:|---:|---:|---:|
| G0 | source_any | 63.33% | 80.00% | 83.33% | 83.33% | 83.33% | 83.33% |
| G0 | source_all | 53.33% | 80.00% | 80.00% | 80.00% | 80.00% | 80.00% |
| G0 | document_hit | 80.00% | 83.33% | 83.33% | 83.33% | 83.33% | 86.67% |
| G0 | document_all | 80.00% | 83.33% | 83.33% | 83.33% | 83.33% | 86.67% |
| G0 | document_intrusion | 20.00% | 37.78% | 41.33% | 46.00% | 52.00% | 64.27% |
| O1 | source_any | 66.67% | 93.33% | 96.67% | 100.00% | 100.00% | 100.00% |
| O1 | source_all | 56.67% | 86.67% | 86.67% | 93.33% | 100.00% | 100.00% |
| O1 | document_hit | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% |
| O1 | document_all | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% |
| O1 | document_intrusion | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| O2 | source_any | 60.00% | 76.67% | 86.67% | 93.33% | 96.67% | 100.00% |
| O2 | source_all | 46.67% | 60.00% | 73.33% | 83.33% | 90.00% | 100.00% |
| O2 | document_hit | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% |
| O2 | document_all | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% |
| O2 | document_intrusion | 0.00% | 0.00% | 0.00% | 0.33% | 1.00% | 14.73% |
| O3 | source_any | 60.00% | 76.67% | 86.67% | 93.33% | 96.67% | 100.00% |
| O3 | source_all | 46.67% | 60.00% | 73.33% | 83.33% | 90.00% | 100.00% |
| O3 | document_hit | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% |
| O3 | document_all | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% |
| O3 | document_intrusion | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |

## Every required source: exact ranks and within-document deltas

Global >50 is censored and never converted into a numeric rank delta. O1/O3 ranks are out of 46. Negative O3-O1 means improvement.

| ID | Required source | G0 | O1 /46 | O2 | O3 /46 | O3-O1 |
|---|---|---:|---:|---:|---:|---:|
| k5607-001 | 5607_kacakcilikla_mucadele_kanunu/normal/1 | 1 | 1 | 1 | 1 | 0 |
| k5607-002 | 5607_kacakcilikla_mucadele_kanunu/normal/2 | >50 | 8 | 2 | 2 | -6 |
| k5607-003 | 5607_kacakcilikla_mucadele_kanunu/normal/3 | >50 | 2 | 4 | 4 | 2 |
| k5607-004 | 5607_kacakcilikla_mucadele_kanunu/normal/3 | >50 | 2 | 2 | 2 | 0 |
| k5607-005 | 5607_kacakcilikla_mucadele_kanunu/normal/3 | 1 | 1 | 1 | 1 | 0 |
| k5607-006 | 5607_kacakcilikla_mucadele_kanunu/normal/3 | 1 | 1 | 8 | 8 | 7 |
| k5607-007 | 5607_kacakcilikla_mucadele_kanunu/normal/4 | 3 | 3 | 2 | 2 | -1 |
| k5607-008 | 5607_kacakcilikla_mucadele_kanunu/normal/5 | 1 | 1 | 1 | 1 | 0 |
| k5607-009 | 5607_kacakcilikla_mucadele_kanunu/normal/6 | 3 | 1 | 1 | 1 | 0 |
| k5607-010 | 5607_kacakcilikla_mucadele_kanunu/normal/7 | 1 | 1 | 1 | 1 | 0 |
| k5607-011 | 5607_kacakcilikla_mucadele_kanunu/normal/9 | 1 | 1 | 1 | 1 | 0 |
| k5607-012 | 5607_kacakcilikla_mucadele_kanunu/normal/10 | 1 | 1 | 1 | 1 | 0 |
| k5607-012 | 5607_kacakcilikla_mucadele_kanunu/normal/13 | 2 | 2 | 4 | 4 | 2 |
| k5607-013 | 5607_kacakcilikla_mucadele_kanunu/normal/11 | 2 | 2 | 20 | 20 | 18 |
| k5607-014 | 5607_kacakcilikla_mucadele_kanunu/normal/12 | 1 | 1 | 1 | 1 | 0 |
| k5607-015 | 5607_kacakcilikla_mucadele_kanunu/normal/13 | 2 | 2 | 4 | 4 | 2 |
| k5607-016 | 5607_kacakcilikla_mucadele_kanunu/normal/16 | 1 | 1 | 6 | 6 | 5 |
| k5607-017 | 5607_kacakcilikla_mucadele_kanunu/normal/16/a | 1 | 1 | 1 | 1 | 0 |
| k5607-018 | 5607_kacakcilikla_mucadele_kanunu/normal/17 | 1 | 1 | 1 | 1 | 0 |
| k5607-019 | 5607_kacakcilikla_mucadele_kanunu/normal/19 | 2 | 2 | 2 | 2 | 0 |
| k5607-020 | 5607_kacakcilikla_mucadele_kanunu/normal/20 | 1 | 1 | 1 | 1 | 0 |
| k5607-021 | 5607_kacakcilikla_mucadele_kanunu/normal/21 | 1 | 1 | 1 | 1 | 0 |
| k5607-022 | 5607_kacakcilikla_mucadele_kanunu/normal/22 | 1 | 1 | 1 | 1 | 0 |
| k5607-023 | 5607_kacakcilikla_mucadele_kanunu/normal/23 | 1 | 1 | 26 | 26 | 25 |
| k5607-024 | 5607_kacakcilikla_mucadele_kanunu/normal/24 | 1 | 1 | 1 | 1 | 0 |
| k5607-025 | 5607_kacakcilikla_mucadele_kanunu/normal/3 | >50 | 4 | 4 | 4 | 0 |
| k5607-025 | 5607_kacakcilikla_mucadele_kanunu/normal/4 | >50 | 8 | 11 | 11 | 3 |
| k5607-026 | 5607_kacakcilikla_mucadele_kanunu/normal/3 | >50 | 11 | 5 | 5 | -6 |
| k5607-026 | 5607_kacakcilikla_mucadele_kanunu/normal/5 | >50 | 2 | 1 | 1 | -1 |
| k5607-027 | 5607_kacakcilikla_mucadele_kanunu/normal/11 | 3 | 3 | 22 | 22 | 19 |
| k5607-027 | 5607_kacakcilikla_mucadele_kanunu/normal/16 | 1 | 1 | 3 | 3 | 2 |
| k5607-028 | 5607_kacakcilikla_mucadele_kanunu/gecici/7 | 1 | 1 | 1 | 1 | 0 |
| k5607-029 | 5607_kacakcilikla_mucadele_kanunu/gecici/10 | 4 | 2 | 1 | 1 | -1 |
| k5607-029 | 5607_kacakcilikla_mucadele_kanunu/normal/3 | >50 | 16 | 21 | 21 | 5 |
| k5607-030 | 5607_kacakcilikla_mucadele_kanunu/gecici/12 | 1 | 1 | 1 | 1 | 0 |
| k5607-030 | 5607_kacakcilikla_mucadele_kanunu/normal/5 | 2 | 2 | 7 | 7 | 5 |

## Primary decomposition and distance evidence

Rules describe overlapping observations: O1 <=10 indicates accessible gold; O1 >10 indicates provision-selection difficulty; both O1/O3 >20 flag persistent poor ranks. These are descriptive thresholds, not causal diagnoses of chunks. Exact ranks and cutoff crossings take precedence over labels.

### k5607-002

5607 sayılı Kanunda “gümrüklenmiş değer” nasıl tanımlanır ve ithal ve ihraç eşyası bakımından hangi değerlerin toplamı esas alınır?
ALL recovered ranks (G0/O1/O2/O3): >50 / 8 / 2 / 2
First expected document ranks (G0/O2): >50 / 1

5607_kacakcilikla_mucadele_kanunu/normal/2: document competition supported: G0 censored, O1 <=10; enriched global source rank improves (historical G0 comparator); enrichment improves within-document source rank

Within-query distance evidence only; absolute L2 thresholds are not transferable across questions.
```json
{
  "O1": {
    "5607_kacakcilikla_mucadele_kanunu/normal/2": {
      "rank": 8,
      "top1_distance": 0.7658208608627319,
      "gold_distance": 0.9050151705741882,
      "gold_minus_top1": 0.1391943097114563
    }
  },
  "O3": {
    "5607_kacakcilikla_mucadele_kanunu/normal/2": {
      "rank": 2,
      "top1_distance": 0.48868197202682495,
      "gold_distance": 0.5526976585388184,
      "gold_minus_top1": 0.06401568651199341
    }
  }
}
```

### k5607-003

Eşyanın gümrük işlemlerine tabi tutulmadan ülkeye sokulması hangi hapis ve adlî para cezasını gerektirir; eşya gümrük kapıları dışından sokulursa ceza nasıl değişir?
ALL recovered ranks (G0/O1/O2/O3): >50 / 2 / 4 / 4
First expected document ranks (G0/O2): >50 / 1

5607_kacakcilikla_mucadele_kanunu/normal/3: document competition supported: G0 censored, O1 <=10; enriched global source rank improves (historical G0 comparator); enrichment worsens within-document source rank

Within-query distance evidence only; absolute L2 thresholds are not transferable across questions.
```json
{
  "O1": {
    "5607_kacakcilikla_mucadele_kanunu/normal/3": {
      "rank": 2,
      "top1_distance": 0.8563374876976013,
      "gold_distance": 0.8607267737388611,
      "gold_minus_top1": 0.004389286041259766
    }
  },
  "O3": {
    "5607_kacakcilikla_mucadele_kanunu/normal/3": {
      "rank": 4,
      "top1_distance": 0.4500713050365448,
      "gold_distance": 0.5102445483207703,
      "gold_minus_top1": 0.060173243284225464
    }
  }
}
```

| Variant | Rank | Provision above Madde 3 | Article title (if present) | L2 |
|---|---:|---|---|---:|
| O1 | 1 | 5607_kacakcilikla_mucadele_kanunu/normal/16 | Tasfiye | 0.856337488 |
| O3 | 1 | 5607_kacakcilikla_mucadele_kanunu/normal/9 | Arama ve elkoyma | 0.450071305 |
| O3 | 2 | 5607_kacakcilikla_mucadele_kanunu/normal/12 | Yasak eşyanın geri gönderilmesi | 0.487526834 |
| O3 | 3 | 5607_kacakcilikla_mucadele_kanunu/normal/2 | Tanımlar | 0.505748391 |

### k5607-004

İhracat gerçekleşmediği hâlde gerçekleşmiş gibi gösterilmesi veya ihraç malının cins, miktar, evsaf ya da fiyatının değiştirilmesi hangi yaptırımla karşılanır; beyandaki fark yüzde onu aşmıyorsa hangi işlem uygulanır?
ALL recovered ranks (G0/O1/O2/O3): >50 / 2 / 2 / 2
First expected document ranks (G0/O2): >50 / 1

5607_kacakcilikla_mucadele_kanunu/normal/3: document competition supported: G0 censored, O1 <=10; enriched global source rank improves (historical G0 comparator)

Within-query distance evidence only; absolute L2 thresholds are not transferable across questions.
```json
{
  "O1": {
    "5607_kacakcilikla_mucadele_kanunu/normal/3": {
      "rank": 2,
      "top1_distance": 0.8865262269973755,
      "gold_distance": 0.9160258173942566,
      "gold_minus_top1": 0.029499590396881104
    }
  },
  "O3": {
    "5607_kacakcilikla_mucadele_kanunu/normal/3": {
      "rank": 2,
      "top1_distance": 0.42656123638153076,
      "gold_distance": 0.48798584938049316,
      "gold_minus_top1": 0.0614246129989624
    }
  }
}
```

| Variant | Rank | Provision above Madde 3 | Article title (if present) | L2 |
|---|---:|---|---|---:|
| O1 | 1 | 5607_kacakcilikla_mucadele_kanunu/normal/11 | Elkonulan eşyanın muhafazası | 0.886526227 |
| O3 | 1 | 5607_kacakcilikla_mucadele_kanunu/normal/2 | Tanımlar | 0.426561236 |

### k5607-014

Yabancı ülkeden gelen yasak eşya yükleme veya taşıma belgelerinde gösterilerek gümrüğe getirilmişse hangi güvenlik koşulları altında nereye gönderilebilir?
ALL recovered ranks (G0/O1/O2/O3): 1 / 1 / 1 / 1
First expected document ranks (G0/O2): 1 / 1

5607_kacakcilikla_mucadele_kanunu/normal/12: No rule triggered; inspect exact ranks
### k5607-017

Elkonulan ve teknik düzenlemelere uygun kaçak akaryakıtın hangi kurumlar tarafından, hangi yöntemlerle tasfiye edilmesi öngörülür?
ALL recovered ranks (G0/O1/O2/O3): 1 / 1 / 1 / 1
First expected document ranks (G0/O2): 1 / 1

5607_kacakcilikla_mucadele_kanunu/normal/16/a: No rule triggered; inspect exact ranks
### k5607-023

Kaçak şüphesiyle eşya yakalanması hâlinde muhbir ve elkoyma ikramiyesine hak kazananlara ödeme yapılmasının temel dayanağı nedir?
ALL recovered ranks (G0/O1/O2/O3): 1 / 1 / 26 / 26
First expected document ranks (G0/O2): 1 / 1

5607_kacakcilikla_mucadele_kanunu/normal/23: enrichment worsens within-document source rank
### k5607-025

Eşyayı gümrük işlemlerine tabi tutmaksızın ülkeye sokan kişi için Madde 3 fıkra 1'deki temel yaptırım nedir; aynı suç örgüt faaliyeti çerçevesinde işlenirse ve eşya toplum sağlığını tehdit edecek nitelikteyse Madde 4 fıkra 1 ve 7 hangi ek sonuçları, hangi koşulla öngörür?
ALL recovered ranks (G0/O1/O2/O3): >50 / 8 / 11 / 11
First expected document ranks (G0/O2): >50 / 1

5607_kacakcilikla_mucadele_kanunu/normal/4: document competition supported: G0 censored, O1 <=10; enriched global source rank improves (historical G0 comparator); enrichment worsens within-document source rank
5607_kacakcilikla_mucadele_kanunu/normal/3: document competition supported: G0 censored, O1 <=10; enriched global source rank improves (historical G0 comparator)

Within-query distance evidence only; absolute L2 thresholds are not transferable across questions.
```json
{
  "O1": {
    "5607_kacakcilikla_mucadele_kanunu/normal/3": {
      "rank": 4,
      "top1_distance": 0.8851954936981201,
      "gold_distance": 0.9181084632873535,
      "gold_minus_top1": 0.0329129695892334
    },
    "5607_kacakcilikla_mucadele_kanunu/normal/4": {
      "rank": 8,
      "top1_distance": 0.8851954936981201,
      "gold_distance": 0.9340206384658813,
      "gold_minus_top1": 0.04882514476776123
    }
  },
  "O3": {
    "5607_kacakcilikla_mucadele_kanunu/normal/3": {
      "rank": 4,
      "top1_distance": 0.47981420159339905,
      "gold_distance": 0.500498354434967,
      "gold_minus_top1": 0.020684152841567993
    },
    "5607_kacakcilikla_mucadele_kanunu/normal/4": {
      "rank": 11,
      "top1_distance": 0.47981420159339905,
      "gold_distance": 0.5357998013496399,
      "gold_minus_top1": 0.055985599756240845
    }
  }
}
```

### k5607-026

Eşyayı gümrük işlemlerine tabi tutmaksızın ülkeye sokmanın Madde 3 fıkra 1'deki temel yaptırımı nedir; Madde 5 kapsamında etkin pişmanlıkla ödeme yapılırsa ödeme tutarı, soruşturma ve kovuşturma evrelerindeki indirimler ve bu imkândan yararlanamayan hâller nelerdir?
ALL recovered ranks (G0/O1/O2/O3): >50 / 11 / 5 / 5
First expected document ranks (G0/O2): 45 / 1

5607_kacakcilikla_mucadele_kanunu/normal/3: within-document provision difficulty: O1 >10; enriched global source rank improves (historical G0 comparator); enrichment improves within-document source rank
5607_kacakcilikla_mucadele_kanunu/normal/5: document competition supported: G0 censored, O1 <=10; enriched global source rank improves (historical G0 comparator); enrichment improves within-document source rank

Within-query distance evidence only; absolute L2 thresholds are not transferable across questions.
```json
{
  "O1": {
    "5607_kacakcilikla_mucadele_kanunu/normal/3": {
      "rank": 11,
      "top1_distance": 0.8038181066513062,
      "gold_distance": 0.9236716032028198,
      "gold_minus_top1": 0.11985349655151367
    },
    "5607_kacakcilikla_mucadele_kanunu/normal/5": {
      "rank": 2,
      "top1_distance": 0.8038181066513062,
      "gold_distance": 0.8047069311141968,
      "gold_minus_top1": 0.000888824462890625
    }
  },
  "O3": {
    "5607_kacakcilikla_mucadele_kanunu/normal/3": {
      "rank": 5,
      "top1_distance": 0.4473201632499695,
      "gold_distance": 0.5233745574951172,
      "gold_minus_top1": 0.0760543942451477
    },
    "5607_kacakcilikla_mucadele_kanunu/normal/5": {
      "rank": 1,
      "top1_distance": 0.4473201632499695,
      "gold_distance": 0.4473201632499695,
      "gold_minus_top1": 0.0
    }
  }
}
```

### k5607-028

16/A ve 23 üncü maddelerde belirtilen yönetmeliklerin yürürlüğe konulması için Geçici Madde 7 hangi süreyi öngörür?
ALL recovered ranks (G0/O1/O2/O3): 1 / 1 / 1 / 1
First expected document ranks (G0/O2): 1 / 1

5607_kacakcilikla_mucadele_kanunu/gecici/7: No rule triggered; inspect exact ranks
### k5607-029

Madde 3 fıkra 2 hangi fiili ve yaptırımı düzenler; gümrük vergilerinin kısmen eksik ödenmesi nedeniyle açılmış kamu davalarında, Geçici Madde 10'un yürürlüğünden önce elkonulan ve müsadere kararı verilmemiş kara taşıtlarının iadesi için bu geçici hüküm hangi başvuru, ödeme ve tasfiye koşullarını arar?
ALL recovered ranks (G0/O1/O2/O3): >50 / 16 / 21 / 21
First expected document ranks (G0/O2): 1 / 1

5607_kacakcilikla_mucadele_kanunu/gecici/10: enriched global source rank improves (historical G0 comparator); enrichment improves within-document source rank
5607_kacakcilikla_mucadele_kanunu/normal/3: within-document provision difficulty: O1 >10; enriched global source rank improves (historical G0 comparator); enrichment worsens within-document source rank

Within-query distance evidence only; absolute L2 thresholds are not transferable across questions.
```json
{
  "O1": {
    "5607_kacakcilikla_mucadele_kanunu/gecici/10": {
      "rank": 2,
      "top1_distance": 0.6588823795318604,
      "gold_distance": 0.7043999433517456,
      "gold_minus_top1": 0.045517563819885254
    },
    "5607_kacakcilikla_mucadele_kanunu/normal/3": {
      "rank": 16,
      "top1_distance": 0.6588823795318604,
      "gold_distance": 1.0289409160614014,
      "gold_minus_top1": 0.370058536529541
    }
  },
  "O3": {
    "5607_kacakcilikla_mucadele_kanunu/gecici/10": {
      "rank": 1,
      "top1_distance": 0.34760910272598267,
      "gold_distance": 0.34760910272598267,
      "gold_minus_top1": 0.0
    },
    "5607_kacakcilikla_mucadele_kanunu/normal/3": {
      "rank": 21,
      "top1_distance": 0.34760910272598267,
      "gold_distance": 0.6215352416038513,
      "gold_minus_top1": 0.27392613887786865
    }
  }
}
```

### k5607-030

Madde 5 fıkra 2(b) uyarınca kovuşturma evresinde hangi ödeme karşılığında ne oranda ceza indirimi uygulanır; Geçici Madde 12 fıkra 1 bu imkânı hüküm verilmiş ve dosyası infaz aşamasındaki kişilere hangi ödeme ve geçici süre koşullarıyla tanır?
ALL recovered ranks (G0/O1/O2/O3): 2 / 2 / 7 / 7
First expected document ranks (G0/O2): 1 / 1

5607_kacakcilikla_mucadele_kanunu/gecici/12: No rule triggered; inspect exact ranks
5607_kacakcilikla_mucadele_kanunu/normal/5: enrichment worsens within-document source rank
## O2 versus saved G0: paired coverage changes

Counts are improved / unchanged / regressed for each question's boolean coverage flag. Full IDs are in JSON. This is a historical-comparator diagnostic, not a same-run production trial.

| Metric | K | Improved | Unchanged | Regressed |
|---|---:|---:|---:|---:|
| document_hit | 1 | 6 | 24 | 0 |
| document_hit | 3 | 5 | 25 | 0 |
| document_hit | 5 | 5 | 25 | 0 |
| document_hit | 10 | 5 | 25 | 0 |
| document_hit | 20 | 5 | 25 | 0 |
| document_hit | 50 | 4 | 26 | 0 |
| document_all | 1 | 6 | 24 | 0 |
| document_all | 3 | 5 | 25 | 0 |
| document_all | 5 | 5 | 25 | 0 |
| document_all | 10 | 5 | 25 | 0 |
| document_all | 20 | 5 | 25 | 0 |
| document_all | 50 | 4 | 26 | 0 |
| source_any | 1 | 3 | 23 | 4 |
| source_any | 3 | 4 | 21 | 5 |
| source_any | 5 | 5 | 21 | 4 |
| source_any | 10 | 5 | 23 | 2 |
| source_any | 20 | 5 | 24 | 1 |
| source_any | 50 | 5 | 25 | 0 |
| source_all | 1 | 1 | 26 | 3 |
| source_all | 3 | 2 | 20 | 8 |
| source_all | 5 | 4 | 20 | 6 |
| source_all | 10 | 4 | 23 | 3 |
| source_all | 20 | 5 | 23 | 2 |
| source_all | 50 | 6 | 24 | 0 |

## Exhaustive within-document rank distributions

First gold and ALL gold are separate for multi-source questions; count denominators appear through the ID lists in JSON.

| Variant | Group | Measure | 1 | 2–3 | 4–5 | 6–10 | 11–20 | 21–30 | 31–46 |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| O1 | all | first_expected_source_rank | 20 | 8 | 1 | 1 | 0 | 0 | 0 |
| O1 | all | all_expected_sources_recovered_by_rank | 17 | 9 | 0 | 2 | 2 | 0 | 0 |
| O1 | single_source | first_expected_source_rank | 17 | 6 | 0 | 1 | 0 | 0 | 0 |
| O1 | single_source | all_expected_sources_recovered_by_rank | 17 | 6 | 0 | 1 | 0 | 0 | 0 |
| O1 | multi_source | first_expected_source_rank | 3 | 2 | 1 | 0 | 0 | 0 | 0 |
| O1 | multi_source | all_expected_sources_recovered_by_rank | 0 | 3 | 0 | 1 | 2 | 0 | 0 |
| O3 | all | first_expected_source_rank | 18 | 5 | 3 | 2 | 1 | 1 | 0 |
| O3 | all | all_expected_sources_recovered_by_rank | 14 | 4 | 4 | 3 | 2 | 3 | 0 |
| O3 | single_source | first_expected_source_rank | 14 | 4 | 2 | 2 | 1 | 1 | 0 |
| O3 | single_source | all_expected_sources_recovered_by_rank | 14 | 4 | 2 | 2 | 1 | 1 | 0 |
| O3 | multi_source | first_expected_source_rank | 4 | 1 | 1 | 0 | 0 | 0 | 0 |
| O3 | multi_source | all_expected_sources_recovered_by_rank | 0 | 0 | 2 | 1 | 1 | 2 | 0 |

## O3 minus O1 rank deltas

Each required source is counted once per question. Repeated sources across different questions are distinct diagnostic instances. No censored global rank enters these calculations.
```json
{
  "unit": "question-required-source pair (repeated sources across questions remain separate)",
  "per_required_source": {
    "count": 36,
    "mean": 2.2222222222222223,
    "median": 0.0,
    "improved": 5,
    "unchanged": 19,
    "regressed": 12
  },
  "first_gold": {
    "count": 30,
    "mean": 1.7333333333333334,
    "median": 0.0,
    "improved": 4,
    "unchanged": 19,
    "regressed": 7
  },
  "all_gold": {
    "count": 30,
    "mean": 2.6666666666666665,
    "median": 0.0,
    "improved": 3,
    "unchanged": 16,
    "regressed": 11
  }
}
```

## Persistent six-question cohort recovery

Includes 002/003/004/025/026/029; excludes historical-drift 014. Lists show observed cutoff coverage, not deployable performance.
```json
{
  "G0": {
    "5": {
      "source_any": [
        "k5607-029"
      ],
      "source_all": []
    },
    "10": {
      "source_any": [
        "k5607-029"
      ],
      "source_all": []
    },
    "20": {
      "source_any": [
        "k5607-029"
      ],
      "source_all": []
    },
    "50": {
      "source_any": [
        "k5607-029"
      ],
      "source_all": []
    }
  },
  "O1": {
    "5": {
      "source_any": [
        "k5607-003",
        "k5607-004",
        "k5607-025",
        "k5607-026",
        "k5607-029"
      ],
      "source_all": [
        "k5607-003",
        "k5607-004"
      ]
    },
    "10": {
      "source_any": [
        "k5607-002",
        "k5607-003",
        "k5607-004",
        "k5607-025",
        "k5607-026",
        "k5607-029"
      ],
      "source_all": [
        "k5607-002",
        "k5607-003",
        "k5607-004",
        "k5607-025"
      ]
    },
    "20": {
      "source_any": [
        "k5607-002",
        "k5607-003",
        "k5607-004",
        "k5607-025",
        "k5607-026",
        "k5607-029"
      ],
      "source_all": [
        "k5607-002",
        "k5607-003",
        "k5607-004",
        "k5607-025",
        "k5607-026",
        "k5607-029"
      ]
    },
    "50": {
      "source_any": [
        "k5607-002",
        "k5607-003",
        "k5607-004",
        "k5607-025",
        "k5607-026",
        "k5607-029"
      ],
      "source_all": [
        "k5607-002",
        "k5607-003",
        "k5607-004",
        "k5607-025",
        "k5607-026",
        "k5607-029"
      ]
    }
  },
  "O2": {
    "5": {
      "source_any": [
        "k5607-002",
        "k5607-003",
        "k5607-004",
        "k5607-025",
        "k5607-026",
        "k5607-029"
      ],
      "source_all": [
        "k5607-002",
        "k5607-003",
        "k5607-004",
        "k5607-026"
      ]
    },
    "10": {
      "source_any": [
        "k5607-002",
        "k5607-003",
        "k5607-004",
        "k5607-025",
        "k5607-026",
        "k5607-029"
      ],
      "source_all": [
        "k5607-002",
        "k5607-003",
        "k5607-004",
        "k5607-026"
      ]
    },
    "20": {
      "source_any": [
        "k5607-002",
        "k5607-003",
        "k5607-004",
        "k5607-025",
        "k5607-026",
        "k5607-029"
      ],
      "source_all": [
        "k5607-002",
        "k5607-003",
        "k5607-004",
        "k5607-025",
        "k5607-026"
      ]
    },
    "50": {
      "source_any": [
        "k5607-002",
        "k5607-003",
        "k5607-004",
        "k5607-025",
        "k5607-026",
        "k5607-029"
      ],
      "source_all": [
        "k5607-002",
        "k5607-003",
        "k5607-004",
        "k5607-025",
        "k5607-026",
        "k5607-029"
      ]
    }
  },
  "O3": {
    "5": {
      "source_any": [
        "k5607-002",
        "k5607-003",
        "k5607-004",
        "k5607-025",
        "k5607-026",
        "k5607-029"
      ],
      "source_all": [
        "k5607-002",
        "k5607-003",
        "k5607-004",
        "k5607-026"
      ]
    },
    "10": {
      "source_any": [
        "k5607-002",
        "k5607-003",
        "k5607-004",
        "k5607-025",
        "k5607-026",
        "k5607-029"
      ],
      "source_all": [
        "k5607-002",
        "k5607-003",
        "k5607-004",
        "k5607-026"
      ]
    },
    "20": {
      "source_any": [
        "k5607-002",
        "k5607-003",
        "k5607-004",
        "k5607-025",
        "k5607-026",
        "k5607-029"
      ],
      "source_all": [
        "k5607-002",
        "k5607-003",
        "k5607-004",
        "k5607-025",
        "k5607-026"
      ]
    },
    "50": {
      "source_any": [
        "k5607-002",
        "k5607-003",
        "k5607-004",
        "k5607-025",
        "k5607-026",
        "k5607-029"
      ],
      "source_all": [
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

## Ten decision questions and single next experiment

1. k5607-002: raw oracle filtering recovers Madde 2 at rank 8/46, sufficient for Top10 but not Top5. O2/O3 place it at rank 2. Thus filtering supplies access, and title enrichment improves its early provision rank. This is consistent with, but does not rerun, M12F-A.

2. k5607-003/004: Madde 3 ranks 2/46 for BOTH under O1. Under O3 it ranks 4/46 for 003 and 2/46 for 004. G0 is censored beyond 50 for both. Strong within-law accessibility supports cross-document competition; these cases do not show fundamentally low Madde 3 rank inside 5607. Exact competing Articles and titles are reported above.

3. k5607-025: O1 Madde 3=4, Madde 4=8, ALL=8. O3 Madde 3=4, Madde 4=11, ALL=11. O2 has the same required-source ranks as O3. Enrichment worsens the second-source rank and loses ALL@10.

4. k5607-026: O1 Madde 3=11, Madde 5=2, ALL=11. O3 Madde 3=5, Madde 5=1, ALL=5. O2 has the same required-source ranks as O3. Enrichment helps this mixed document/provision-selection case.

5. k5607-029: G0 Gecici 10=4 and Madde 3>50. O1 Gecici 10=2, Madde 3=16, ALL=16. O2/O3 Gecici 10=1, Madde 3=21, ALL=21. The expected document already leads G0; provision selection remains a separate difficulty and enrichment worsens complete coverage.

6. Across the six persistent cases, O1 recovers ANY source in 5/6 at Top5 and 6/6 at Top10. ALL coverage becomes 2/6 at Top5, 4/6 at Top10 and 6/6 at Top20. G0 ALL coverage is 0/6 even at Top50. Among the five G0 complete misses specifically, O1 ANY recovers 4/5 at Top5 and 5/5 at Top10. These are oracle-access diagnostics, not production gains.

7. Of four O1 ALL@5 failures (002,025,026,029), O3 brings two (002,026) into Top5; 025 and 029 remain incomplete there. At Top10, O3 fixes 026 but regresses 025, leaving the cohort ALL count unchanged at 4/6. Across all 30 questions, O3 ALL@5 falls from O1 26/30 to 22/30. Required-source rank deltas are 5 improved / 19 unchanged / 12 regressed, mean +2.222 and median 0; enrichment is not a general fix.

8. Document discrimination is a major supported contributor, but it is not sufficient alone for complete early retrieval: only 2/6 primary cases are ALL-complete by O1 Top5. G0-to-O1 is a historical comparator with newly embedded raw vectors, so vector drift is not independently isolated. No fresh global baseline was run.

9. There is observed within-5607 provision-selection difficulty, especially Madde 3 rank 11 for 026 and rank 16 for 029, plus Madde 4 rank 8 for 025. Nevertheless all 36 required question-source pairs rank within O1 Top16, so the primary cohort does not support a blanket persistent low-rank Article/chunk defect. Chunk breadth causality remains unproven. Enrichment creates substantial regressions, including 006 Madde 3 from 1 to 8, 013 Madde 11 from 2 to 20, and control 023 Madde 23 from 1 to 26.

10. Recommend ONE development-only, question-text-based document-discrimination/routing experiment using the full three-law benchmark and ambiguity/cross-law controls, with no gold document available to the router. Most primary ALL failures are accessible within O1 Top10 (4/6), and all first gold sources are within Top8, so document discrimination is the dominant supported next target. Track composite provision coverage separately; do not adopt oracle filtering or universal title enrichment. A NEW UNSEEN HOLDOUT is mandatory before any future adoption.

Oracle-filter performance is a decomposition diagnostic, not deployable retrieval performance.
A NEW UNSEEN HOLDOUT is mandatory before any future adoption. No oracle filtering, routing, reranking or other candidate is adopted.
