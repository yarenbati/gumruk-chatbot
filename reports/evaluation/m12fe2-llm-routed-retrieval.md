# M12F-E2 — LLM Router Retrieval Integration Diagnostic

M12F-E2 READY FOR REVIEW — ROUTED RETRIEVAL MIXED

Development-only evidence. Saved M12F-E predictions were reused; the LLM router was not called again. This is the final M12F routing integration experiment.

## Population and accounting

```json
{
  "population": {
    "count": 105,
    "composition": {
      "5326": 45,
      "4458": 30,
      "5607": 30
    },
    "implicit": 99,
    "explicit": 6,
    "full_records_identical": true
  },
  "saved_router": {
    "path": "reports\\evaluation\\m12fe-llm-router.json",
    "status": "completed",
    "top1": 100,
    "top2": 105,
    "5607_top1": 27,
    "valid_predictions": 105
  },
  "api": {
    "unique_embedding_inputs": 105,
    "requests": 1,
    "successful_embeddings": 105,
    "failures": 0,
    "prompt_tokens": 5205,
    "total_tokens": 5205,
    "generation_calls": 0,
    "router_calls": 0,
    "accounting_scope": "successful embedding batch; initial sandbox failure is recorded separately in network_recovery"
  },
  "query_operations": {
    "R1": 105,
    "R2": 105,
    "total_fresh_retrieval_queries": 210
  }
}
```

B0 is saved historical M12F-B raw/global evidence. R1 and R2 are fresh copy-only retrieval. This is not a same-run causal comparison.

## Metrics

| Variant | Metric | @1 | @3 | @5 |
|---|---|---:|---:|---:|
| B0 | source_any | 66.67% | 80.95% | 87.62% |
| B0 | source_all | 56.19% | 77.14% | 82.86% |
| B0 | document_hit | 91.43% | 93.33% | 93.33% |
| B0 | document_all | 91.43% | 93.33% | 93.33% |
| B0 | document_intrusion | 8.57% | 15.24% | 17.33% |
| R1 | source_any | 65.71% | 81.90% | 88.57% |
| R1 | source_all | 54.29% | 75.24% | 80.95% |
| R1 | document_hit | 95.24% | 95.24% | 95.24% |
| R1 | document_all | 95.24% | 95.24% | 95.24% |
| R1 | document_intrusion | 4.76% | 4.76% | 4.76% |
| R2 | source_any | 66.67% | 80.95% | 87.62% |
| R2 | source_all | 56.19% | 77.14% | 82.86% |
| R2 | document_hit | 91.43% | 93.33% | 93.33% |
| R2 | document_all | 91.43% | 93.33% | 93.33% |
| R2 | document_intrusion | 8.57% | 13.97% | 15.62% |

## Paired changes against B0 at @5

```json
{
  "R1": {
    "source_any": {
      "5": {
        "improved": {
          "count": 5,
          "ids": [
            "gk020",
            "k5607-003",
            "k5607-004",
            "k5607-025",
            "k5607-026"
          ]
        },
        "unchanged": {
          "count": 96,
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
            "gk028",
            "gk029",
            "gk030",
            "k5607-001",
            "k5607-002",
            "k5607-005",
            "k5607-006",
            "k5607-007",
            "k5607-008",
            "k5607-009",
            "k5607-011",
            "k5607-012",
            "k5607-013",
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
            "k5607-029",
            "k5607-030"
          ]
        },
        "regressed": {
          "count": 4,
          "ids": [
            "q040",
            "k5607-010",
            "k5607-014",
            "k5607-028"
          ]
        }
      }
    },
    "source_all": {
      "5": {
        "improved": {
          "count": 2,
          "ids": [
            "k5607-003",
            "k5607-004"
          ]
        },
        "unchanged": {
          "count": 99,
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
            "gk020",
            "gk021",
            "gk022",
            "gk023",
            "gk024",
            "gk025",
            "gk026",
            "gk027",
            "gk028",
            "gk029",
            "gk030",
            "k5607-001",
            "k5607-002",
            "k5607-005",
            "k5607-006",
            "k5607-007",
            "k5607-008",
            "k5607-009",
            "k5607-011",
            "k5607-012",
            "k5607-013",
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
            "k5607-029",
            "k5607-030"
          ]
        },
        "regressed": {
          "count": 4,
          "ids": [
            "q040",
            "k5607-010",
            "k5607-014",
            "k5607-028"
          ]
        }
      }
    },
    "document_hit": {
      "5": {
        "improved": {
          "count": 6,
          "ids": [
            "gk020",
            "k5607-002",
            "k5607-003",
            "k5607-004",
            "k5607-025",
            "k5607-026"
          ]
        },
        "unchanged": {
          "count": 95,
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
            "gk028",
            "gk029",
            "gk030",
            "k5607-001",
            "k5607-005",
            "k5607-006",
            "k5607-007",
            "k5607-008",
            "k5607-009",
            "k5607-011",
            "k5607-012",
            "k5607-013",
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
            "k5607-029",
            "k5607-030"
          ]
        },
        "regressed": {
          "count": 4,
          "ids": [
            "q040",
            "k5607-010",
            "k5607-014",
            "k5607-028"
          ]
        }
      }
    }
  },
  "R2": {
    "source_any": {
      "5": {
        "improved": {
          "count": 0,
          "ids": []
        },
        "unchanged": {
          "count": 105,
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
            "gk020",
            "gk021",
            "gk022",
            "gk023",
            "gk024",
            "gk025",
            "gk026",
            "gk027",
            "gk028",
            "gk029",
            "gk030",
            "k5607-001",
            "k5607-002",
            "k5607-003",
            "k5607-004",
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
            "k5607-025",
            "k5607-026",
            "k5607-027",
            "k5607-028",
            "k5607-029",
            "k5607-030"
          ]
        },
        "regressed": {
          "count": 0,
          "ids": []
        }
      }
    },
    "source_all": {
      "5": {
        "improved": {
          "count": 0,
          "ids": []
        },
        "unchanged": {
          "count": 105,
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
            "gk020",
            "gk021",
            "gk022",
            "gk023",
            "gk024",
            "gk025",
            "gk026",
            "gk027",
            "gk028",
            "gk029",
            "gk030",
            "k5607-001",
            "k5607-002",
            "k5607-003",
            "k5607-004",
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
            "k5607-025",
            "k5607-026",
            "k5607-027",
            "k5607-028",
            "k5607-029",
            "k5607-030"
          ]
        },
        "regressed": {
          "count": 0,
          "ids": []
        }
      }
    },
    "document_hit": {
      "5": {
        "improved": {
          "count": 0,
          "ids": []
        },
        "unchanged": {
          "count": 105,
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
            "gk020",
            "gk021",
            "gk022",
            "gk023",
            "gk024",
            "gk025",
            "gk026",
            "gk027",
            "gk028",
            "gk029",
            "gk030",
            "k5607-001",
            "k5607-002",
            "k5607-003",
            "k5607-004",
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
            "k5607-025",
            "k5607-026",
            "k5607-027",
            "k5607-028",
            "k5607-029",
            "k5607-030"
          ]
        },
        "regressed": {
          "count": 0,
          "ids": []
        }
      }
    }
  }
}
```

## Five saved LLM Top1 routing errors

- `q040`: true=5326_kabahatler_kanunu; Top1=5607_kacakcilikla_mucadele_kanunu; Top2=5326_kabahatler_kanunu; classification=A hard-route regression; B R2 safety recovery; B0 ANY/ALL=True/True; R1=False/False; R2=True/True
- `gk028`: true=4458_gumruk_kanunu; Top1=5326_kabahatler_kanunu; Top2=4458_gumruk_kanunu; classification=C B0 was already wrong; D no retrieval impact; B0 ANY/ALL=False/False; R1=False/False; R2=False/False
- `k5607-010`: true=5607_kacakcilikla_mucadele_kanunu; Top1=4458_gumruk_kanunu; Top2=5607_kacakcilikla_mucadele_kanunu; classification=A hard-route regression; B R2 safety recovery; B0 ANY/ALL=True/True; R1=False/False; R2=True/True
- `k5607-014`: true=5607_kacakcilikla_mucadele_kanunu; Top1=4458_gumruk_kanunu; Top2=5607_kacakcilikla_mucadele_kanunu; classification=A hard-route regression; B R2 safety recovery; B0 ANY/ALL=True/True; R1=False/False; R2=True/True
- `k5607-028`: true=5607_kacakcilikla_mucadele_kanunu; Top1=4458_gumruk_kanunu; Top2=5607_kacakcilikla_mucadele_kanunu; classification=A hard-route regression; B R2 safety recovery; B0 ANY/ALL=True/True; R1=False/False; R2=True/True

## Six primary cases

