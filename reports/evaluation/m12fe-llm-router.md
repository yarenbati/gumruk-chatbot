# M12F-E — LLM Question-Only Document Router Diagnostic

M12F-E READY FOR REVIEW — LLM ROUTER PROMISING

Phase A only: document classification. No Chroma, retrieval, production routing, prompt tuning, benchmark-label fitting or adoption.
A NEW UNSEEN HOLDOUT is mandatory before any future candidate adoption.

## Population and frozen prompt

105 exact M12D records: 5326=45, 4458=30, 5607=30; implicit=99, explicit=6.
Model: `gpt-5.6-terra`. Prompt/schema fingerprint: `aa5d6288db8b55b64a3b2759b0f9c200510ef118fe095411be58f25e04ade0b3`.

```text
You classify which available legal document most likely answers a user's question.

Available documents:
1. 5326_kabahatler_kanunu — general misdemeanour and administrative sanction framework.
2. 4458_gumruk_kanunu — customs procedures, duties, declarations, customs regimes and administration.
3. 5607_kacakcilikla_mucadele_kanunu — smuggling offences and anti-smuggling provisions.

Rank all three document IDs from most likely to least likely for the user's question.
Return only the requested structured object. Do not explain your ranking.

```

## API accounting

```json
{
  "model": "gpt-5.6-terra",
  "requests": 105,
  "successful_classifications": 105,
  "failures": 0,
  "input_tokens": 24373,
  "output_tokens": 10217,
  "total_tokens": 34590,
  "generation_calls": 0,
  "generation_calls_meaning": "0 downstream RAG answer-generation calls; the 105 LLM classification calls are counted separately in requests."
}
```

Network failures: []

## Router accuracy

| Group | N | Top1 | Top2 | Failures |
|---|---:|---:|---:|---:|
| all | 105 | 100 (95.24%) | 105 (100.00%) | 0 |
| implicit | 99 | 94 (94.95%) | 99 (100.00%) | 0 |
| explicit | 6 | 6 (100.00%) | 6 (100.00%) | 0 |

### Per-document accuracy

| True document | N | Top1 | Top2 |
|---|---:|---:|---:|
| 5326_kabahatler_kanunu | 45 | 44 | 45 |
| 4458_gumruk_kanunu | 30 | 29 | 30 |
| 5607_kacakcilikla_mucadele_kanunu | 30 | 27 | 30 |

### Top1 confusion matrix

| True / Predicted | 5326_kabahatler_kanunu | 4458_gumruk_kanunu | 5607_kacakcilikla_mucadele_kanunu |
|---|---:|---:|---:|
| 5326_kabahatler_kanunu | 44 | 0 | 1 |
| 4458_gumruk_kanunu | 1 | 29 | 0 |
| 5607_kacakcilikla_mucadele_kanunu | 0 | 3 | 27 |

Top1 error IDs: q040, gk028, k5607-010, k5607-014, k5607-028

## Saved-centroid comparison

```json
{
  "top1": {
    "both_correct": {
      "count": 85,
      "ids": [
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
        "q031",
        "q032",
        "q033",
        "q034",
        "q035",
        "q036",
        "q037",
        "q038",
        "q039",
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
        "gk023",
        "gk024",
        "gk025",
        "gk026",
        "gk027",
        "gk029",
        "gk030",
        "k5607-001",
        "k5607-006",
        "k5607-007",
        "k5607-009",
        "k5607-011",
        "k5607-012",
        "k5607-015",
        "k5607-016",
        "k5607-017",
        "k5607-018",
        "k5607-019",
        "k5607-020",
        "k5607-023",
        "k5607-024",
        "k5607-027",
        "k5607-030"
      ]
    },
    "llm_only": {
      "count": 15,
      "ids": [
        "q030",
        "q041",
        "gk020",
        "gk022",
        "k5607-002",
        "k5607-003",
        "k5607-004",
        "k5607-005",
        "k5607-008",
        "k5607-013",
        "k5607-021",
        "k5607-022",
        "k5607-025",
        "k5607-026",
        "k5607-029"
      ]
    },
    "centroid_only": {
      "count": 3,
      "ids": [
        "q040",
        "k5607-010",
        "k5607-028"
      ]
    },
    "both_wrong": {
      "count": 2,
      "ids": [
        "gk028",
        "k5607-014"
      ]
    }
  },
  "top2": {
    "both_correct": {
      "count": 102,
      "ids": [
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
        "k5607-002",
        "k5607-003",
        "k5607-004",
        "k5607-005",
        "k5607-006",
        "k5607-007",
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
        "k5607-025",
        "k5607-026",
        "k5607-027",
        "k5607-028",
        "k5607-029",
        "k5607-030"
      ]
    },
    "llm_only": {
      "count": 3,
      "ids": [
        "gk020",
        "gk028",
        "k5607-008"
      ]
    },
    "centroid_only": {
      "count": 0,
      "ids": []
    },
    "both_wrong": {
      "count": 0,
      "ids": []
    }
  },
  "reference": "Saved M12F-D predictions; centroid routing was not rerun."
}
```

## Six primary cases

| ID | LLM rank 1 | LLM rank 2 | LLM rank 3 | True rank |
|---|---|---|---|---:|
| k5607-002 | 5607_kacakcilikla_mucadele_kanunu | 4458_gumruk_kanunu | 5326_kabahatler_kanunu | 1 |
| k5607-003 | 5607_kacakcilikla_mucadele_kanunu | 4458_gumruk_kanunu | 5326_kabahatler_kanunu | 1 |
| k5607-004 | 5607_kacakcilikla_mucadele_kanunu | 4458_gumruk_kanunu | 5326_kabahatler_kanunu | 1 |
| k5607-025 | 5607_kacakcilikla_mucadele_kanunu | 4458_gumruk_kanunu | 5326_kabahatler_kanunu | 1 |
| k5607-026 | 5607_kacakcilikla_mucadele_kanunu | 4458_gumruk_kanunu | 5326_kabahatler_kanunu | 1 |
| k5607-029 | 5607_kacakcilikla_mucadele_kanunu | 4458_gumruk_kanunu | 5326_kabahatler_kanunu | 1 |

LLM classification is compared with saved M12F-D centroid predictions only; no retrieval, Chroma access, or B0 combination was performed.

Phase A is document classification only. No benchmark-label tuning, prompt adaptation, retrieval integration, production routing or adoption occurred. A NEW UNSEEN HOLDOUT remains mandatory before any future candidate adoption.

Next step: M12F-E2: run one development-only LLM-router retrieval integration diagnostic. Do not implement production routing or adopt a candidate before review and a NEW UNSEEN HOLDOUT.

No commit is part of this milestone.
