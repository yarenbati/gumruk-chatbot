# M10E-A retrieval experiments

**Status: accepted and closed as a qualified development experiment; the physical storage byte-stability gate remains FAIL.**

B2 is the metric-based development candidate only. Counts, IDs, documents and metadata match, but three physical Chroma storage-file hashes changed. No mutation API was called; root cause remains unresolved. No restoration or retrieval rerun was attempted. This milestone cannot claim full production immutability.

Development-benchmark evidence only; M10E-B blind holdout validation is required before M10F adoption. No holdout was created or inspected. These are retrieval metrics, not legal-answer accuracy.

See [fixed protocol](../../docs/m10e-experiment-protocol.md), [JSON](m10e-retrieval-experiments.json), [CSV](m10e-retrieval-experiments.csv).

## Execution

75 dense Top-20 calls, 3,205 embedding tokens, no SDK retries. B1: zero OpenAI calls. B2/B3 reused every dense payload. No generation or B0 rerun. Prefix integrity: **75/75 exact chunk-ID rankings; 75/75 QualifiedSourceKey sequences; zero differences**.

- **B0**: Frozen M10D dense Top-5; no new baseline retrieval.
- **B1**: BM25 over persisted article_title + section_context + document; positive scores only, Top-20 candidates, Top-5 output.
- **B2**: Dense Top-20 + BM25 Top-20 RRF; sum 1/(60+rank), missing membership zero; descending score, ascending chunk ID ties.
- **B3**: Deduplicate the full B2 candidate ranking by M10D QualifiedSourceKey, retaining first, then select Top-5.
- **B4**: SKIPPED before experiments: shared titles/sections/text can be complementary evidence. No independently justified diversity penalty; no arbitrary tuning.

Fixed: k1=1.5, b=0.75, dense/lexical K=20, RRF K=60, Top-5 output, ascending chunk-ID ties. No post-result parameter tuning.

## Metrics

All rates are percentages; triplets are @1 / @3 / @5.

| Strategy | Subset | ANY | ALL | Law hit | Unexpected Top-1 law | Intrusion@5 |
|---|---|---|---|---|---:|---:|
| B0 | 5326 | 75.6 / 86.7 / 95.6 | 64.4 / 82.2 / 88.9 | 97.8 / 100.0 / 100.0 | 2.2 | 7.11 |
| B0 | 4458 | 56.7 / 73.3 / 80.0 | 46.7 / 66.7 / 76.7 | 93.3 / 93.3 / 93.3 | 6.7 | 6.67 |
| B0 | combined | 68.0 / 81.3 / 89.3 | 57.3 / 76.0 / 84.0 | 96.0 / 97.3 / 97.3 | 4.0 | 6.93 |
| B1 | 5326 | 66.7 / 86.7 / 91.1 | 55.6 / 84.4 / 86.7 | 88.9 / 100.0 / 100.0 | 11.1 | 24.89 |
| B1 | 4458 | 66.7 / 86.7 / 90.0 | 53.3 / 80.0 / 86.7 | 90.0 / 96.7 / 100.0 | 10.0 | 8.67 |
| B1 | combined | 66.7 / 86.7 / 90.7 | 54.7 / 82.7 / 86.7 | 89.3 / 98.7 / 100.0 | 10.7 | 18.40 |
| B2 | 5326 | 82.2 / 95.6 / 97.8 | 73.3 / 93.3 / 97.8 | 100.0 / 100.0 / 100.0 | 0.0 | 10.22 |
| B2 | 4458 | 70.0 / 83.3 / 86.7 | 60.0 / 83.3 / 86.7 | 93.3 / 96.7 / 100.0 | 6.7 | 5.33 |
| B2 | combined | 77.3 / 90.7 / 93.3 | 68.0 / 89.3 / 93.3 | 97.3 / 98.7 / 100.0 | 2.7 | 8.27 |
| B3 | 5326 | 82.2 / 95.6 / 97.8 | 73.3 / 93.3 / 97.8 | 100.0 / 100.0 / 100.0 | 0.0 | 10.22 |
| B3 | 4458 | 70.0 / 83.3 / 86.7 | 60.0 / 83.3 / 86.7 | 93.3 / 96.7 / 100.0 | 6.7 | 5.33 |
| B3 | combined | 77.3 / 90.7 / 93.3 | 68.0 / 89.3 / 93.3 | 97.3 / 98.7 / 100.0 | 2.7 | 8.27 |