```json
{
  "k5607-002": {
    "saved_router_ranking": [
      "5607_kacakcilikla_mucadele_kanunu",
      "4458_gumruk_kanunu",
      "5326_kabahatler_kanunu"
    ],
    "expected_sources": [
      "5607_kacakcilikla_mucadele_kanunu/normal/2"
    ],
    "variants": {
      "B0": {
        "top5": [
          {
            "rank": 1,
            "chunk_id": "4458-madde-25-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/25",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.6854152083396912,
            "text_sha256": "e1b47c2f8f3460ae37f416177764e51ee1d0e906334538b8cab68f6b4e546231"
          },
          {
            "rank": 2,
            "chunk_id": "4458-madde-235-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/235",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.6929594278335571,
            "text_sha256": "213865796a89430ab83594a46796680280c3abf376f2d67f95145cffe89d736f"
          },
          {
            "rank": 3,
            "chunk_id": "4458-madde-126-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/126",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.6960080862045288,
            "text_sha256": "80b450a8f295c1aef84e4eebdb6c68b09beb7e6b6bdb6305ff7fec635f1e3d86"
          },
          {
            "rank": 4,
            "chunk_id": "4458-madde-143-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/143",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7030948400497437,
            "text_sha256": "2c6f56f015ccc43feaef5df2cf0ccafa8643f3f5efccc16f730ae0fa2fa6fd7c"
          },
          {
            "rank": 5,
            "chunk_id": "4458-madde-26-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/26",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7031776905059814,
            "text_sha256": "116deb0a2fb7f92ab665138b97ea2ee0877605d7bc9173503e47c5fcf26c0851"
          },
          {
            "rank": 6,
            "chunk_id": "4458-madde-66-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/66",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7071590423583984,
            "text_sha256": "f34357f7f6b72c7b54d45526da612d54d5c7bd8fb7593ec88e07033e39ef3219"
          },
          {
            "rank": 7,
            "chunk_id": "4458-madde-170-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/170",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7131003141403198,
            "text_sha256": "84d746251b0734b8df5d1f8cee01f2e72ec479f41bf223a0ca7e0926c25302d2"
          },
          {
            "rank": 8,
            "chunk_id": "4458-madde-142-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/142",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7234158515930176,
            "text_sha256": "19b62607aead911d140ccfabcd3bb9262f766f5a28f09d25f9612c83cbfbfee6"
          },
          {
            "rank": 9,
            "chunk_id": "4458-madde-112-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/112",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7294674515724182,
            "text_sha256": "30586318732f6c5edb26b7cd444673b534262630352dd0fe9a58a8d6c4d28c1e"
          },
          {
            "rank": 10,
            "chunk_id": "4458-madde-104-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/104",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7303980588912964,
            "text_sha256": "e9a58ada897fa772c20beacb3716a7d400cb85cb29a7075364f3e2c4e0fa9dcb"
          },
          {
            "rank": 11,
            "chunk_id": "4458-madde-187-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/187",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7339699268341064,
            "text_sha256": "ac19779e0b0a8698de3154b8185addd38dc7dec8718cc71c4898600ea4d0a421"
          },
          {
            "rank": 12,
            "chunk_id": "4458-madde-114-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/114",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.734917402267456,
            "text_sha256": "dafc86b5bd51aa3c62b40c256d0eb05c2dd21469bd755fba030bc2a0de007bf6"
          },
          {
            "rank": 13,
            "chunk_id": "4458-madde-134-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/134",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7365504503250122,
            "text_sha256": "d66ea0c5f8bd03455dcf9026bb5e47819634362b7aad1ec0c4166490f0495149"
          },
          {
            "rank": 14,
            "chunk_id": "4458-madde-147-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/147",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7428013682365417,
            "text_sha256": "4bae7ea36ef355f969d86e9df21654a3ade53660bd7ee19c7e01bfcc60aa5ee2"
          },
          {
            "rank": 15,
            "chunk_id": "4458-madde-186-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/186",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7438778877258301,
            "text_sha256": "e3fe527a9838aab7f48017e5b2d0455b1e056e80b7ba7e4b6abf6a486d9dcc93"
          },
          {
            "rank": 16,
            "chunk_id": "4458-madde-27-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/27",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7441431283950806,
            "text_sha256": "990518d695526594b7035a349d9dc76f009c86958c78994f68d0f78c8f353fc8"
          },
          {
            "rank": 17,
            "chunk_id": "4458-madde-236-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/236",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7460622787475586,
            "text_sha256": "78c72e0aada272a95b02f7371e2961ef4b87e2cc2e9e9fc716267e72dd51b0b1"
          },
          {
            "rank": 18,
            "chunk_id": "4458-madde-24-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/24",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7491934299468994,
            "text_sha256": "a581f8cf6d3ed8c790d5b1d9e55c27dd025faa70ff1c4245a8609fa7ca5ec896"
          },
          {
            "rank": 19,
            "chunk_id": "4458-madde-213-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/213",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7503290176391602,
            "text_sha256": "07b0c22643fba773a2e6a13cda4159f6eb60e9d5d3b83ba0cc76b8e6f69524d5"
          },
          {
            "rank": 20,
            "chunk_id": "4458-madde-167-chunk-002",
            "document_source_key": "4458_gumruk_kanunu/normal/167",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7503724098205566,
            "text_sha256": "01b1bcbb6b8b930c5c17ef9ce25bdf94a21949385a5d60884b5a9e15ee79c54a"
          },
          {
            "rank": 21,
            "chunk_id": "4458-madde-179-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/179",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7528224587440491,
            "text_sha256": "bc331011ecbe6309c7cd58845d830f9f350fb7c1ea1b5dfcf5fbc7763c02e600"
          },
          {
            "rank": 22,
            "chunk_id": "4458-madde-169-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/169",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.756109893321991,
            "text_sha256": "0377131965a3ecc90c43c7f99c5470a02230a4a5ea71323d1f027acc364eb2bc"
          },
          {
            "rank": 23,
            "chunk_id": "4458-madde-3-chunk-002",
            "document_source_key": "4458_gumruk_kanunu/normal/3",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7574849128723145,
            "text_sha256": "973b710311504667dfaa608539d428c1d91d8bd0d45746fadbabe915c4a6c3e9"
          },
          {
            "rank": 24,
            "chunk_id": "4458-madde-81-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/81",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7597872018814087,
            "text_sha256": "9218dfe5c0f31b0318830fc485f161d88e07974cdf0a011d9e4250c1ad6b66b6"
          },
          {
            "rank": 25,
            "chunk_id": "4458-madde-151-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/151",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7647268176078796,
            "text_sha256": "e9fa5a58199e997b9164f71ae686bfb0620e21661934104b820c7ab021821b18"
          },
          {
            "rank": 26,
            "chunk_id": "4458-madde-178-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/178",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7674880027770996,
            "text_sha256": "62ef3b0914448aa84482d47a9047f95e3c333958b363fd1a0fb770a1ec3706b7"
          },
          {
            "rank": 27,
            "chunk_id": "4458-madde-146-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/146",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7681129574775696,
            "text_sha256": "94fe7bda47e76a66fa420e4895c14ca2021b9d86191c1aa9117d14d2ac43cedc"
          },
          {
            "rank": 28,
            "chunk_id": "4458-madde-31-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/31",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7686959505081177,
            "text_sha256": "67635c8c54d0fa0fca7b45b6b3826912502187654668792fa7f460e332c01b33"
          },
          {
            "rank": 29,
            "chunk_id": "4458-madde-70-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/70",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7700673341751099,
            "text_sha256": "a73524ff022af42b9cbf3a9e30f98cc1448e7e214a792263a4b3b7e1ecd38918"
          },
          {
            "rank": 30,
            "chunk_id": "4458-madde-109-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/109",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7711082696914673,
            "text_sha256": "eb5784df32a2a8e76dbc63bb38b5556a71cc145e52256565ecdefe1183ba5aa7"
          },
          {
            "rank": 31,
            "chunk_id": "4458-madde-50-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/50",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7718481421470642,
            "text_sha256": "d936c9628a66e0fa24b15a3a798c51a959ecb21e83dd5344eba8a49579d7b6f0"
          },
          {
            "rank": 32,
            "chunk_id": "4458-madde-53-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/53",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.775989294052124,
            "text_sha256": "65b36f75c0807147b8304c8bba487a2316f7d0fed24f9cf875626e284a395aa6"
          },
          {
            "rank": 33,
            "chunk_id": "4458-madde-57-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/57",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7777732014656067,
            "text_sha256": "18c922e91ab00293fe677615d7b3633ad90572cae297c50e00f525f930e39a91"
          },
          {
            "rank": 34,
            "chunk_id": "4458-madde-28-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/28",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7790650129318237,
            "text_sha256": "dca3e2782a138529fabca24001576a0a3d2580ee77e881a1ee51e00df317e42d"
          },
          {
            "rank": 35,
            "chunk_id": "4458-madde-98-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/98",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.779629111289978,
            "text_sha256": "37ecc16981a38cc2f6e2cba6a038b9220c177481c2cf11347db42271009c54bb"
          },
          {
            "rank": 36,
            "chunk_id": "4458-madde-68-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/68",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7809100151062012,
            "text_sha256": "9b066ed6cc6604e7b2a732831eb5060c2b32296d490fd8027f97c9cd7660b447"
          },
          {
            "rank": 37,
            "chunk_id": "4458-madde-121-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/121",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7816195487976074,
            "text_sha256": "ee64169d05a4d28df8b00f0376239ebc5348828b3906e01ec54fc024b42816c0"
          },
          {
            "rank": 38,
            "chunk_id": "4458-madde-191-a-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/191/a",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7832909822463989,
            "text_sha256": "ab7d790ce48109954acd5d9ffd0467a299a2c2a12e264b7976f7899c6cd7f25b"
          },
          {
            "rank": 39,
            "chunk_id": "4458-madde-49-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/49",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7835521101951599,
            "text_sha256": "18b92217295f7b1c0f473286e2a825c1890dd809a28cb4a1977d6ef9682943ce"
          },
          {
            "rank": 40,
            "chunk_id": "4458-madde-138-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/138",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7886452078819275,
            "text_sha256": "48ccb8df8a8340cab00727de46266513a2537370906f150df3e1ed481941f582"
          },
          {
            "rank": 41,
            "chunk_id": "4458-madde-136-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/136",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7895179986953735,
            "text_sha256": "9687f1b028e578aec89c62b54b1cf9cf7a8c7f80141e88ec676c9d4d2b1c3bd3"
          },
          {
            "rank": 42,
            "chunk_id": "4458-madde-184-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/184",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7896071672439575,
            "text_sha256": "b3d1087f7e6073bef285131bc0629f0a5c4319faefd2679e64f77da09f721a66"
          },
          {
            "rank": 43,
            "chunk_id": "4458-madde-167-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/167",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7923667430877686,
            "text_sha256": "6c00702ccc75bb880861db66a8102287c6281d967c7e80d65d34b54076c1d085"
          },
          {
            "rank": 44,
            "chunk_id": "4458-madde-118-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/118",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7924633026123047,
            "text_sha256": "d3a1b317cf1a8e3cac9fb6f9553b3fc1674292f618db8edc7cf22a935d7de953"
          },
          {
            "rank": 45,
            "chunk_id": "4458-madde-231-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/231",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7925221920013428,
            "text_sha256": "4e666bd26164d40838e7b097190218b89fb9d7f89447acce71a609015021489f"
          },
          {
            "rank": 46,
            "chunk_id": "4458-madde-183-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/183",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7938379049301147,
            "text_sha256": "8cb93cf9d1cf1a30b34d5382a83e5b6d29ad3e330845791361848c59672193b9"
          },
          {
            "rank": 47,
            "chunk_id": "4458-madde-18-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/18",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7943662405014038,
            "text_sha256": "a6ae314e7fd5849d3dc5f7b9de81829a09714be4ee1557294e2d49b450636850"
          },
          {
            "rank": 48,
            "chunk_id": "4458-madde-196-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/196",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7944458723068237,
            "text_sha256": "65e846b089a26fbcabbd7c23ec4246128ebd808ab8f91adcc87707cfe454b7c5"
          },
          {
            "rank": 49,
            "chunk_id": "4458-madde-75-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/75",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7946560382843018,
            "text_sha256": "53ef510c2c22196627340b9c18652cfc57c07d806a4cae5b927c4bcc7c06e79a"
          },
          {
            "rank": 50,
            "chunk_id": "4458-madde-78-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/78",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.794853687286377,
            "text_sha256": "fadb2ea3fc56acf010a5e4ef765bdb57b4342c77328f7fdfeaf53dcb0e704f51"
          }
        ],
        "source_ranks": {
          "5607_kacakcilikla_mucadele_kanunu/normal/2": null
        }
      },
      "R1": {
        "top5": [
          {
            "rank": 1,
            "chunk_id": "5607-madde-15-chunk-001",
            "document_source_key": "5607_kacakcilikla_mucadele_kanunu/normal/15",
            "document_id": "5607_kacakcilikla_mucadele_kanunu",
            "legislation_number": "5607",
            "distance": 0.7659544944763184,
            "text_sha256": "aa7adcb533e16d31c9a5cfaedbe9e2d6332edb2d2ce11bc531c5ca9dc0892142"
          },
          {
            "rank": 2,
            "chunk_id": "5607-madde-16-chunk-001",
            "document_source_key": "5607_kacakcilikla_mucadele_kanunu/normal/16",
            "document_id": "5607_kacakcilikla_mucadele_kanunu",
            "legislation_number": "5607",
            "distance": 0.815157949924469,
            "text_sha256": "cd89e500280c2222df0e9175e834ce403e6ad3bffed289e5b83a3d4122332df2"
          },
          {
            "rank": 3,
            "chunk_id": "5607-madde-11-chunk-001",
            "document_source_key": "5607_kacakcilikla_mucadele_kanunu/normal/11",
            "document_id": "5607_kacakcilikla_mucadele_kanunu",
            "legislation_number": "5607",
            "distance": 0.8677492737770081,
            "text_sha256": "2cae2606436a95ca99d39dd80a894ed05b96bfba834d08c15383ffce3cf7e502"
          },
          {
            "rank": 4,
            "chunk_id": "5607-gecici-madde-6-chunk-001",
            "document_source_key": "5607_kacakcilikla_mucadele_kanunu/gecici/6",
            "document_id": "5607_kacakcilikla_mucadele_kanunu",
            "legislation_number": "5607",
            "distance": 0.8826892375946045,
            "text_sha256": "bc5e3d98ebec7a0955e0ace18107734bdff3774a4937214e3dea700360cecdea"
          },
          {
            "rank": 5,
            "chunk_id": "5607-madde-23-chunk-001",
            "document_source_key": "5607_kacakcilikla_mucadele_kanunu/normal/23",
            "document_id": "5607_kacakcilikla_mucadele_kanunu",
            "legislation_number": "5607",
            "distance": 0.893948495388031,
            "text_sha256": "49b08bc0cd9cdf38b9c030aee4da03cb7d1e7bcf4c553ce8088556434d781e89"
          }
        ],
        "source_ranks": {
          "5607_kacakcilikla_mucadele_kanunu/normal/2": null
        }
      },
      "R2": {
        "top5": [
          {
            "rank": 1,
            "chunk_id": "4458-madde-25-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/25",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.6854152083396912,
            "text_sha256": "e1b47c2f8f3460ae37f416177764e51ee1d0e906334538b8cab68f6b4e546231"
          },
          {
            "rank": 2,
            "chunk_id": "4458-madde-235-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/235",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.6929594278335571,
            "text_sha256": "213865796a89430ab83594a46796680280c3abf376f2d67f95145cffe89d736f"
          },
          {
            "rank": 3,
            "chunk_id": "4458-madde-126-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/126",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.6960080862045288,
            "text_sha256": "80b450a8f295c1aef84e4eebdb6c68b09beb7e6b6bdb6305ff7fec635f1e3d86"
          },
          {
            "rank": 4,
            "chunk_id": "4458-madde-143-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/143",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7030948400497437,
            "text_sha256": "2c6f56f015ccc43feaef5df2cf0ccafa8643f3f5efccc16f730ae0fa2fa6fd7c"
          },
          {
            "rank": 5,
            "chunk_id": "4458-madde-26-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/26",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7031776905059814,
            "text_sha256": "116deb0a2fb7f92ab665138b97ea2ee0877605d7bc9173503e47c5fcf26c0851"
          }
        ],
        "source_ranks": {
          "5607_kacakcilikla_mucadele_kanunu/normal/2": null
        }
      }
    }
  },
  "k5607-003": {
    "saved_router_ranking": [
      "5607_kacakcilikla_mucadele_kanunu",
      "4458_gumruk_kanunu",
      "5326_kabahatler_kanunu"
    ],
    "expected_sources": [
      "5607_kacakcilikla_mucadele_kanunu/normal/3"
    ],
    "variants": {
      "B0": {
        "top5": [
          {
            "rank": 1,
            "chunk_id": "4458-madde-236-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/236",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.6469547152519226,
            "text_sha256": "78c72e0aada272a95b02f7371e2961ef4b87e2cc2e9e9fc716267e72dd51b0b1"
          },
          {
            "rank": 2,
            "chunk_id": "4458-madde-235-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/235",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.6534733772277832,
            "text_sha256": "213865796a89430ab83594a46796680280c3abf376f2d67f95145cffe89d736f"
          },
          {
            "rank": 3,
            "chunk_id": "4458-madde-239-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/239",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.6786705851554871,
            "text_sha256": "1655e8c95b3744d061913995cb3bb4bca0e96460022f1b282c42f2b395f95a49"
          },
          {
            "rank": 4,
            "chunk_id": "4458-madde-57-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/57",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.6951010823249817,
            "text_sha256": "18c922e91ab00293fe677615d7b3633ad90572cae297c50e00f525f930e39a91"
          },
          {
            "rank": 5,
            "chunk_id": "4458-madde-186-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/186",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7066694498062134,
            "text_sha256": "e3fe527a9838aab7f48017e5b2d0455b1e056e80b7ba7e4b6abf6a486d9dcc93"
          },
          {
            "rank": 6,
            "chunk_id": "4458-madde-104-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/104",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7084269523620605,
            "text_sha256": "e9a58ada897fa772c20beacb3716a7d400cb85cb29a7075364f3e2c4e0fa9dcb"
          },
          {
            "rank": 7,
            "chunk_id": "4458-madde-78-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/78",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7138091325759888,
            "text_sha256": "fadb2ea3fc56acf010a5e4ef765bdb57b4342c77328f7fdfeaf53dcb0e704f51"
          },
          {
            "rank": 8,
            "chunk_id": "4458-madde-183-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/183",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.718228280544281,
            "text_sha256": "8cb93cf9d1cf1a30b34d5382a83e5b6d29ad3e330845791361848c59672193b9"
          },
          {
            "rank": 9,
            "chunk_id": "4458-madde-182-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/182",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7209732532501221,
            "text_sha256": "aed3c33afb987589b28db2747f4c485ff638ca1e9e0517bc44301dac04111ccd"
          },
          {
            "rank": 10,
            "chunk_id": "4458-madde-237-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/237",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7236261963844299,
            "text_sha256": "95841409e5913c2f8e8ffe25ae704623b06bdd77d6aac7296ccf60cdb893eeb6"
          },
          {
            "rank": 11,
            "chunk_id": "4458-madde-234-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/234",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7342581748962402,
            "text_sha256": "ff3755e8a5a182b2b228d9fbe57fae63eab24a72b2bbf3922780d28073285b48"
          },
          {
            "rank": 12,
            "chunk_id": "4458-madde-235-chunk-002",
            "document_source_key": "4458_gumruk_kanunu/normal/235",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7438059449195862,
            "text_sha256": "cb7a33090f14cfccf41acae04f50bd838d2424c46c23ca289d2cdf6814516ab2"
          },
          {
            "rank": 13,
            "chunk_id": "4458-madde-190-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/190",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7482181787490845,
            "text_sha256": "d07a8d2795fefccc524fd7cf098659cb17c29061f2088bd623a8175f3b43c2a9"
          },
          {
            "rank": 14,
            "chunk_id": "4458-madde-213-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/213",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7494335174560547,
            "text_sha256": "07b0c22643fba773a2e6a13cda4159f6eb60e9d5d3b83ba0cc76b8e6f69524d5"
          },
          {
            "rank": 15,
            "chunk_id": "4458-madde-68-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/68",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7504598498344421,
            "text_sha256": "9b066ed6cc6604e7b2a732831eb5060c2b32296d490fd8027f97c9cd7660b447"
          },
          {
            "rank": 16,
            "chunk_id": "4458-madde-241-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/241",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7504637241363525,
            "text_sha256": "bba8b06b0bcfd5e6dc1cb8d5b45386982f41b73a527af707b90e8b6f8ce75f56"
          },
          {
            "rank": 17,
            "chunk_id": "4458-madde-198-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/198",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7563658952713013,
            "text_sha256": "f15f08608f0cfbdc9f45216c8ae55b4d5be2504b9780a837892881f573f1a7d9"
          },
          {
            "rank": 18,
            "chunk_id": "4458-madde-69-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/69",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7599844932556152,
            "text_sha256": "2ce38d9daae86455b62d1fff4175f8f57fd9ce4bb952b333db74380506d8e480"
          },
          {
            "rank": 19,
            "chunk_id": "4458-madde-194-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/194",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7707250714302063,
            "text_sha256": "fd4dfb9affd8823bbef6eb4db0c794f92d08d0e66911d7cf925f1d386cbc1726"
          },
          {
            "rank": 20,
            "chunk_id": "4458-madde-158-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/158",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7776032090187073,
            "text_sha256": "b9cca99069c8c8493456f6f3416d00b70650220d91528975f954e699ef7d664b"
          },
          {
            "rank": 21,
            "chunk_id": "4458-madde-161-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/161",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7789422869682312,
            "text_sha256": "563d60293b9f5c5e4500255e9487906dc77896ae74cc71a9417e2ac64aea23ad"
          },
          {
            "rank": 22,
            "chunk_id": "4458-madde-70-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/70",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7833093404769897,
            "text_sha256": "a73524ff022af42b9cbf3a9e30f98cc1448e7e214a792263a4b3b7e1ecd38918"
          },
          {
            "rank": 23,
            "chunk_id": "4458-madde-160-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/160",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7837361097335815,
            "text_sha256": "640a5986b4d4745e689d4502041102731c0d479d8df1c39500df1ff33192a896"
          },
          {
            "rank": 24,
            "chunk_id": "4458-madde-179-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/179",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7861557006835938,
            "text_sha256": "bc331011ecbe6309c7cd58845d830f9f350fb7c1ea1b5dfcf5fbc7763c02e600"
          },
          {
            "rank": 25,
            "chunk_id": "4458-madde-241-chunk-002",
            "document_source_key": "4458_gumruk_kanunu/normal/241",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7880465388298035,
            "text_sha256": "b5db2fcac8afd9e79072555aa3633ef3d695451cf664e3faaf418c35bc0365ed"
          },
          {
            "rank": 26,
            "chunk_id": "4458-madde-167-chunk-002",
            "document_source_key": "4458_gumruk_kanunu/normal/167",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7885671854019165,
            "text_sha256": "01b1bcbb6b8b930c5c17ef9ce25bdf94a21949385a5d60884b5a9e15ee79c54a"
          },
          {
            "rank": 27,
            "chunk_id": "4458-madde-184-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/184",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7889164686203003,
            "text_sha256": "b3d1087f7e6073bef285131bc0629f0a5c4319faefd2679e64f77da09f721a66"
          },
          {
            "rank": 28,
            "chunk_id": "4458-madde-189-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/189",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7905686497688293,
            "text_sha256": "1717c4727a5f0c6ca11d8f2b05a131597628cc460c5a95e50dcd57976a9ac841"
          },
          {
            "rank": 29,
            "chunk_id": "4458-madde-168-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/168",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7921364307403564,
            "text_sha256": "f7c88896c10f6add4014291ae8d7a01708d7045614ccdf9c63e93d83172a8421"
          },
          {
            "rank": 30,
            "chunk_id": "4458-madde-32-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/32",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7929840087890625,
            "text_sha256": "99e007bae1f07c3074d9c4225a4865ef54194a36841e7ca47cad3b6ec47fb7dd"
          },
          {
            "rank": 31,
            "chunk_id": "4458-madde-121-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/121",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8036689162254333,
            "text_sha256": "ee64169d05a4d28df8b00f0376239ebc5348828b3906e01ec54fc024b42816c0"
          },
          {
            "rank": 32,
            "chunk_id": "4458-madde-86-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/86",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8038572669029236,
            "text_sha256": "81b507804988f0b1afa4c43566c08c3d8c5e817a6a6d5e35adec983b78ec0681"
          },
          {
            "rank": 33,
            "chunk_id": "4458-madde-76-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/76",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.805802047252655,
            "text_sha256": "593110c352977dfbae512674b344cb88ce94cac606efa813d1bfc3e6c1a00d8f"
          },
          {
            "rank": 34,
            "chunk_id": "4458-madde-155-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/155",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8101338744163513,
            "text_sha256": "effc7ec246235a9973ecb097d1fc2b9ec177911a6382505a85e4e91c4bf9e5c4"
          },
          {
            "rank": 35,
            "chunk_id": "4458-madde-109-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/109",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8102109432220459,
            "text_sha256": "eb5784df32a2a8e76dbc63bb38b5556a71cc145e52256565ecdefe1183ba5aa7"
          },
          {
            "rank": 36,
            "chunk_id": "4458-madde-66-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/66",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8102532625198364,
            "text_sha256": "f34357f7f6b72c7b54d45526da612d54d5c7bd8fb7593ec88e07033e39ef3219"
          },
          {
            "rank": 37,
            "chunk_id": "4458-madde-157-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/157",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8102730512619019,
            "text_sha256": "a452a52dabb3f1110b0dbbf0f8da0250fc742bf4374f0e978bd09bb7d321418c"
          },
          {
            "rank": 38,
            "chunk_id": "4458-madde-74-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/74",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8130459785461426,
            "text_sha256": "b68f8d28a49e11700b3622871ee3be7cedfb1fc69c7dcf267e0c475eac1f69ec"
          },
          {
            "rank": 39,
            "chunk_id": "4458-madde-56-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/56",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8142735958099365,
            "text_sha256": "1970d2a90e3d279cd1baf5d6ad7c580ed5f79aa4b0e6b5a79457b6378d032b6c"
          },
          {
            "rank": 40,
            "chunk_id": "4458-madde-64-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/64",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8142881989479065,
            "text_sha256": "96061a42c17de53d80d8d71d7c51573254d9740ad57ea59f6a9c13090a77b1d6"
          },
          {
            "rank": 41,
            "chunk_id": "4458-madde-55-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/55",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.81615149974823,
            "text_sha256": "04bd1b02bb853ee4dbc0a2cd06571b8bee25aa95ee6eed68dbda2fa17f1e69d2"
          },
          {
            "rank": 42,
            "chunk_id": "4458-madde-37-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/37",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8166339993476868,
            "text_sha256": "c8b6d358b4aed4de85d0ab322752a526ce58d46777a44024ec602c8517fd451c"
          },
          {
            "rank": 43,
            "chunk_id": "4458-madde-45-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/45",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8176570534706116,
            "text_sha256": "fcc906763fb47a4b19df2783d344a397f048ff57fc086a789d5fa6975968caa9"
          },
          {
            "rank": 44,
            "chunk_id": "4458-madde-15-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/15",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.818510115146637,
            "text_sha256": "f7b767cfa271a7247665b973d058830d288c1e48c792475a0b6daf8348553a91"
          },
          {
            "rank": 45,
            "chunk_id": "4458-madde-165-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/165",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.820340096950531,
            "text_sha256": "6a3b1cbcae2759d557b57e6b4243dc7c3c3295cf48f714e53ffc61aba8c2fddd"
          },
          {
            "rank": 46,
            "chunk_id": "4458-madde-53-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/53",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8209415674209595,
            "text_sha256": "65b36f75c0807147b8304c8bba487a2316f7d0fed24f9cf875626e284a395aa6"
          },
          {
            "rank": 47,
            "chunk_id": "4458-madde-24-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/24",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8211522698402405,
            "text_sha256": "a581f8cf6d3ed8c790d5b1d9e55c27dd025faa70ff1c4245a8609fa7ca5ec896"
          },
          {
            "rank": 48,
            "chunk_id": "4458-madde-106-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/106",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8212041854858398,
            "text_sha256": "9dc00186c3eed441536755db19473d47049de673a02a82fb14d636af915d582d"
          },
          {
            "rank": 49,
            "chunk_id": "4458-madde-238-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/238",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.82171231508255,
            "text_sha256": "c11239d87c965fa951cb6c2dde9eeb9fb3bde5c6dec3dad38e4abcd05a80cfb5"
          },
          {
            "rank": 50,
            "chunk_id": "4458-madde-100-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/100",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8257532715797424,
            "text_sha256": "5d1c6ba4a80ca93fdbe00d45d75d9157f71ecf01570fef09de976bdfa95b8588"
          }
        ],
        "source_ranks": {
          "5607_kacakcilikla_mucadele_kanunu/normal/3": null
        }
      },
      "R1": {
        "top5": [
          {
            "rank": 1,
            "chunk_id": "5607-madde-16-chunk-001",
            "document_source_key": "5607_kacakcilikla_mucadele_kanunu/normal/16",
            "document_id": "5607_kacakcilikla_mucadele_kanunu",
            "legislation_number": "5607",
            "distance": 0.8563992977142334,
            "text_sha256": "cd89e500280c2222df0e9175e834ce403e6ad3bffed289e5b83a3d4122332df2"
          },
          {
            "rank": 2,
            "chunk_id": "5607-madde-12-chunk-001",
            "document_source_key": "5607_kacakcilikla_mucadele_kanunu/normal/12",
            "document_id": "5607_kacakcilikla_mucadele_kanunu",
            "legislation_number": "5607",
            "distance": 0.9057561159133911,
            "text_sha256": "fe1567d7bc58f192bd2831e1666e3e9397a56364e0779cab27ae624717c93519"
          },
          {
            "rank": 3,
            "chunk_id": "5607-madde-11-chunk-001",
            "document_source_key": "5607_kacakcilikla_mucadele_kanunu/normal/11",
            "document_id": "5607_kacakcilikla_mucadele_kanunu",
            "legislation_number": "5607",
            "distance": 0.9302463531494141,
            "text_sha256": "2cae2606436a95ca99d39dd80a894ed05b96bfba834d08c15383ffce3cf7e502"
          },
          {
            "rank": 4,
            "chunk_id": "5607-madde-3-chunk-003",
            "document_source_key": "5607_kacakcilikla_mucadele_kanunu/normal/3",
            "document_id": "5607_kacakcilikla_mucadele_kanunu",
            "legislation_number": "5607",
            "distance": 0.9337289333343506,
            "text_sha256": "29ac962782279460023c82284c4a74c366f8d9f06c75762b1e86896d92a7d3a1"
          },
          {
            "rank": 5,
            "chunk_id": "5607-gecici-madde-6-chunk-001",
            "document_source_key": "5607_kacakcilikla_mucadele_kanunu/gecici/6",
            "document_id": "5607_kacakcilikla_mucadele_kanunu",
            "legislation_number": "5607",
            "distance": 0.9700812101364136,
            "text_sha256": "bc5e3d98ebec7a0955e0ace18107734bdff3774a4937214e3dea700360cecdea"
          }
        ],
        "source_ranks": {
          "5607_kacakcilikla_mucadele_kanunu/normal/3": 4
        }
      },
      "R2": {
        "top5": [
          {
            "rank": 1,
            "chunk_id": "4458-madde-236-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/236",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.6469547152519226,
            "text_sha256": "78c72e0aada272a95b02f7371e2961ef4b87e2cc2e9e9fc716267e72dd51b0b1"
          },
          {
            "rank": 2,
            "chunk_id": "4458-madde-235-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/235",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.6534733772277832,
            "text_sha256": "213865796a89430ab83594a46796680280c3abf376f2d67f95145cffe89d736f"
          },
          {
            "rank": 3,
            "chunk_id": "4458-madde-239-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/239",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.6786705851554871,
            "text_sha256": "1655e8c95b3744d061913995cb3bb4bca0e96460022f1b282c42f2b395f95a49"
          },
          {
            "rank": 4,
            "chunk_id": "4458-madde-57-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/57",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.6951010823249817,
            "text_sha256": "18c922e91ab00293fe677615d7b3633ad90572cae297c50e00f525f930e39a91"
          },
          {
            "rank": 5,
            "chunk_id": "4458-madde-186-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/186",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7066694498062134,
            "text_sha256": "e3fe527a9838aab7f48017e5b2d0455b1e056e80b7ba7e4b6abf6a486d9dcc93"
          }
        ],
        "source_ranks": {
          "5607_kacakcilikla_mucadele_kanunu/normal/3": null
        }
      }
    }
  },
  "k5607-004": {
    "saved_router_ranking": [
      "5607_kacakcilikla_mucadele_kanunu",
      "4458_gumruk_kanunu",
      "5326_kabahatler_kanunu"
    ],
    "expected_sources": [
      "5607_kacakcilikla_mucadele_kanunu/normal/3"
    ],
    "variants": {
      "B0": {
        "top5": [
          {
            "rank": 1,
            "chunk_id": "4458-madde-141-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/141",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.6974372267723083,
            "text_sha256": "7be7cddfe924b43ade030a0ec0ae6cbe56d0844a10b90000bb2cc721eeda0089"
          },
          {
            "rank": 2,
            "chunk_id": "4458-madde-179-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/179",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7061578631401062,
            "text_sha256": "bc331011ecbe6309c7cd58845d830f9f350fb7c1ea1b5dfcf5fbc7763c02e600"
          },
          {
            "rank": 3,
            "chunk_id": "4458-madde-27-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/27",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7153065204620361,
            "text_sha256": "990518d695526594b7035a349d9dc76f009c86958c78994f68d0f78c8f353fc8"
          },
          {
            "rank": 4,
            "chunk_id": "4458-madde-25-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/25",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7179021239280701,
            "text_sha256": "e1b47c2f8f3460ae37f416177764e51ee1d0e906334538b8cab68f6b4e546231"
          },
          {
            "rank": 5,
            "chunk_id": "4458-madde-24-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/24",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7180213928222656,
            "text_sha256": "a581f8cf6d3ed8c790d5b1d9e55c27dd025faa70ff1c4245a8609fa7ca5ec896"
          },
          {
            "rank": 6,
            "chunk_id": "4458-madde-115-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/115",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7217462062835693,
            "text_sha256": "9ac15fe9a811ac02c887c90eebcd859ab799aa9e506c572efd15953e59c69e5f"
          },
          {
            "rank": 7,
            "chunk_id": "4458-madde-194-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/194",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7438966035842896,
            "text_sha256": "fd4dfb9affd8823bbef6eb4db0c794f92d08d0e66911d7cf925f1d386cbc1726"
          },
          {
            "rank": 8,
            "chunk_id": "4458-madde-109-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/109",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7518044710159302,
            "text_sha256": "eb5784df32a2a8e76dbc63bb38b5556a71cc145e52256565ecdefe1183ba5aa7"
          },
          {
            "rank": 9,
            "chunk_id": "4458-madde-234-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/234",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7524265050888062,
            "text_sha256": "ff3755e8a5a182b2b228d9fbe57fae63eab24a72b2bbf3922780d28073285b48"
          },
          {
            "rank": 10,
            "chunk_id": "4458-madde-235-chunk-002",
            "document_source_key": "4458_gumruk_kanunu/normal/235",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.758293628692627,
            "text_sha256": "cb7a33090f14cfccf41acae04f50bd838d2424c46c23ca289d2cdf6814516ab2"
          },
          {
            "rank": 11,
            "chunk_id": "4458-madde-235-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/235",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7671573162078857,
            "text_sha256": "213865796a89430ab83594a46796680280c3abf376f2d67f95145cffe89d736f"
          },
          {
            "rank": 12,
            "chunk_id": "4458-madde-170-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/170",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7709939479827881,
            "text_sha256": "84d746251b0734b8df5d1f8cee01f2e72ec479f41bf223a0ca7e0926c25302d2"
          },
          {
            "rank": 13,
            "chunk_id": "4458-madde-143-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/143",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7712118029594421,
            "text_sha256": "2c6f56f015ccc43feaef5df2cf0ccafa8643f3f5efccc16f730ae0fa2fa6fd7c"
          },
          {
            "rank": 14,
            "chunk_id": "4458-madde-236-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/236",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7725679278373718,
            "text_sha256": "78c72e0aada272a95b02f7371e2961ef4b87e2cc2e9e9fc716267e72dd51b0b1"
          },
          {
            "rank": 15,
            "chunk_id": "4458-madde-28-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/28",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7733908891677856,
            "text_sha256": "dca3e2782a138529fabca24001576a0a3d2580ee77e881a1ee51e00df317e42d"
          },
          {
            "rank": 16,
            "chunk_id": "4458-madde-121-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/121",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7737614512443542,
            "text_sha256": "ee64169d05a4d28df8b00f0376239ebc5348828b3906e01ec54fc024b42816c0"
          },
          {
            "rank": 17,
            "chunk_id": "4458-madde-56-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/56",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7780480980873108,
            "text_sha256": "1970d2a90e3d279cd1baf5d6ad7c580ed5f79aa4b0e6b5a79457b6378d032b6c"
          },
          {
            "rank": 18,
            "chunk_id": "4458-madde-108-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/108",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7790812849998474,
            "text_sha256": "ad8850727256076e58443ab6862b2c73abfbe176e57c467206a4bd273ba3d02f"
          },
          {
            "rank": 19,
            "chunk_id": "4458-madde-144-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/144",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7808010578155518,
            "text_sha256": "3860fc221ae005bd93dea91d8cf2b8a7208bb514071af3aeb25d75df0940c31b"
          },
          {
            "rank": 20,
            "chunk_id": "4458-madde-119-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/119",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7839323878288269,
            "text_sha256": "231327143c8cf59a550a40f705c6a0375fbdfcb7d36445badae3e006a468b001"
          },
          {
            "rank": 21,
            "chunk_id": "4458-madde-26-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/26",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7880538702011108,
            "text_sha256": "116deb0a2fb7f92ab665138b97ea2ee0877605d7bc9173503e47c5fcf26c0851"
          },
          {
            "rank": 22,
            "chunk_id": "4458-madde-145-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/145",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7944885492324829,
            "text_sha256": "58b9cb4836b4bcf0cdeaac8c9a78e8ce6877fa7ced7d5bdbdcf044d2c6d4a6a0"
          },
          {
            "rank": 23,
            "chunk_id": "4458-madde-241-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/241",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8062215447425842,
            "text_sha256": "bba8b06b0bcfd5e6dc1cb8d5b45386982f41b73a527af707b90e8b6f8ce75f56"
          },
          {
            "rank": 24,
            "chunk_id": "4458-madde-184-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/184",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8068921566009521,
            "text_sha256": "b3d1087f7e6073bef285131bc0629f0a5c4319faefd2679e64f77da09f721a66"
          },
          {
            "rank": 25,
            "chunk_id": "4458-madde-136-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/136",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8082342147827148,
            "text_sha256": "9687f1b028e578aec89c62b54b1cf9cf7a8c7f80141e88ec676c9d4d2b1c3bd3"
          },
          {
            "rank": 26,
            "chunk_id": "4458-madde-167-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/167",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8091531991958618,
            "text_sha256": "6c00702ccc75bb880861db66a8102287c6281d967c7e80d65d34b54076c1d085"
          },
          {
            "rank": 27,
            "chunk_id": "4458-madde-137-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/137",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8141677975654602,
            "text_sha256": "188e0b573603321ae382d168b59d28d7299dfce817414a6e074412079f3d1965"
          },
          {
            "rank": 28,
            "chunk_id": "4458-madde-140-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/140",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8151986598968506,
            "text_sha256": "06483b66a483cf6b6ed7c49e8af135342f3bfd707b16cbdac47d36ce4f2c67fe"
          },
          {
            "rank": 29,
            "chunk_id": "4458-madde-198-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/198",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8166621327400208,
            "text_sha256": "f15f08608f0cfbdc9f45216c8ae55b4d5be2504b9780a837892881f573f1a7d9"
          },
          {
            "rank": 30,
            "chunk_id": "4458-madde-127-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/127",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8257452249526978,
            "text_sha256": "101e6f0349501b6b875b920fb2dbd96108eb19e54356d91fef1d0456c3354282"
          },
          {
            "rank": 31,
            "chunk_id": "4458-madde-213-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/213",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8270138502120972,
            "text_sha256": "07b0c22643fba773a2e6a13cda4159f6eb60e9d5d3b83ba0cc76b8e6f69524d5"
          },
          {
            "rank": 32,
            "chunk_id": "4458-madde-116-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/116",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.827657163143158,
            "text_sha256": "fd2b3f311dd9a55a663fdcd2a1cb5e15c9d7b30636094d93a01da6f99a5fd110"
          },
          {
            "rank": 33,
            "chunk_id": "4458-madde-76-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/76",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.832042932510376,
            "text_sha256": "593110c352977dfbae512674b344cb88ce94cac606efa813d1bfc3e6c1a00d8f"
          },
          {
            "rank": 34,
            "chunk_id": "4458-madde-186-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/186",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8353276252746582,
            "text_sha256": "e3fe527a9838aab7f48017e5b2d0455b1e056e80b7ba7e4b6abf6a486d9dcc93"
          },
          {
            "rank": 35,
            "chunk_id": "4458-madde-138-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/138",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8360418081283569,
            "text_sha256": "48ccb8df8a8340cab00727de46266513a2537370906f150df3e1ed481941f582"
          },
          {
            "rank": 36,
            "chunk_id": "4458-madde-169-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/169",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8399671912193298,
            "text_sha256": "0377131965a3ecc90c43c7f99c5470a02230a4a5ea71323d1f027acc364eb2bc"
          },
          {
            "rank": 37,
            "chunk_id": "4458-madde-147-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/147",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8407486081123352,
            "text_sha256": "4bae7ea36ef355f969d86e9df21654a3ade53660bd7ee19c7e01bfcc60aa5ee2"
          },
          {
            "rank": 38,
            "chunk_id": "4458-madde-167-chunk-002",
            "document_source_key": "4458_gumruk_kanunu/normal/167",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8410712480545044,
            "text_sha256": "01b1bcbb6b8b930c5c17ef9ce25bdf94a21949385a5d60884b5a9e15ee79c54a"
          },
          {
            "rank": 39,
            "chunk_id": "4458-madde-57-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/57",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8421941995620728,
            "text_sha256": "18c922e91ab00293fe677615d7b3633ad90572cae297c50e00f525f930e39a91"
          },
          {
            "rank": 40,
            "chunk_id": "4458-madde-135-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/135",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8467262983322144,
            "text_sha256": "dd7e33d840d19445fecad9d326a112bd084fa3919e0c3c4c7be93d200b10afdb"
          },
          {
            "rank": 41,
            "chunk_id": "4458-madde-142-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/142",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8475433588027954,
            "text_sha256": "19b62607aead911d140ccfabcd3bb9262f766f5a28f09d25f9612c83cbfbfee6"
          },
          {
            "rank": 42,
            "chunk_id": "4458-madde-191-a-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/191/a",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8476588726043701,
            "text_sha256": "ab7d790ce48109954acd5d9ffd0467a299a2c2a12e264b7976f7899c6cd7f25b"
          },
          {
            "rank": 43,
            "chunk_id": "4458-madde-150-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/150",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8517282009124756,
            "text_sha256": "ccc3e92f2bf54358be6d9780b4df4670f10e253472acf772522eab543732f58f"
          },
          {
            "rank": 44,
            "chunk_id": "4458-madde-114-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/114",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.852142333984375,
            "text_sha256": "dafc86b5bd51aa3c62b40c256d0eb05c2dd21469bd755fba030bc2a0de007bf6"
          },
          {
            "rank": 45,
            "chunk_id": "4458-madde-237-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/237",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8539339900016785,
            "text_sha256": "95841409e5913c2f8e8ffe25ae704623b06bdd77d6aac7296ccf60cdb893eeb6"
          },
          {
            "rank": 46,
            "chunk_id": "4458-madde-111-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/111",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8547743558883667,
            "text_sha256": "0c2ca7bc49d470e107f9ec7c728095e9fa8ac4b90b6993ce554d6071c4ae0b15"
          },
          {
            "rank": 47,
            "chunk_id": "4458-madde-104-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/104",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8578263521194458,
            "text_sha256": "e9a58ada897fa772c20beacb3716a7d400cb85cb29a7075364f3e2c4e0fa9dcb"
          },
          {
            "rank": 48,
            "chunk_id": "4458-madde-112-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/112",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8602581024169922,
            "text_sha256": "30586318732f6c5edb26b7cd444673b534262630352dd0fe9a58a8d6c4d28c1e"
          },
          {
            "rank": 49,
            "chunk_id": "4458-madde-130-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/130",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8608056306838989,
            "text_sha256": "0620a2748e9a70d615495f2081c1217621e4d13e45d6ec66b9778162969a386c"
          },
          {
            "rank": 50,
            "chunk_id": "4458-madde-146-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/146",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8612039685249329,
            "text_sha256": "94fe7bda47e76a66fa420e4895c14ca2021b9d86191c1aa9117d14d2ac43cedc"
          }
        ],
        "source_ranks": {
          "5607_kacakcilikla_mucadele_kanunu/normal/3": null
        }
      },
      "R1": {
        "top5": [
          {
            "rank": 1,
            "chunk_id": "5607-madde-11-chunk-001",
            "document_source_key": "5607_kacakcilikla_mucadele_kanunu/normal/11",
            "document_id": "5607_kacakcilikla_mucadele_kanunu",
            "legislation_number": "5607",
            "distance": 0.8856533169746399,
            "text_sha256": "2cae2606436a95ca99d39dd80a894ed05b96bfba834d08c15383ffce3cf7e502"
          },
          {
            "rank": 2,
            "chunk_id": "5607-madde-3-chunk-002",
            "document_source_key": "5607_kacakcilikla_mucadele_kanunu/normal/3",
            "document_id": "5607_kacakcilikla_mucadele_kanunu",
            "legislation_number": "5607",
            "distance": 0.9152269959449768,
            "text_sha256": "5ae95f4124004857325d86b56390f21fa942597393e4499e35c1a562d3c38eee"
          },
          {
            "rank": 3,
            "chunk_id": "5607-madde-23-chunk-001",
            "document_source_key": "5607_kacakcilikla_mucadele_kanunu/normal/23",
            "document_id": "5607_kacakcilikla_mucadele_kanunu",
            "legislation_number": "5607",
            "distance": 0.9333060383796692,
            "text_sha256": "49b08bc0cd9cdf38b9c030aee4da03cb7d1e7bcf4c553ce8088556434d781e89"
          },
          {
            "rank": 4,
            "chunk_id": "5607-madde-16-chunk-001",
            "document_source_key": "5607_kacakcilikla_mucadele_kanunu/normal/16",
            "document_id": "5607_kacakcilikla_mucadele_kanunu",
            "legislation_number": "5607",
            "distance": 0.9586359262466431,
            "text_sha256": "cd89e500280c2222df0e9175e834ce403e6ad3bffed289e5b83a3d4122332df2"
          },
          {
            "rank": 5,
            "chunk_id": "5607-madde-16-a-chunk-001",
            "document_source_key": "5607_kacakcilikla_mucadele_kanunu/normal/16/a",
            "document_id": "5607_kacakcilikla_mucadele_kanunu",
            "legislation_number": "5607",
            "distance": 0.9847835302352905,
            "text_sha256": "a91fdc5b14cb3122a78e4ccdd8bf36d2525b97ecfe44cf4194cb8987b75772a4"
          }
        ],
        "source_ranks": {
          "5607_kacakcilikla_mucadele_kanunu/normal/3": 2
        }
      },
      "R2": {
        "top5": [
          {
            "rank": 1,
            "chunk_id": "4458-madde-141-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/141",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.6974372267723083,
            "text_sha256": "7be7cddfe924b43ade030a0ec0ae6cbe56d0844a10b90000bb2cc721eeda0089"
          },
          {
            "rank": 2,
            "chunk_id": "4458-madde-179-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/179",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7061578631401062,
            "text_sha256": "bc331011ecbe6309c7cd58845d830f9f350fb7c1ea1b5dfcf5fbc7763c02e600"
          },
          {
            "rank": 3,
            "chunk_id": "4458-madde-27-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/27",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7153065204620361,
            "text_sha256": "990518d695526594b7035a349d9dc76f009c86958c78994f68d0f78c8f353fc8"
          },
          {
            "rank": 4,
            "chunk_id": "4458-madde-25-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/25",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7179021239280701,
            "text_sha256": "e1b47c2f8f3460ae37f416177764e51ee1d0e906334538b8cab68f6b4e546231"
          },
          {
            "rank": 5,
            "chunk_id": "4458-madde-24-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/24",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7180213928222656,
            "text_sha256": "a581f8cf6d3ed8c790d5b1d9e55c27dd025faa70ff1c4245a8609fa7ca5ec896"
          }
        ],
        "source_ranks": {
          "5607_kacakcilikla_mucadele_kanunu/normal/3": null
        }
      }
    }
  },
  "k5607-025": {
    "saved_router_ranking": [
      "5607_kacakcilikla_mucadele_kanunu",
      "4458_gumruk_kanunu",
      "5326_kabahatler_kanunu"
    ],
    "expected_sources": [
      "5607_kacakcilikla_mucadele_kanunu/normal/3",
      "5607_kacakcilikla_mucadele_kanunu/normal/4"
    ],
    "variants": {
      "B0": {
        "top5": [
          {
            "rank": 1,
            "chunk_id": "4458-madde-57-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/57",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7140333652496338,
            "text_sha256": "18c922e91ab00293fe677615d7b3633ad90572cae297c50e00f525f930e39a91"
          },
          {
            "rank": 2,
            "chunk_id": "4458-madde-167-chunk-002",
            "document_source_key": "4458_gumruk_kanunu/normal/167",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7439285516738892,
            "text_sha256": "01b1bcbb6b8b930c5c17ef9ce25bdf94a21949385a5d60884b5a9e15ee79c54a"
          },
          {
            "rank": 3,
            "chunk_id": "4458-madde-235-chunk-002",
            "document_source_key": "4458_gumruk_kanunu/normal/235",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7467989921569824,
            "text_sha256": "cb7a33090f14cfccf41acae04f50bd838d2424c46c23ca289d2cdf6814516ab2"
          },
          {
            "rank": 4,
            "chunk_id": "4458-madde-235-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/235",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7605505585670471,
            "text_sha256": "213865796a89430ab83594a46796680280c3abf376f2d67f95145cffe89d736f"
          },
          {
            "rank": 5,
            "chunk_id": "4458-madde-236-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/236",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7738392949104309,
            "text_sha256": "78c72e0aada272a95b02f7371e2961ef4b87e2cc2e9e9fc716267e72dd51b0b1"
          },
          {
            "rank": 6,
            "chunk_id": "4458-madde-234-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/234",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.79083251953125,
            "text_sha256": "ff3755e8a5a182b2b228d9fbe57fae63eab24a72b2bbf3922780d28073285b48"
          },
          {
            "rank": 7,
            "chunk_id": "4458-madde-237-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/237",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7925285696983337,
            "text_sha256": "95841409e5913c2f8e8ffe25ae704623b06bdd77d6aac7296ccf60cdb893eeb6"
          },
          {
            "rank": 8,
            "chunk_id": "4458-madde-194-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/194",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7944939136505127,
            "text_sha256": "fd4dfb9affd8823bbef6eb4db0c794f92d08d0e66911d7cf925f1d386cbc1726"
          },
          {
            "rank": 9,
            "chunk_id": "4458-madde-24-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/24",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8020157217979431,
            "text_sha256": "a581f8cf6d3ed8c790d5b1d9e55c27dd025faa70ff1c4245a8609fa7ca5ec896"
          },
          {
            "rank": 10,
            "chunk_id": "4458-madde-183-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/183",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8071574568748474,
            "text_sha256": "8cb93cf9d1cf1a30b34d5382a83e5b6d29ad3e330845791361848c59672193b9"
          },
          {
            "rank": 11,
            "chunk_id": "4458-madde-241-chunk-002",
            "document_source_key": "4458_gumruk_kanunu/normal/241",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8098306655883789,
            "text_sha256": "b5db2fcac8afd9e79072555aa3633ef3d695451cf664e3faaf418c35bc0365ed"
          },
          {
            "rank": 12,
            "chunk_id": "4458-madde-27-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/27",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8099942207336426,
            "text_sha256": "990518d695526594b7035a349d9dc76f009c86958c78994f68d0f78c8f353fc8"
          },
          {
            "rank": 13,
            "chunk_id": "4458-madde-186-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/186",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8114867806434631,
            "text_sha256": "e3fe527a9838aab7f48017e5b2d0455b1e056e80b7ba7e4b6abf6a486d9dcc93"
          },
          {
            "rank": 14,
            "chunk_id": "4458-madde-178-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/178",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8133876919746399,
            "text_sha256": "62ef3b0914448aa84482d47a9047f95e3c333958b363fd1a0fb770a1ec3706b7"
          },
          {
            "rank": 15,
            "chunk_id": "4458-madde-239-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/239",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8164423108100891,
            "text_sha256": "1655e8c95b3744d061913995cb3bb4bca0e96460022f1b282c42f2b395f95a49"
          },
          {
            "rank": 16,
            "chunk_id": "4458-madde-18-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/18",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8196426630020142,
            "text_sha256": "a6ae314e7fd5849d3dc5f7b9de81829a09714be4ee1557294e2d49b450636850"
          },
          {
            "rank": 17,
            "chunk_id": "4458-madde-238-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/238",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8200492858886719,
            "text_sha256": "c11239d87c965fa951cb6c2dde9eeb9fb3bde5c6dec3dad38e4abcd05a80cfb5"
          },
          {
            "rank": 18,
            "chunk_id": "4458-madde-184-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/184",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8201295137405396,
            "text_sha256": "b3d1087f7e6073bef285131bc0629f0a5c4319faefd2679e64f77da09f721a66"
          },
          {
            "rank": 19,
            "chunk_id": "4458-madde-167-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/167",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.829082190990448,
            "text_sha256": "6c00702ccc75bb880861db66a8102287c6281d967c7e80d65d34b54076c1d085"
          },
          {
            "rank": 20,
            "chunk_id": "4458-madde-187-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/187",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8299627304077148,
            "text_sha256": "ac19779e0b0a8698de3154b8185addd38dc7dec8718cc71c4898600ea4d0a421"
          },
          {
            "rank": 21,
            "chunk_id": "4458-madde-25-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/25",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8333121538162231,
            "text_sha256": "e1b47c2f8f3460ae37f416177764e51ee1d0e906334538b8cab68f6b4e546231"
          },
          {
            "rank": 22,
            "chunk_id": "4458-madde-104-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/104",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8355416059494019,
            "text_sha256": "e9a58ada897fa772c20beacb3716a7d400cb85cb29a7075364f3e2c4e0fa9dcb"
          },
          {
            "rank": 23,
            "chunk_id": "4458-madde-115-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/115",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8364173769950867,
            "text_sha256": "9ac15fe9a811ac02c887c90eebcd859ab799aa9e506c572efd15953e59c69e5f"
          },
          {
            "rank": 24,
            "chunk_id": "4458-madde-53-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/53",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.836685061454773,
            "text_sha256": "65b36f75c0807147b8304c8bba487a2316f7d0fed24f9cf875626e284a395aa6"
          },
          {
            "rank": 25,
            "chunk_id": "4458-madde-213-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/213",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8385792374610901,
            "text_sha256": "07b0c22643fba773a2e6a13cda4159f6eb60e9d5d3b83ba0cc76b8e6f69524d5"
          },
          {
            "rank": 26,
            "chunk_id": "4458-madde-179-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/179",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8409925699234009,
            "text_sha256": "bc331011ecbe6309c7cd58845d830f9f350fb7c1ea1b5dfcf5fbc7763c02e600"
          },
          {
            "rank": 27,
            "chunk_id": "4458-madde-28-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/28",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8429021835327148,
            "text_sha256": "dca3e2782a138529fabca24001576a0a3d2580ee77e881a1ee51e00df317e42d"
          },
          {
            "rank": 28,
            "chunk_id": "4458-madde-78-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/78",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8449737429618835,
            "text_sha256": "fadb2ea3fc56acf010a5e4ef765bdb57b4342c77328f7fdfeaf53dcb0e704f51"
          },
          {
            "rank": 29,
            "chunk_id": "4458-madde-141-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/141",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8471189141273499,
            "text_sha256": "7be7cddfe924b43ade030a0ec0ae6cbe56d0844a10b90000bb2cc721eeda0089"
          },
          {
            "rank": 30,
            "chunk_id": "4458-madde-231-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/231",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8476728200912476,
            "text_sha256": "4e666bd26164d40838e7b097190218b89fb9d7f89447acce71a609015021489f"
          },
          {
            "rank": 31,
            "chunk_id": "4458-madde-10-a-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/10/a",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8484557867050171,
            "text_sha256": "65bb8a0743396522cea028e625b2a57cb4de59c230f3cbed4ad4f95f7665ed87"
          },
          {
            "rank": 32,
            "chunk_id": "4458-madde-68-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/68",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8491600751876831,
            "text_sha256": "9b066ed6cc6604e7b2a732831eb5060c2b32296d490fd8027f97c9cd7660b447"
          },
          {
            "rank": 33,
            "chunk_id": "4458-madde-69-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/69",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8506320714950562,
            "text_sha256": "2ce38d9daae86455b62d1fff4175f8f57fd9ce4bb952b333db74380506d8e480"
          },
          {
            "rank": 34,
            "chunk_id": "4458-madde-7-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/7",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8517706394195557,
            "text_sha256": "4b52c50e7c1a976b3980b18376aedff67c99379bc5c03672572b2baf4cf7a825"
          },
          {
            "rank": 35,
            "chunk_id": "4458-madde-56-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/56",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8551560640335083,
            "text_sha256": "1970d2a90e3d279cd1baf5d6ad7c580ed5f79aa4b0e6b5a79457b6378d032b6c"
          },
          {
            "rank": 36,
            "chunk_id": "4458-madde-158-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/158",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8573062419891357,
            "text_sha256": "b9cca99069c8c8493456f6f3416d00b70650220d91528975f954e699ef7d664b"
          },
          {
            "rank": 37,
            "chunk_id": "4458-madde-161-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/161",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8576453328132629,
            "text_sha256": "563d60293b9f5c5e4500255e9487906dc77896ae74cc71a9417e2ac64aea23ad"
          },
          {
            "rank": 38,
            "chunk_id": "4458-madde-98-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/98",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8621301054954529,
            "text_sha256": "37ecc16981a38cc2f6e2cba6a038b9220c177481c2cf11347db42271009c54bb"
          },
          {
            "rank": 39,
            "chunk_id": "4458-madde-9-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/9",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8625966310501099,
            "text_sha256": "946d9c83f6d803c464f2e636c05e664aba1eb6788ec8ed20b053193f9fbe450d"
          },
          {
            "rank": 40,
            "chunk_id": "4458-madde-121-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/121",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8653693199157715,
            "text_sha256": "ee64169d05a4d28df8b00f0376239ebc5348828b3906e01ec54fc024b42816c0"
          },
          {
            "rank": 41,
            "chunk_id": "4458-madde-70-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/70",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8660263419151306,
            "text_sha256": "a73524ff022af42b9cbf3a9e30f98cc1448e7e214a792263a4b3b7e1ecd38918"
          },
          {
            "rank": 42,
            "chunk_id": "4458-madde-100-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/100",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.869005024433136,
            "text_sha256": "5d1c6ba4a80ca93fdbe00d45d75d9157f71ecf01570fef09de976bdfa95b8588"
          },
          {
            "rank": 43,
            "chunk_id": "4458-madde-143-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/143",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8726447820663452,
            "text_sha256": "2c6f56f015ccc43feaef5df2cf0ccafa8643f3f5efccc16f730ae0fa2fa6fd7c"
          },
          {
            "rank": 44,
            "chunk_id": "4458-madde-37-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/37",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8781978487968445,
            "text_sha256": "c8b6d358b4aed4de85d0ab322752a526ce58d46777a44024ec602c8517fd451c"
          },
          {
            "rank": 45,
            "chunk_id": "4458-madde-198-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/198",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8797120451927185,
            "text_sha256": "f15f08608f0cfbdc9f45216c8ae55b4d5be2504b9780a837892881f573f1a7d9"
          },
          {
            "rank": 46,
            "chunk_id": "4458-madde-10-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/10",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.881270706653595,
            "text_sha256": "e16a9f45c8b40cae31da92640c26ceda2fb415d8268e23ae5f90b074f494691b"
          },
          {
            "rank": 47,
            "chunk_id": "4458-madde-26-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/26",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8815595507621765,
            "text_sha256": "116deb0a2fb7f92ab665138b97ea2ee0877605d7bc9173503e47c5fcf26c0851"
          },
          {
            "rank": 48,
            "chunk_id": "4458-madde-102-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/102",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8830170631408691,
            "text_sha256": "f5464cf375971257aae8562bb0ccaa0d814892ba9ce26d0214285fa9655333ba"
          },
          {
            "rank": 49,
            "chunk_id": "4458-madde-191-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/191",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.883402943611145,
            "text_sha256": "c2173f1439af0f97f2f085e6b2e688f420b39da3ea4ee39436de622daaa3b177"
          },
          {
            "rank": 50,
            "chunk_id": "4458-madde-182-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/182",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8837611079216003,
            "text_sha256": "aed3c33afb987589b28db2747f4c485ff638ca1e9e0517bc44301dac04111ccd"
          }
        ],
        "source_ranks": {
          "5607_kacakcilikla_mucadele_kanunu/normal/3": null,
          "5607_kacakcilikla_mucadele_kanunu/normal/4": null
        }
      },
      "R1": {
        "top5": [
          {
            "rank": 1,
            "chunk_id": "5607-madde-16-chunk-001",
            "document_source_key": "5607_kacakcilikla_mucadele_kanunu/normal/16",
            "document_id": "5607_kacakcilikla_mucadele_kanunu",
            "legislation_number": "5607",
            "distance": 0.8847047090530396,
            "text_sha256": "cd89e500280c2222df0e9175e834ce403e6ad3bffed289e5b83a3d4122332df2"
          },
          {
            "rank": 2,
            "chunk_id": "5607-madde-11-chunk-001",
            "document_source_key": "5607_kacakcilikla_mucadele_kanunu/normal/11",
            "document_id": "5607_kacakcilikla_mucadele_kanunu",
            "legislation_number": "5607",
            "distance": 0.8856291770935059,
            "text_sha256": "2cae2606436a95ca99d39dd80a894ed05b96bfba834d08c15383ffce3cf7e502"
          },
          {
            "rank": 3,
            "chunk_id": "5607-madde-12-chunk-001",
            "document_source_key": "5607_kacakcilikla_mucadele_kanunu/normal/12",
            "document_id": "5607_kacakcilikla_mucadele_kanunu",
            "legislation_number": "5607",
            "distance": 0.8971934914588928,
            "text_sha256": "fe1567d7bc58f192bd2831e1666e3e9397a56364e0779cab27ae624717c93519"
          },
          {
            "rank": 4,
            "chunk_id": "5607-gecici-madde-6-chunk-001",
            "document_source_key": "5607_kacakcilikla_mucadele_kanunu/gecici/6",
            "document_id": "5607_kacakcilikla_mucadele_kanunu",
            "legislation_number": "5607",
            "distance": 0.9243834614753723,
            "text_sha256": "bc5e3d98ebec7a0955e0ace18107734bdff3774a4937214e3dea700360cecdea"
          },
          {
            "rank": 5,
            "chunk_id": "5607-madde-3-chunk-003",
            "document_source_key": "5607_kacakcilikla_mucadele_kanunu/normal/3",
            "document_id": "5607_kacakcilikla_mucadele_kanunu",
            "legislation_number": "5607",
            "distance": 0.930474042892456,
            "text_sha256": "29ac962782279460023c82284c4a74c366f8d9f06c75762b1e86896d92a7d3a1"
          }
        ],
        "source_ranks": {
          "5607_kacakcilikla_mucadele_kanunu/normal/3": 5,
          "5607_kacakcilikla_mucadele_kanunu/normal/4": null
        }
      },
      "R2": {
        "top5": [
          {
            "rank": 1,
            "chunk_id": "4458-madde-57-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/57",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7141185998916626,
            "text_sha256": "18c922e91ab00293fe677615d7b3633ad90572cae297c50e00f525f930e39a91"
          },
          {
            "rank": 2,
            "chunk_id": "4458-madde-167-chunk-002",
            "document_source_key": "4458_gumruk_kanunu/normal/167",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7442929744720459,
            "text_sha256": "01b1bcbb6b8b930c5c17ef9ce25bdf94a21949385a5d60884b5a9e15ee79c54a"
          },
          {
            "rank": 3,
            "chunk_id": "4458-madde-235-chunk-002",
            "document_source_key": "4458_gumruk_kanunu/normal/235",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7468167543411255,
            "text_sha256": "cb7a33090f14cfccf41acae04f50bd838d2424c46c23ca289d2cdf6814516ab2"
          },
          {
            "rank": 4,
            "chunk_id": "4458-madde-235-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/235",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7607426643371582,
            "text_sha256": "213865796a89430ab83594a46796680280c3abf376f2d67f95145cffe89d736f"
          },
          {
            "rank": 5,
            "chunk_id": "4458-madde-236-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/236",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7736935615539551,
            "text_sha256": "78c72e0aada272a95b02f7371e2961ef4b87e2cc2e9e9fc716267e72dd51b0b1"
          }
        ],
        "source_ranks": {
          "5607_kacakcilikla_mucadele_kanunu/normal/3": null,
          "5607_kacakcilikla_mucadele_kanunu/normal/4": null
        }
      }
    }
  },
  "k5607-026": {
    "saved_router_ranking": [
      "5607_kacakcilikla_mucadele_kanunu",
      "4458_gumruk_kanunu",
      "5326_kabahatler_kanunu"
    ],
    "expected_sources": [
      "5607_kacakcilikla_mucadele_kanunu/normal/3",
      "5607_kacakcilikla_mucadele_kanunu/normal/5"
    ],
    "variants": {
      "B0": {
        "top5": [
          {
            "rank": 1,
            "chunk_id": "4458-madde-57-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/57",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.6664212942123413,
            "text_sha256": "18c922e91ab00293fe677615d7b3633ad90572cae297c50e00f525f930e39a91"
          },
          {
            "rank": 2,
            "chunk_id": "4458-madde-24-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/24",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.6823248267173767,
            "text_sha256": "a581f8cf6d3ed8c790d5b1d9e55c27dd025faa70ff1c4245a8609fa7ca5ec896"
          },
          {
            "rank": 3,
            "chunk_id": "4458-madde-187-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/187",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.6835641860961914,
            "text_sha256": "ac19779e0b0a8698de3154b8185addd38dc7dec8718cc71c4898600ea4d0a421"
          },
          {
            "rank": 4,
            "chunk_id": "4458-madde-235-chunk-002",
            "document_source_key": "4458_gumruk_kanunu/normal/235",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.6927468776702881,
            "text_sha256": "cb7a33090f14cfccf41acae04f50bd838d2424c46c23ca289d2cdf6814516ab2"
          },
          {
            "rank": 5,
            "chunk_id": "4458-madde-234-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/234",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.6961438655853271,
            "text_sha256": "ff3755e8a5a182b2b228d9fbe57fae63eab24a72b2bbf3922780d28073285b48"
          },
          {
            "rank": 6,
            "chunk_id": "4458-madde-27-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/27",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7008781433105469,
            "text_sha256": "990518d695526594b7035a349d9dc76f009c86958c78994f68d0f78c8f353fc8"
          },
          {
            "rank": 7,
            "chunk_id": "4458-madde-184-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/184",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7083981037139893,
            "text_sha256": "b3d1087f7e6073bef285131bc0629f0a5c4319faefd2679e64f77da09f721a66"
          },
          {
            "rank": 8,
            "chunk_id": "4458-madde-237-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/237",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7119482755661011,
            "text_sha256": "95841409e5913c2f8e8ffe25ae704623b06bdd77d6aac7296ccf60cdb893eeb6"
          },
          {
            "rank": 9,
            "chunk_id": "4458-madde-25-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/25",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7122122049331665,
            "text_sha256": "e1b47c2f8f3460ae37f416177764e51ee1d0e906334538b8cab68f6b4e546231"
          },
          {
            "rank": 10,
            "chunk_id": "4458-madde-194-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/194",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7177428007125854,
            "text_sha256": "fd4dfb9affd8823bbef6eb4db0c794f92d08d0e66911d7cf925f1d386cbc1726"
          },
          {
            "rank": 11,
            "chunk_id": "4458-madde-198-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/198",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7185063362121582,
            "text_sha256": "f15f08608f0cfbdc9f45216c8ae55b4d5be2504b9780a837892881f573f1a7d9"
          },
          {
            "rank": 12,
            "chunk_id": "4458-madde-236-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/236",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7193396091461182,
            "text_sha256": "78c72e0aada272a95b02f7371e2961ef4b87e2cc2e9e9fc716267e72dd51b0b1"
          },
          {
            "rank": 13,
            "chunk_id": "4458-madde-235-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/235",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7202333807945251,
            "text_sha256": "213865796a89430ab83594a46796680280c3abf376f2d67f95145cffe89d736f"
          },
          {
            "rank": 14,
            "chunk_id": "4458-madde-186-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/186",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7202722430229187,
            "text_sha256": "e3fe527a9838aab7f48017e5b2d0455b1e056e80b7ba7e4b6abf6a486d9dcc93"
          },
          {
            "rank": 15,
            "chunk_id": "4458-madde-179-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/179",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7274408936500549,
            "text_sha256": "bc331011ecbe6309c7cd58845d830f9f350fb7c1ea1b5dfcf5fbc7763c02e600"
          },
          {
            "rank": 16,
            "chunk_id": "4458-madde-213-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/213",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7276542782783508,
            "text_sha256": "07b0c22643fba773a2e6a13cda4159f6eb60e9d5d3b83ba0cc76b8e6f69524d5"
          },
          {
            "rank": 17,
            "chunk_id": "4458-madde-183-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/183",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7383921146392822,
            "text_sha256": "8cb93cf9d1cf1a30b34d5382a83e5b6d29ad3e330845791361848c59672193b9"
          },
          {
            "rank": 18,
            "chunk_id": "4458-madde-231-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/231",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7387205362319946,
            "text_sha256": "4e666bd26164d40838e7b097190218b89fb9d7f89447acce71a609015021489f"
          },
          {
            "rank": 19,
            "chunk_id": "4458-madde-121-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/121",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7435349822044373,
            "text_sha256": "ee64169d05a4d28df8b00f0376239ebc5348828b3906e01ec54fc024b42816c0"
          },
          {
            "rank": 20,
            "chunk_id": "4458-madde-238-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/238",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7440258860588074,
            "text_sha256": "c11239d87c965fa951cb6c2dde9eeb9fb3bde5c6dec3dad38e4abcd05a80cfb5"
          },
          {
            "rank": 21,
            "chunk_id": "4458-madde-119-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/119",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7468618154525757,
            "text_sha256": "231327143c8cf59a550a40f705c6a0375fbdfcb7d36445badae3e006a468b001"
          },
          {
            "rank": 22,
            "chunk_id": "4458-madde-141-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/141",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7488452792167664,
            "text_sha256": "7be7cddfe924b43ade030a0ec0ae6cbe56d0844a10b90000bb2cc721eeda0089"
          },
          {
            "rank": 23,
            "chunk_id": "4458-madde-115-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/115",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7520759701728821,
            "text_sha256": "9ac15fe9a811ac02c887c90eebcd859ab799aa9e506c572efd15953e59c69e5f"
          },
          {
            "rank": 24,
            "chunk_id": "4458-madde-77-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/77",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7525588274002075,
            "text_sha256": "cb5312d71370116227e2dadeda96613599d77bf46ce21a407d4526ef1a886135"
          },
          {
            "rank": 25,
            "chunk_id": "4458-madde-28-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/28",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7533384561538696,
            "text_sha256": "dca3e2782a138529fabca24001576a0a3d2580ee77e881a1ee51e00df317e42d"
          },
          {
            "rank": 26,
            "chunk_id": "4458-madde-241-chunk-002",
            "document_source_key": "4458_gumruk_kanunu/normal/241",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7635216116905212,
            "text_sha256": "b5db2fcac8afd9e79072555aa3633ef3d695451cf664e3faaf418c35bc0365ed"
          },
          {
            "rank": 27,
            "chunk_id": "4458-madde-239-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/239",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7675694227218628,
            "text_sha256": "1655e8c95b3744d061913995cb3bb4bca0e96460022f1b282c42f2b395f95a49"
          },
          {
            "rank": 28,
            "chunk_id": "4458-madde-69-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/69",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7716343998908997,
            "text_sha256": "2ce38d9daae86455b62d1fff4175f8f57fd9ce4bb952b333db74380506d8e480"
          },
          {
            "rank": 29,
            "chunk_id": "4458-madde-167-chunk-002",
            "document_source_key": "4458_gumruk_kanunu/normal/167",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7760986089706421,
            "text_sha256": "01b1bcbb6b8b930c5c17ef9ce25bdf94a21949385a5d60884b5a9e15ee79c54a"
          },
          {
            "rank": 30,
            "chunk_id": "4458-madde-143-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/143",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.776613175868988,
            "text_sha256": "2c6f56f015ccc43feaef5df2cf0ccafa8643f3f5efccc16f730ae0fa2fa6fd7c"
          },
          {
            "rank": 31,
            "chunk_id": "4458-madde-53-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/53",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7781079411506653,
            "text_sha256": "65b36f75c0807147b8304c8bba487a2316f7d0fed24f9cf875626e284a395aa6"
          },
          {
            "rank": 32,
            "chunk_id": "4458-madde-68-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/68",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7792074680328369,
            "text_sha256": "9b066ed6cc6604e7b2a732831eb5060c2b32296d490fd8027f97c9cd7660b447"
          },
          {
            "rank": 33,
            "chunk_id": "4458-madde-104-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/104",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7806828618049622,
            "text_sha256": "e9a58ada897fa772c20beacb3716a7d400cb85cb29a7075364f3e2c4e0fa9dcb"
          },
          {
            "rank": 34,
            "chunk_id": "4458-madde-75-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/75",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.781822919845581,
            "text_sha256": "53ef510c2c22196627340b9c18652cfc57c07d806a4cae5b927c4bcc7c06e79a"
          },
          {
            "rank": 35,
            "chunk_id": "4458-madde-207-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/207",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7837949395179749,
            "text_sha256": "27df5ed93c592f5aa272564f15e1c118700418598731ac7cb8893c5402c22843"
          },
          {
            "rank": 36,
            "chunk_id": "4458-madde-191-a-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/191/a",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7851607799530029,
            "text_sha256": "ab7d790ce48109954acd5d9ffd0467a299a2c2a12e264b7976f7899c6cd7f25b"
          },
          {
            "rank": 37,
            "chunk_id": "4458-madde-78-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/78",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7872630953788757,
            "text_sha256": "fadb2ea3fc56acf010a5e4ef765bdb57b4342c77328f7fdfeaf53dcb0e704f51"
          },
          {
            "rank": 38,
            "chunk_id": "4458-madde-161-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/161",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7884936332702637,
            "text_sha256": "563d60293b9f5c5e4500255e9487906dc77896ae74cc71a9417e2ac64aea23ad"
          },
          {
            "rank": 39,
            "chunk_id": "4458-madde-26-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/26",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7913126945495605,
            "text_sha256": "116deb0a2fb7f92ab665138b97ea2ee0877605d7bc9173503e47c5fcf26c0851"
          },
          {
            "rank": 40,
            "chunk_id": "4458-madde-134-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/134",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7933337688446045,
            "text_sha256": "d66ea0c5f8bd03455dcf9026bb5e47819634362b7aad1ec0c4166490f0495149"
          },
          {
            "rank": 41,
            "chunk_id": "4458-madde-180-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/180",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7952505946159363,
            "text_sha256": "2202ee65aef0ac29097db1927641b81dcf5eb9de0ca34ee7d090fd1182873afa"
          },
          {
            "rank": 42,
            "chunk_id": "4458-madde-100-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/100",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7983140349388123,
            "text_sha256": "5d1c6ba4a80ca93fdbe00d45d75d9157f71ecf01570fef09de976bdfa95b8588"
          },
          {
            "rank": 43,
            "chunk_id": "4458-madde-168-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/168",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8006309866905212,
            "text_sha256": "f7c88896c10f6add4014291ae8d7a01708d7045614ccdf9c63e93d83172a8421"
          },
          {
            "rank": 44,
            "chunk_id": "4458-madde-167-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/167",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8013696670532227,
            "text_sha256": "6c00702ccc75bb880861db66a8102287c6281d967c7e80d65d34b54076c1d085"
          },
          {
            "rank": 45,
            "chunk_id": "5607-madde-16-chunk-001",
            "document_source_key": "5607_kacakcilikla_mucadele_kanunu/normal/16",
            "document_id": "5607_kacakcilikla_mucadele_kanunu",
            "legislation_number": "5607",
            "distance": 0.8036321997642517,
            "text_sha256": "cd89e500280c2222df0e9175e834ce403e6ad3bffed289e5b83a3d4122332df2"
          },
          {
            "rank": 46,
            "chunk_id": "4458-madde-82-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/82",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8060059547424316,
            "text_sha256": "d855f1274628d4a47ae3703cb0a5ed401ccd6dca4f62e93ee60c30c5a43119fd"
          },
          {
            "rank": 47,
            "chunk_id": "4458-madde-98-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/98",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8070825338363647,
            "text_sha256": "37ecc16981a38cc2f6e2cba6a038b9220c177481c2cf11347db42271009c54bb"
          },
          {
            "rank": 48,
            "chunk_id": "4458-madde-241-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/241",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8070868253707886,
            "text_sha256": "bba8b06b0bcfd5e6dc1cb8d5b45386982f41b73a527af707b90e8b6f8ce75f56"
          },
          {
            "rank": 49,
            "chunk_id": "4458-madde-140-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/140",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8125936985015869,
            "text_sha256": "06483b66a483cf6b6ed7c49e8af135342f3bfd707b16cbdac47d36ce4f2c67fe"
          },
          {
            "rank": 50,
            "chunk_id": "4458-madde-232-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/232",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8130285143852234,
            "text_sha256": "b05029313c204e2c8defead43a42b24ea669274dad07f98cab2f08e4e5bd4664"
          }
        ],
        "source_ranks": {
          "5607_kacakcilikla_mucadele_kanunu/normal/3": null,
          "5607_kacakcilikla_mucadele_kanunu/normal/5": null
        }
      },
      "R1": {
        "top5": [
          {
            "rank": 1,
            "chunk_id": "5607-madde-16-chunk-001",
            "document_source_key": "5607_kacakcilikla_mucadele_kanunu/normal/16",
            "document_id": "5607_kacakcilikla_mucadele_kanunu",
            "legislation_number": "5607",
            "distance": 0.8035846948623657,
            "text_sha256": "cd89e500280c2222df0e9175e834ce403e6ad3bffed289e5b83a3d4122332df2"
          },
          {
            "rank": 2,
            "chunk_id": "5607-madde-5-chunk-001",
            "document_source_key": "5607_kacakcilikla_mucadele_kanunu/normal/5",
            "document_id": "5607_kacakcilikla_mucadele_kanunu",
            "legislation_number": "5607",
            "distance": 0.8046808242797852,
            "text_sha256": "9629559d1137d863339afa0de3ab8a96fcc70b1bc54fe80e5849f1344951e9df"
          },
          {
            "rank": 3,
            "chunk_id": "5607-gecici-madde-11-chunk-001",
            "document_source_key": "5607_kacakcilikla_mucadele_kanunu/gecici/11",
            "document_id": "5607_kacakcilikla_mucadele_kanunu",
            "legislation_number": "5607",
            "distance": 0.855682373046875,
            "text_sha256": "d93a68b9977169834e8df0f98104b8009eee37bb69187f69f6462ea5ffc7dc3f"
          },
          {
            "rank": 4,
            "chunk_id": "5607-madde-23-chunk-001",
            "document_source_key": "5607_kacakcilikla_mucadele_kanunu/normal/23",
            "document_id": "5607_kacakcilikla_mucadele_kanunu",
            "legislation_number": "5607",
            "distance": 0.8654850721359253,
            "text_sha256": "49b08bc0cd9cdf38b9c030aee4da03cb7d1e7bcf4c553ce8088556434d781e89"
          },
          {
            "rank": 5,
            "chunk_id": "5607-gecici-madde-10-chunk-001",
            "document_source_key": "5607_kacakcilikla_mucadele_kanunu/gecici/10",
            "document_id": "5607_kacakcilikla_mucadele_kanunu",
            "legislation_number": "5607",
            "distance": 0.8771806955337524,
            "text_sha256": "52100659ea8d86dd79467f13bf00bf1f4936df3652398f86ea17fcfa9053e15f"
          }
        ],
        "source_ranks": {
          "5607_kacakcilikla_mucadele_kanunu/normal/3": null,
          "5607_kacakcilikla_mucadele_kanunu/normal/5": 2
        }
      },
      "R2": {
        "top5": [
          {
            "rank": 1,
            "chunk_id": "4458-madde-57-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/57",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.666262149810791,
            "text_sha256": "18c922e91ab00293fe677615d7b3633ad90572cae297c50e00f525f930e39a91"
          },
          {
            "rank": 2,
            "chunk_id": "4458-madde-24-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/24",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.6823012828826904,
            "text_sha256": "a581f8cf6d3ed8c790d5b1d9e55c27dd025faa70ff1c4245a8609fa7ca5ec896"
          },
          {
            "rank": 3,
            "chunk_id": "4458-madde-187-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/187",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.6835287809371948,
            "text_sha256": "ac19779e0b0a8698de3154b8185addd38dc7dec8718cc71c4898600ea4d0a421"
          },
          {
            "rank": 4,
            "chunk_id": "4458-madde-235-chunk-002",
            "document_source_key": "4458_gumruk_kanunu/normal/235",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.6926824450492859,
            "text_sha256": "cb7a33090f14cfccf41acae04f50bd838d2424c46c23ca289d2cdf6814516ab2"
          },
          {
            "rank": 5,
            "chunk_id": "4458-madde-234-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/234",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.6961226463317871,
            "text_sha256": "ff3755e8a5a182b2b228d9fbe57fae63eab24a72b2bbf3922780d28073285b48"
          }
        ],
        "source_ranks": {
          "5607_kacakcilikla_mucadele_kanunu/normal/3": null,
          "5607_kacakcilikla_mucadele_kanunu/normal/5": null
        }
      }
    }
  },
  "k5607-029": {
    "saved_router_ranking": [
      "5607_kacakcilikla_mucadele_kanunu",
      "4458_gumruk_kanunu",
      "5326_kabahatler_kanunu"
    ],
    "expected_sources": [
      "5607_kacakcilikla_mucadele_kanunu/gecici/10",
      "5607_kacakcilikla_mucadele_kanunu/normal/3"
    ],
    "variants": {
      "B0": {
        "top5": [
          {
            "rank": 1,
            "chunk_id": "5607-gecici-madde-11-chunk-001",
            "document_source_key": "5607_kacakcilikla_mucadele_kanunu/gecici/11",
            "document_id": "5607_kacakcilikla_mucadele_kanunu",
            "legislation_number": "5607",
            "distance": 0.6584870219230652,
            "text_sha256": "d93a68b9977169834e8df0f98104b8009eee37bb69187f69f6462ea5ffc7dc3f"
          },
          {
            "rank": 2,
            "chunk_id": "4458-gecici-madde-9-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/gecici/9",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.6791099905967712,
            "text_sha256": "af0724bf2c9b14f0fd8106dcd4ca1b731f9ac0b88be35040e450c9d36671d389"
          },
          {
            "rank": 3,
            "chunk_id": "4458-gecici-madde-10-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/gecici/10",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7013326287269592,
            "text_sha256": "cfc11f7aec71fee849fb3338c3d3d2e2a643c9910dc29f7d49fc9d990609186b"
          },
          {
            "rank": 4,
            "chunk_id": "5607-gecici-madde-10-chunk-001",
            "document_source_key": "5607_kacakcilikla_mucadele_kanunu/gecici/10",
            "document_id": "5607_kacakcilikla_mucadele_kanunu",
            "legislation_number": "5607",
            "distance": 0.704149603843689,
            "text_sha256": "52100659ea8d86dd79467f13bf00bf1f4936df3652398f86ea17fcfa9053e15f"
          },
          {
            "rank": 5,
            "chunk_id": "4458-madde-180-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/180",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7236523628234863,
            "text_sha256": "2202ee65aef0ac29097db1927641b81dcf5eb9de0ca34ee7d090fd1182873afa"
          },
          {
            "rank": 6,
            "chunk_id": "4458-madde-216-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/216",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7312768697738647,
            "text_sha256": "4231b71cc1404869c8cc7915b24a94db2ff98c2bc41c6e0e11aaac7bf8fd589b"
          },
          {
            "rank": 7,
            "chunk_id": "4458-madde-238-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/238",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7405460476875305,
            "text_sha256": "c11239d87c965fa951cb6c2dde9eeb9fb3bde5c6dec3dad38e4abcd05a80cfb5"
          },
          {
            "rank": 8,
            "chunk_id": "4458-madde-197-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/197",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7595300078392029,
            "text_sha256": "343c741f2fc61b459b7b47db9822b2cc2b6935d48d90928d57fb66fc169c8fb2"
          },
          {
            "rank": 9,
            "chunk_id": "4458-madde-48-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/48",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7610346078872681,
            "text_sha256": "96693ea164300d36bc32de1dd5e27a81fd9e6bb7d13f41c0b89db4d09c3995ee"
          },
          {
            "rank": 10,
            "chunk_id": "4458-madde-242-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/242",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7672156691551208,
            "text_sha256": "77d1b2570e0c1099d4629cd7afbf0f58f3e7993aed7d2d6c5ff1f5b9ae704037"
          },
          {
            "rank": 11,
            "chunk_id": "4458-madde-232-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/232",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7699151039123535,
            "text_sha256": "b05029313c204e2c8defead43a42b24ea669274dad07f98cab2f08e4e5bd4664"
          },
          {
            "rank": 12,
            "chunk_id": "4458-gecici-madde-4-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/gecici/4",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.770389974117279,
            "text_sha256": "2242e00b1a8c3387c09b3ae410903ce79b770eb53988acf866002cc1a4527e7a"
          },
          {
            "rank": 13,
            "chunk_id": "4458-madde-235-chunk-002",
            "document_source_key": "4458_gumruk_kanunu/normal/235",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7796664834022522,
            "text_sha256": "cb7a33090f14cfccf41acae04f50bd838d2424c46c23ca289d2cdf6814516ab2"
          },
          {
            "rank": 14,
            "chunk_id": "4458-gecici-madde-2-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/gecici/2",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7858089208602905,
            "text_sha256": "3cc14956654ffa5fab7378c2f86482dd0abfab994d8ee2eb01fb5ed719225137"
          },
          {
            "rank": 15,
            "chunk_id": "4458-madde-211-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/211",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7938708066940308,
            "text_sha256": "2a3fe8ae8e8d9ba283526992d87ca6fc594401ea753495baa2d3c05c47bebe42"
          },
          {
            "rank": 16,
            "chunk_id": "4458-madde-198-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/198",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7950547933578491,
            "text_sha256": "f15f08608f0cfbdc9f45216c8ae55b4d5be2504b9780a837892881f573f1a7d9"
          },
          {
            "rank": 17,
            "chunk_id": "4458-madde-143-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/143",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7951088547706604,
            "text_sha256": "2c6f56f015ccc43feaef5df2cf0ccafa8643f3f5efccc16f730ae0fa2fa6fd7c"
          },
          {
            "rank": 18,
            "chunk_id": "4458-madde-217-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/217",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7957713007926941,
            "text_sha256": "744f7c8082e800b3ae55da659145901f69cf42929a4b50f99f1f59370f7e4787"
          },
          {
            "rank": 19,
            "chunk_id": "4458-gecici-madde-7-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/gecici/7",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8056668043136597,
            "text_sha256": "ac7858c325bfa1fb23fe0e6f9c86396e58bf1b18575fe879912c167dd3cb4c49"
          },
          {
            "rank": 20,
            "chunk_id": "4458-gecici-madde-11-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/gecici/11",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.808016300201416,
            "text_sha256": "c25fdb2354c1e1b402c8e62d5cfedaff9ba8faa0e32f87bc42245c19831550d1"
          },
          {
            "rank": 21,
            "chunk_id": "4458-gecici-madde-6-chunk-002",
            "document_source_key": "4458_gumruk_kanunu/gecici/6",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8116663694381714,
            "text_sha256": "1d08b171b4daa4465ca2a6f8c8348270548b9424621e921d810840e4d4adcc95"
          },
          {
            "rank": 22,
            "chunk_id": "4458-madde-85-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/85",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.818706214427948,
            "text_sha256": "2763489374d74ab243b8bc1665d0d740431077de0f39d79d4dad93dee1631c5b"
          },
          {
            "rank": 23,
            "chunk_id": "4458-madde-231-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/231",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8187373876571655,
            "text_sha256": "4e666bd26164d40838e7b097190218b89fb9d7f89447acce71a609015021489f"
          },
          {
            "rank": 24,
            "chunk_id": "4458-islenemeyen-hukum-gecici-madde-1-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/islenemeyen_hukum/1",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8221047520637512,
            "text_sha256": "53531cc39c64940ba61976e7be469609f32e3ed7c16dc6169ca10ca41367ff9a"
          },
          {
            "rank": 25,
            "chunk_id": "5607-madde-16-chunk-001",
            "document_source_key": "5607_kacakcilikla_mucadele_kanunu/normal/16",
            "document_id": "5607_kacakcilikla_mucadele_kanunu",
            "legislation_number": "5607",
            "distance": 0.823173999786377,
            "text_sha256": "cd89e500280c2222df0e9175e834ce403e6ad3bffed289e5b83a3d4122332df2"
          },
          {
            "rank": 26,
            "chunk_id": "4458-madde-130-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/130",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8235559463500977,
            "text_sha256": "0620a2748e9a70d615495f2081c1217621e4d13e45d6ec66b9778162969a386c"
          },
          {
            "rank": 27,
            "chunk_id": "4458-madde-142-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/142",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8278552889823914,
            "text_sha256": "19b62607aead911d140ccfabcd3bb9262f766f5a28f09d25f9612c83cbfbfee6"
          },
          {
            "rank": 28,
            "chunk_id": "4458-madde-49-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/49",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8285121321678162,
            "text_sha256": "18b92217295f7b1c0f473286e2a825c1890dd809a28cb4a1977d6ef9682943ce"
          },
          {
            "rank": 29,
            "chunk_id": "4458-madde-213-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/213",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8289973735809326,
            "text_sha256": "07b0c22643fba773a2e6a13cda4159f6eb60e9d5d3b83ba0cc76b8e6f69524d5"
          },
          {
            "rank": 30,
            "chunk_id": "4458-madde-121-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/121",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8311783671379089,
            "text_sha256": "ee64169d05a4d28df8b00f0376239ebc5348828b3906e01ec54fc024b42816c0"
          },
          {
            "rank": 31,
            "chunk_id": "4458-madde-134-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/134",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8315507173538208,
            "text_sha256": "d66ea0c5f8bd03455dcf9026bb5e47819634362b7aad1ec0c4166490f0495149"
          },
          {
            "rank": 32,
            "chunk_id": "4458-madde-184-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/184",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8358471393585205,
            "text_sha256": "b3d1087f7e6073bef285131bc0629f0a5c4319faefd2679e64f77da09f721a66"
          },
          {
            "rank": 33,
            "chunk_id": "4458-madde-234-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/234",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8387725353240967,
            "text_sha256": "ff3755e8a5a182b2b228d9fbe57fae63eab24a72b2bbf3922780d28073285b48"
          },
          {
            "rank": 34,
            "chunk_id": "4458-madde-212-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/212",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8395259380340576,
            "text_sha256": "eb35c0324892f63f3edf60d473ebbc58c8b74922a2f8f8881472e6181192c5fa"
          },
          {
            "rank": 35,
            "chunk_id": "5607-madde-10-chunk-001",
            "document_source_key": "5607_kacakcilikla_mucadele_kanunu/normal/10",
            "document_id": "5607_kacakcilikla_mucadele_kanunu",
            "legislation_number": "5607",
            "distance": 0.8454960584640503,
            "text_sha256": "23f48c24fb2611e0d174ce67b84888fd77b01040133c72a7b79d01056e6de630"
          },
          {
            "rank": 36,
            "chunk_id": "4458-madde-233-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/233",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8455159068107605,
            "text_sha256": "329fee8b1355682900a93f6b6a19c9bf24ad0658f34e12061f13372e0ecbf272"
          },
          {
            "rank": 37,
            "chunk_id": "4458-gecici-madde-1-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/gecici/1",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8457695841789246,
            "text_sha256": "380307ee77374c74d749f97336f8da608198640920bdd7b0a68ccd63b94d28c7"
          },
          {
            "rank": 38,
            "chunk_id": "4458-madde-7-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/7",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8484114408493042,
            "text_sha256": "4b52c50e7c1a976b3980b18376aedff67c99379bc5c03672572b2baf4cf7a825"
          },
          {
            "rank": 39,
            "chunk_id": "4458-madde-201-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/201",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8500457406044006,
            "text_sha256": "97d852032efe28e06793e43caeecd6674235ebaa74ecaecee2499cbde39435f4"
          },
          {
            "rank": 40,
            "chunk_id": "4458-madde-210-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/210",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8532953262329102,
            "text_sha256": "d674adf06411b53bd4b3bdde964f8280d47b8b03087ac7b98dc19cf54db4c4e7"
          },
          {
            "rank": 41,
            "chunk_id": "4458-madde-147-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/147",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8534063100814819,
            "text_sha256": "4bae7ea36ef355f969d86e9df21654a3ade53660bd7ee19c7e01bfcc60aa5ee2"
          },
          {
            "rank": 42,
            "chunk_id": "4458-madde-179-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/179",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8535984754562378,
            "text_sha256": "bc331011ecbe6309c7cd58845d830f9f350fb7c1ea1b5dfcf5fbc7763c02e600"
          },
          {
            "rank": 43,
            "chunk_id": "4458-madde-244-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/244",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8559257984161377,
            "text_sha256": "e52c62583676a84c720bbc3437a83409876dd23e614494109e08e1ede494bce5"
          },
          {
            "rank": 44,
            "chunk_id": "4458-madde-131-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/131",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8563245534896851,
            "text_sha256": "819d7cfc944b208243bcf08d1c799c817f84134be23f7559d4ddcb5121c1d8a1"
          },
          {
            "rank": 45,
            "chunk_id": "4458-madde-214-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/214",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8583183288574219,
            "text_sha256": "e334df574c39c8d986aad4ad9f035d1e25c811f4f98587d8c114549ef5d3e5fb"
          },
          {
            "rank": 46,
            "chunk_id": "4458-madde-196-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/196",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8598237633705139,
            "text_sha256": "65e846b089a26fbcabbd7c23ec4246128ebd808ab8f91adcc87707cfe454b7c5"
          },
          {
            "rank": 47,
            "chunk_id": "4458-madde-193-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/193",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8628572821617126,
            "text_sha256": "d1b78854f634460c8a5015089c5103f1daf132de721fe4653f36728d813faeea"
          },
          {
            "rank": 48,
            "chunk_id": "4458-madde-133-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/133",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8648546934127808,
            "text_sha256": "9db6c2b7070bbbb1d81b8be9a0342472f305229203b45a147bbbf70b7fabd59f"
          },
          {
            "rank": 49,
            "chunk_id": "4458-madde-92-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/92",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8658729791641235,
            "text_sha256": "adad4fc90d6f3c77d41deb1a1e8e657812e44efd9202eb8b3b04665a97164bfb"
          },
          {
            "rank": 50,
            "chunk_id": "4458-madde-241-chunk-002",
            "document_source_key": "4458_gumruk_kanunu/normal/241",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.8659300804138184,
            "text_sha256": "b5db2fcac8afd9e79072555aa3633ef3d695451cf664e3faaf418c35bc0365ed"
          }
        ],
        "source_ranks": {
          "5607_kacakcilikla_mucadele_kanunu/gecici/10": 4,
          "5607_kacakcilikla_mucadele_kanunu/normal/3": null
        }
      },
      "R1": {
        "top5": [
          {
            "rank": 1,
            "chunk_id": "5607-gecici-madde-11-chunk-001",
            "document_source_key": "5607_kacakcilikla_mucadele_kanunu/gecici/11",
            "document_id": "5607_kacakcilikla_mucadele_kanunu",
            "legislation_number": "5607",
            "distance": 0.6588823795318604,
            "text_sha256": "d93a68b9977169834e8df0f98104b8009eee37bb69187f69f6462ea5ffc7dc3f"
          },
          {
            "rank": 2,
            "chunk_id": "5607-gecici-madde-10-chunk-001",
            "document_source_key": "5607_kacakcilikla_mucadele_kanunu/gecici/10",
            "document_id": "5607_kacakcilikla_mucadele_kanunu",
            "legislation_number": "5607",
            "distance": 0.7043999433517456,
            "text_sha256": "52100659ea8d86dd79467f13bf00bf1f4936df3652398f86ea17fcfa9053e15f"
          },
          {
            "rank": 3,
            "chunk_id": "5607-madde-16-chunk-001",
            "document_source_key": "5607_kacakcilikla_mucadele_kanunu/normal/16",
            "document_id": "5607_kacakcilikla_mucadele_kanunu",
            "legislation_number": "5607",
            "distance": 0.8235735893249512,
            "text_sha256": "cd89e500280c2222df0e9175e834ce403e6ad3bffed289e5b83a3d4122332df2"
          },
          {
            "rank": 4,
            "chunk_id": "5607-madde-10-chunk-001",
            "document_source_key": "5607_kacakcilikla_mucadele_kanunu/normal/10",
            "document_id": "5607_kacakcilikla_mucadele_kanunu",
            "legislation_number": "5607",
            "distance": 0.8456796407699585,
            "text_sha256": "23f48c24fb2611e0d174ce67b84888fd77b01040133c72a7b79d01056e6de630"
          },
          {
            "rank": 5,
            "chunk_id": "5607-gecici-madde-3-chunk-001",
            "document_source_key": "5607_kacakcilikla_mucadele_kanunu/gecici/3",
            "document_id": "5607_kacakcilikla_mucadele_kanunu",
            "legislation_number": "5607",
            "distance": 0.9227221608161926,
            "text_sha256": "8748b26e51e1d954d2c04217bbf16ff27729cf086e7853715f0736eb2dac59e4"
          }
        ],
        "source_ranks": {
          "5607_kacakcilikla_mucadele_kanunu/gecici/10": 2,
          "5607_kacakcilikla_mucadele_kanunu/normal/3": null
        }
      },
      "R2": {
        "top5": [
          {
            "rank": 1,
            "chunk_id": "5607-gecici-madde-11-chunk-001",
            "document_source_key": "5607_kacakcilikla_mucadele_kanunu/gecici/11",
            "document_id": "5607_kacakcilikla_mucadele_kanunu",
            "legislation_number": "5607",
            "distance": 0.6588823795318604,
            "text_sha256": "d93a68b9977169834e8df0f98104b8009eee37bb69187f69f6462ea5ffc7dc3f"
          },
          {
            "rank": 2,
            "chunk_id": "4458-gecici-madde-9-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/gecici/9",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.6793810129165649,
            "text_sha256": "af0724bf2c9b14f0fd8106dcd4ca1b731f9ac0b88be35040e450c9d36671d389"
          },
          {
            "rank": 3,
            "chunk_id": "4458-gecici-madde-10-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/gecici/10",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7020284533500671,
            "text_sha256": "cfc11f7aec71fee849fb3338c3d3d2e2a643c9910dc29f7d49fc9d990609186b"
          },
          {
            "rank": 4,
            "chunk_id": "5607-gecici-madde-10-chunk-001",
            "document_source_key": "5607_kacakcilikla_mucadele_kanunu/gecici/10",
            "document_id": "5607_kacakcilikla_mucadele_kanunu",
            "legislation_number": "5607",
            "distance": 0.7043999433517456,
            "text_sha256": "52100659ea8d86dd79467f13bf00bf1f4936df3652398f86ea17fcfa9053e15f"
          },
          {
            "rank": 5,
            "chunk_id": "4458-madde-180-chunk-001",
            "document_source_key": "4458_gumruk_kanunu/normal/180",
            "document_id": "4458_gumruk_kanunu",
            "legislation_number": "4458",
            "distance": 0.7240056991577148,
            "text_sha256": "2202ee65aef0ac29097db1927641b81dcf5eb9de0ca34ee7d090fd1182873afa"
          }
        ],
        "source_ranks": {
          "5607_kacakcilikla_mucadele_kanunu/gecici/10": 4,
          "5607_kacakcilikla_mucadele_kanunu/normal/3": null
        }
      }
    }
  }
}
```

## Interpretation

R1 and R2 are diagnostics only. No production routing candidate was adopted. Correct routing does not claim to solve within-document provision selection, especially for the composite 5607 cases. Any future adopted candidate requires a NEW UNSEEN HOLDOUT.

This is the final M12F routing integration experiment. The next high-level step after review is M12F closure, then M13 — Gümrük Yönetmeliği onboarding.

Production bytes unchanged: `True`; copy logical state unchanged: `True`; protected inputs unchanged: `True`.