B4 skipped before the experiment; no metrics.

## Multi-source and single-source

| Strategy | multi_part ALL@5 (6 questions) | Single-source ANY@5 (24 questions) |
|---|---:|---:|
| B0 | 50.0 | 83.3 |
| B1 | 66.7 | 91.7 |
| B2 | 66.7 | 91.7 |
| B3 | 66.7 | 91.7 |

## case_type_4458

| Strategy | Group | N | ANY@1/3/5 | ALL@1/3/5 |
|---|---|---:|---|---|
| B0 | ambiguity_resistant | 4 | 50.0 / 75.0 / 75.0 | 50.0 / 75.0 / 75.0 |
| B0 | exception_condition | 8 | 62.5 / 62.5 / 75.0 | 62.5 / 62.5 / 75.0 |
| B0 | long_tail | 4 | 50.0 / 75.0 / 100.0 | 50.0 / 75.0 / 100.0 |
| B0 | multi_part | 6 | 50.0 / 66.7 / 66.7 | 0.0 / 33.3 / 50.0 |
| B0 | paraphrase | 8 | 62.5 / 87.5 / 87.5 | 62.5 / 87.5 / 87.5 |
| B1 | ambiguity_resistant | 4 | 75.0 / 75.0 / 75.0 | 75.0 / 75.0 / 75.0 |
| B1 | exception_condition | 8 | 75.0 / 87.5 / 87.5 | 75.0 / 87.5 / 87.5 |
| B1 | long_tail | 4 | 100.0 / 100.0 / 100.0 | 100.0 / 100.0 / 100.0 |
| B1 | multi_part | 6 | 66.7 / 83.3 / 83.3 | 0.0 / 50.0 / 66.7 |
| B1 | paraphrase | 8 | 37.5 / 87.5 / 100.0 | 37.5 / 87.5 / 100.0 |
| B2 | ambiguity_resistant | 4 | 75.0 / 75.0 / 75.0 | 75.0 / 75.0 / 75.0 |
| B2 | exception_condition | 8 | 62.5 / 75.0 / 87.5 | 62.5 / 75.0 / 87.5 |
| B2 | long_tail | 4 | 100.0 / 100.0 / 100.0 | 100.0 / 100.0 / 100.0 |
| B2 | multi_part | 6 | 50.0 / 66.7 / 66.7 | 0.0 / 66.7 / 66.7 |
| B2 | paraphrase | 8 | 75.0 / 100.0 / 100.0 | 75.0 / 100.0 / 100.0 |
| B3 | ambiguity_resistant | 4 | 75.0 / 75.0 / 75.0 | 75.0 / 75.0 / 75.0 |
| B3 | exception_condition | 8 | 62.5 / 75.0 / 87.5 | 62.5 / 75.0 / 87.5 |
| B3 | long_tail | 4 | 100.0 / 100.0 / 100.0 | 100.0 / 100.0 / 100.0 |
| B3 | multi_part | 6 | 50.0 / 66.7 / 66.7 | 0.0 / 66.7 / 66.7 |
| B3 | paraphrase | 8 | 75.0 / 100.0 / 100.0 | 75.0 / 100.0 / 100.0 |

## difficulty_4458

| Strategy | Group | N | ANY@1/3/5 | ALL@1/3/5 |
|---|---|---:|---|---|
| B0 | easy | 8 | 62.5 / 75.0 / 75.0 | 62.5 / 75.0 / 75.0 |
| B0 | hard | 8 | 62.5 / 75.0 / 75.0 | 37.5 / 62.5 / 62.5 |
| B0 | medium | 14 | 50.0 / 71.4 / 85.7 | 42.9 / 64.3 / 85.7 |
| B1 | easy | 8 | 50.0 / 87.5 / 87.5 | 50.0 / 87.5 / 87.5 |
| B1 | hard | 8 | 87.5 / 87.5 / 87.5 | 50.0 / 75.0 / 75.0 |
| B1 | medium | 14 | 64.3 / 85.7 / 92.9 | 57.1 / 78.6 / 92.9 |
| B2 | easy | 8 | 62.5 / 87.5 / 87.5 | 62.5 / 87.5 / 87.5 |
| B2 | hard | 8 | 75.0 / 75.0 / 75.0 | 50.0 / 75.0 / 75.0 |
| B2 | medium | 14 | 71.4 / 85.7 / 92.9 | 64.3 / 85.7 / 92.9 |
| B3 | easy | 8 | 62.5 / 87.5 / 87.5 | 62.5 / 87.5 / 87.5 |
| B3 | hard | 8 | 75.0 / 75.0 / 75.0 | 50.0 / 75.0 / 75.0 |
| B3 | medium | 14 | 71.4 / 85.7 / 92.9 | 64.3 / 85.7 / 92.9 |

## Latency and token attribution

Means in milliseconds. B0 is historical, not a controlled latency comparison. Shared dense time/tokens are attributed per variant, paid only once. Index construction: 69.97 ms. Report I/O excluded.

| Strategy | Subset | Dense | Lexical | Fusion | Dedup | Total | Tokens |
|---|---|---:|---:|---:|---:|---:|---:|
| B0 | 5326 | 408.813 | 0.000 | 0.000 | 0.000 | 408.813 | 1699 |
| B0 | 4458 | 315.393 | 0.000 | 0.000 | 0.000 | 315.393 | 1506 |
| B0 | combined | 371.445 | 0.000 | 0.000 | 0.000 | 371.445 | 3205 |
| B1 | 5326 | 0.000 | 8.008 | 0.000 | 0.000 | 8.008 | 0 |
| B1 | 4458 | 0.000 | 9.319 | 0.000 | 0.000 | 9.319 | 0 |
| B1 | combined | 0.000 | 8.533 | 0.000 | 0.000 | 8.533 | 0 |
| B2 | 5326 | 350.114 | 8.008 | 0.043 | 0.000 | 358.166 | 1699 |
| B2 | 4458 | 227.819 | 9.319 | 0.042 | 0.000 | 237.180 | 1506 |
| B2 | combined | 301.196 | 8.533 | 0.043 | 0.000 | 309.771 | 3205 |
| B3 | 5326 | 350.114 | 8.008 | 0.043 | 0.218 | 358.384 | 1699 |
| B3 | 4458 | 227.819 | 9.319 | 0.042 | 0.211 | 237.391 | 1506 |
| B3 | combined | 301.196 | 8.533 | 0.043 | 0.215 | 309.987 | 3205 |

## Priority cases

Ranks are within the final Top-5; absent means outside that selected set. Full dense and fused candidate rankings are in JSON. B4 skipped.

| Question | Strategy | Top-5 keys in order | Expected ranks | ANY@5 | ALL@5 | Top-1 law |
|---|---|---|---|---|---|---|
| q002 | B0 | 5326/normal/16; 5326/normal/27; 5326/normal/28; 5326/normal/15; 5326/normal/25 | 5326/normal/4: absent | False | False | 5326 |
| q002 | B1 | 5326/normal/4; 5326/normal/21; 4458/normal/5/a; 4458/normal/215; 4458/normal/10 | 5326/normal/4: 1 | True | True | 5326 |
| q002 | B2 | 5326/normal/21; 5326/normal/16; 5326/normal/4; 5326/normal/27; 4458/normal/5/a | 5326/normal/4: 3 | True | True | 5326 |
| q002 | B3 | 5326/normal/21; 5326/normal/16; 5326/normal/4; 5326/normal/27; 4458/normal/5/a | 5326/normal/4: 3 | True | True | 5326 |
| q042 | B0 | 5326/normal/7; 5326/normal/5; 5326/normal/1; 5326/normal/10; 5326/normal/2 | 5326/normal/6: absent | False | False | 5326 |
| q042 | B1 | 5326/normal/6; 4458/normal/10; 5326/normal/4; 4458/normal/26; 4458/normal/5/a | 5326/normal/6: 1 | True | True | 5326 |
| q042 | B2 | 5326/normal/4; 5326/normal/13; 5326/normal/16; 5326/normal/1; 5326/normal/22 | 5326/normal/6: absent | False | False | 5326 |
| q042 | B3 | 5326/normal/4; 5326/normal/13; 5326/normal/16; 5326/normal/1; 5326/normal/22 | 5326/normal/6: absent | False | False | 5326 |
| gk004 | B0 | 4458/normal/161; 4458/normal/74; 4458/normal/155; 4458/normal/160; 4458/normal/159 | 4458/normal/163: absent | False | False | 4458 |
| gk004 | B1 | 4458/normal/168; 4458/normal/150; 4458/normal/163; 4458/normal/160; 4458/normal/108 | 4458/normal/163: 3 | True | True | 4458 |
| gk004 | B2 | 4458/normal/160; 4458/normal/163; 4458/normal/168; 4458/normal/161; 4458/normal/189 | 4458/normal/163: 2 | True | True | 4458 |
| gk004 | B3 | 4458/normal/160; 4458/normal/163; 4458/normal/168; 4458/normal/161; 4458/normal/189 | 4458/normal/163: 2 | True | True | 4458 |
| gk012 | B0 | 4458/normal/167; 4458/normal/235; 4458/normal/167; 4458/normal/158; 4458/normal/56 | 4458/normal/57: absent | False | False | 4458 |
| gk012 | B1 | 4458/normal/167; 4458/normal/57; 4458/normal/32; 4458/normal/144; 4458/normal/109 | 4458/normal/57: 2 | True | True | 4458 |
| gk012 | B2 | 4458/normal/167; 4458/normal/235; 4458/normal/109; 4458/normal/167; 4458/normal/57 | 4458/normal/57: 5 | True | True | 4458 |
| gk012 | B3 | 4458/normal/167; 4458/normal/235; 4458/normal/109; 4458/normal/57; 4458/normal/32 | 4458/normal/57: 4 | True | True | 4458 |
| gk014 | B0 | 4458/normal/78; 4458/normal/161; 4458/normal/121; 4458/normal/158; 4458/normal/113 | 4458/normal/167: absent | False | False | 4458 |
| gk014 | B1 | 4458/normal/168; 4458/normal/142; 4458/normal/115; 4458/normal/187; 4458/normal/164 | 4458/normal/167: absent | False | False | 4458 |
| gk014 | B2 | 4458/normal/168; 4458/normal/142; 4458/normal/157; 4458/normal/115; 4458/normal/187 | 4458/normal/167: absent | False | False | 4458 |
| gk014 | B3 | 4458/normal/168; 4458/normal/142; 4458/normal/157; 4458/normal/115; 4458/normal/187 | 4458/normal/167: absent | False | False | 4458 |
| gk019 | B0 | 4458/normal/133; 4458/normal/194; 4458/normal/135; 4458/normal/141; 4458/normal/168 | 4458/normal/181: absent; 4458/normal/208: absent | False | False | 4458 |
| gk019 | B1 | 4458/normal/181; 4458/normal/132; 4458/normal/133; 4458/normal/182; 4458/normal/134 | 4458/normal/181: 1; 4458/normal/208: absent | True | False | 4458 |
| gk019 | B2 | 4458/normal/133; 4458/normal/168; 4458/normal/184; 4458/normal/141; 4458/normal/134 | 4458/normal/181: absent; 4458/normal/208: absent | False | False | 4458 |
| gk019 | B3 | 4458/normal/133; 4458/normal/168; 4458/normal/184; 4458/normal/141; 4458/normal/134 | 4458/normal/181: absent; 4458/normal/208: absent | False | False | 4458 |
| gk020 | B0 | 5326/normal/28; 5326/normal/43/a; 5326/normal/15; 5326/normal/32; 5326/normal/41 | 4458/normal/234: absent; 4458/normal/241: absent | False | False | 5326 |
| gk020 | B1 | 4458/normal/236; 5326/normal/39; 4458/normal/235; 5326/normal/40; 4458/normal/237 | 4458/normal/234: absent; 4458/normal/241: absent | False | False | 4458 |
| gk020 | B2 | 5326/normal/32; 4458/normal/235; 5326/normal/41; 4458/normal/236; 5326/normal/15 | 4458/normal/234: absent; 4458/normal/241: absent | False | False | 5326 |
| gk020 | B3 | 5326/normal/32; 4458/normal/235; 5326/normal/41; 4458/normal/236; 5326/normal/15 | 4458/normal/234: absent; 4458/normal/241: absent | False | False | 5326 |
| gk028 | B0 | 5326/normal/43/a; 5326/normal/32; 5326/normal/17; 5326/normal/15; 5326/normal/28 | 4458/normal/241: absent | False | False | 5326 |
| gk028 | B1 | 5326/normal/32; 5326/normal/39; 5326/normal/14; 4458/normal/231; 4458/normal/244 | 4458/normal/241: absent | False | False | 5326 |
| gk028 | B2 | 5326/normal/32; 5326/normal/14; 5326/gecici/3; 4458/normal/238; 5326/normal/42 | 4458/normal/241: absent | False | False | 5326 |
| gk028 | B3 | 5326/normal/32; 5326/normal/14; 5326/gecici/3; 4458/normal/238; 5326/normal/42 | 4458/normal/241: absent | False | False | 5326 |
| gk022 | B0 | 4458/normal/5/a; 4458/normal/227; 4458/gecici/6; 4458/normal/228; 4458/gecici/5 | 4458/islenemeyen_hukum/1: absent; 4458/normal/5/a: 1 | True | False | 4458 |
| gk022 | B1 | 4458/islenemeyen_hukum/1; 4458/normal/5/a; 4458/normal/202; 4458/normal/10; 4458/normal/95 | 4458/islenemeyen_hukum/1: 1; 4458/normal/5/a: 2 | True | True | 4458 |
| gk022 | B2 | 4458/normal/5/a; 4458/gecici/6; 4458/islenemeyen_hukum/1; 4458/normal/10; 4458/normal/227 | 4458/islenemeyen_hukum/1: 3; 4458/normal/5/a: 1 | True | True | 4458 |
| gk022 | B3 | 4458/normal/5/a; 4458/gecici/6; 4458/islenemeyen_hukum/1; 4458/normal/10; 4458/normal/227 | 4458/islenemeyen_hukum/1: 3; 4458/normal/5/a: 1 | True | True | 4458 |
| gk029 | B0 | 4458/gecici/1; 4458/normal/50; 4458/normal/46; 4458/normal/70; 4458/normal/69 | 4458/gecici/1: 1 | True | True | 4458 |
| gk029 | B1 | 4458/gecici/1; 4458/gecici/2; 4458/normal/177; 4458/normal/174; 4458/normal/87 | 4458/gecici/1: 1 | True | True | 4458 |
| gk029 | B2 | 4458/gecici/1; 4458/gecici/2; 4458/normal/66; 4458/normal/190; 4458/normal/50 | 4458/gecici/1: 1 | True | True | 4458 |
| gk029 | B3 | 4458/gecici/1; 4458/gecici/2; 4458/normal/66; 4458/normal/190; 4458/normal/50 | 4458/gecici/1: 1 | True | True | 4458 |

## Acceptance and recommendation

| Strategy | Preserve 5326 | Improve 4458 ANY/ALL@5 | Preserve Top-1 law | Improve multi_part | Preserve single-source | Metric eligible |
|---|---|---|---|---|---|---|
| B1 | False | True | False | True | True | False |
| B2 | True | True | True | True | True | True |
| B3 | True | True | True | True | True | True |

B2/B3 have identical aggregate metrics. B3 changes two Top-5 lists without additional recall/completeness gain; B2 is simpler. B1 fails 5326 preservation and legislation selection.

B2 improves 5326 ANY/ALL@5 from 43/45 and 40/45 to 44/45 and 44/45; 4458 from 24/30 and 23/30 to 26/30 and 26/30. Top-1 law hit is 73/75; multi_part ALL@5 rises from 3/6 to 4/6. Intrusion increases overall from 6.93% to 8.27% (5326 increases; 4458 decreases). This tradeoff is not legal-error accuracy.

**B2 remains a qualified development candidate: the physical storage integrity gate failed. No production adoption.**

### Top-5 transitions

- B1 any_source_hit_at_5: improved q002, q042, gk004, gk012, gk019; regressed q016, q020, q022, q030.
- B1 all_sources_match_at_5: improved q002, q033, q042, gk004, gk012, gk022; regressed q016, q020, q022, q030.
- B2 any_source_hit_at_5: improved q002, gk004, gk012; regressed none.
- B2 all_sources_match_at_5: improved q002, q032, q033, q035, gk004, gk012, gk022; regressed none.
- B3 any_source_hit_at_5: improved q002, gk004, gk012; regressed none.
- B3 all_sources_match_at_5: improved q002, q032, q033, q035, gk004, gk012, gk022; regressed none.

## Immutability

Counts before/after: 5326=53, 4458=276, total=329. IDs and full document/metadata content fingerprint equal:

`e85575a671dd0ab8a55ed15fd543e964d9e15f14389d88228510bfe0a5c96ee8`

Physical file-hash equality: **false**. Changed storage files:

- `chroma\448e5756-391d-4ede-87e8-7792e286ce3b\data_level0.bin`: before `8507fc1835a555e67d8a2d885a59352525c337776d3481dafcad172e5079f32e`; after `20ccb38136aab1045c1dbd31ee292752355a95bc1e9e716d1b7e97358cebeda4`.
- `chroma\448e5756-391d-4ede-87e8-7792e286ce3b\length.bin`: before `00ed689c49020456f98541d4ebde91603ce0801dfee1734f422dce3a54ab0877`; after `1c18f71367d6809957499528a354b3bff1f592b4144f1791d6a8a14fa3ac5849`.
- `chroma\chroma.sqlite3`: before `e164fd7b6f8e9cd9da6322762288d07407c031fb2b05b38cf95e69f399717307`; after `c27782299f2cb01ed54c76a84cf7e61d5d3864406e9c8223c93c92c1c2dc8d4c`.

Initial inventory-inspection storage hashes also differ from experiment-entry hashes. No explicit mutation API was invoked; the cause of physical persistence changes is unresolved. The report preserves all three snapshots. No storage repair or restore was attempted.

Frozen files match before/after. Frozen 4458 dataset SHA-256:

`bf81bb00f665435ace8ab28bbce274ba473074825501fcde0af34c98c45bb595`

Protected production code and M10D evaluator unchanged. Only fixed experiment constants added to config. No commit.

## Tests

Pre-run normal gate: **398 passed, 2 skipped** (RUN_OPENAI_INTEGRATION_TESTS=0). Final normal gate: **398 passed, 2 skipped in 28.17s** with integrations disabled. No network/OpenAI/production-Chroma access in normal tests. `git diff --check` passed. All 300 CSV rows agree with the JSON. Frozen hashes remain unchanged. Post-process storage hashes match the in-run after snapshot; they still differ from before.

## Subsequent single-read storage forensics

See [full forensic report](m10e-storage-forensics.md) and [machine-readable fingerprints](m10e-storage-forensics.json). One get returned all 329 finite embeddings of dimension 1536. IDs, documents, metadata and law counts match both original snapshots. No comparable earlier full embedding fingerprint was found: PRE/POST embedding equality remains **UNPROVEN**. This new POST fingerprint does not prove historical vector equality.

Logical record integrity: **PASS**. POST embedding snapshot: **VERIFIED**. Explicit application mutation API calls: **0**. Physical storage byte stability: **FAIL**. The single initialization/get/close lifecycle reproduced changes to chroma.sqlite3, data_level0.bin and length.bin; exact internal cause remains unresolved. Neither full immutability nor corpus corruption is established. Original experiment JSON/CSV and all metrics/rankings remain unchanged.

B2 remains the metric-based development candidate. Combined non-expected-legislation share@5 rises **6.93% -> 8.27%** despite substantial exact-source retrieval gains; other-law presence increases deeper in Top-5. B3 has no aggregate advantage, so B2 is preferred for simplicity. B4 remains intentionally skipped before measurement. Latest offline tests: **398 passed, 2 skipped in 21.17s**, integrations disabled.

## Accepted M10E-A closure

M10E-A is closed as a **qualified development experiment**. The single real
run remains 75 dense calls and 3,205 query-embedding tokens; its authoritative
JSON/CSV, rankings and metrics are preserved unchanged. The historical storage
gate failure remains recorded; acceptance does not imply byte-level immutability
or establish that the production collection is corrupted.

```text
logical_record_integrity: PASS
stored_embeddings_post_snapshot: VERIFIED
embedding_vector_count: 329
embedding_dimension: 1536
pre_post_embedding_equality: UNPROVEN
reason: no compatible pre-M10E full embedding fingerprint exists
explicit_application_mutation_api_calls: 0
physical_storage_byte_stability: FAIL
changed_files_observed_during_read_lifecycle:
  - chroma.sqlite3
  - data_level0.bin
  - length.bin
physical_storage_change_cause: UNRESOLVED
```

Final strategy decisions:

- **B1: rejected** ? fails 5326 preservation / weaker law selection.
- **B2: qualified development candidate** ? no production adoption yet.
- **B3: not preferred** ? same aggregate retrieval metrics as B2, with
  additional deduplication complexity.
- **B4: intentionally skipped before measurement** ? remains skipped;
  no strategy is introduced after seeing results.

The combined non-expected-legislation share@5 increase from **6.93% to 8.27%**
is a **tradeoff, not a failure**: B2 improves exact-source retrieval substantially
while slightly increasing other-law presence deeper in Top-5.

Future experiments must follow the [storage-copy policy](../../docs/m10e-experiment-protocol.md#experimental-storage-policy-for-future-work).
