# M10E-C — Hybrid Retrieval Failure Analysis

M10E-B remains **NOT VALIDATED**, as closed in commit
`5f33c56d59be923d232012d493ccd8f0077a8e69`. Its predeclared multi-source
ALL@5 gate failed: 80% → 60%. No gate or ranking/scoring result was changed.
M10F production adoption remains blocked. **No development candidate selected.**

This analysis uses only the frozen M10E-A/M10E-B report data. All replay
metrics below are **DEVELOPMENT diagnostics, not validation**. No OpenAI,
Chroma query/open, corpus text reconstruction, new holdout, production change,
parameter search, or commit is part of M10E-C.

## 1. Persisted-data availability

| Per-question data | M10E-A: 75 development questions | M10E-B: 30 observed holdout questions |
|---|---|---|
| Dense Top-20 | All 75, `candidate_cache[id].dense_top20`, ordered chunk IDs, source keys, law, distance | Not persisted; only B0 Top-5 with distances |
| BM25 Top-20 | All 75, `rankings.B1` and `lexical_scores`; 73 lists have 20 entries, one 19, one 8 (positive-score filtering) | Not persisted, including no B1 Top-5 |
| Full RRF ranking/scores | All 75, `rankings.B2` and `rrf_scores`; full candidate unions of 24–38 chunks | Not persisted; only B2 output ranks 1–5, no RRF scores |
| B0 Top-5 | All 75, `results.B0`; frozen M10D prefix exactly matches cached dense prefix for all 75 | All 30, `results.B0`; first five of the original single dense Top-20 call |
| B2 Top-5 | All 75, `results.B2`; exactly matches cached RRF prefix | All 30, `results.B2` |
| Other outputs | B1/B3 Top-5, priority-case diagnostics, prefix comparisons | Multi-source diagnostics repeat saved Top-5/source ranks; they do not supply missing candidates |

Authoritative inputs: `m10e-retrieval-experiments.json` and
`m10e-holdout-b0-vs-b2.json` in this directory. Their CSV/Markdown companions
are output/summary projections, not additional full candidate caches.
Collection inventories and fingerprints are not per-question candidate data.
No missing candidate was generated. Historical M10E-A cases cannot supply
BM25 ranks for different M10E-B queries, even when source keys coincide.

M10E-B input identity remains SHA-256
`6c38c04ef73cc8aee755e5e97c748b6b141ad55da888f9fde5a2af51ad17af48`:
30 questions, 10 × 5326, 20 × 4458, 35 distinct QualifiedSourceKeys, DEV gold
overlap 0. Its execution history remains 60 real dense/API calls across two
attempts: 30 in the invalid serialization-failure attempt (results neither
persisted nor inspected), then 30 in the explicitly authorized replacement,
the only valid benchmark, with 1,556 embedding tokens. M10E-C adds zero calls.

## 2. Mechanisms and evidentiary limits

Frozen B2 sums `1/(60 + dense_rank)` and `1/(60 + BM25_rank)`, with zero
contribution for absence from a candidate list, descending total score and
ascending chunk ID for ties. Dense/BM25 candidate limits remain 20; BM25 k1
remains 1.5 and b remains 0.75. Neither score magnitude nor dense-distance
margin enters RRF. It allocates chunk slots, without a protected dense anchor
or a completeness objective.

At these frozen settings, even a chunk at rank 20 in both lists scores
`2/80 = 0.025`, above a rank-1 singleton's `1/61 = 0.01639344262295082`.
This is a structural preference for dual-list membership. It can recover
lexical evidence or displace strong dense evidence. A missing BM25 candidate
has zero contribution, but missing persistence is not evidence of missing
BM25 membership. We do not assert that 189 or 230 was absent from BM25.

Repeated chunks from one source can consume multiple slots: h4458-20 has
two chunks of article 235 at B2 ranks 4 and 5; gk012 has two chunks of 167.
These observations motivate source allocation as a future research issue,
but do not establish that deduplication alone solves either holdout failure.
No third candidate or new source-identity policy is introduced here.

### h4458-14: completeness loss

Gold: `4458/normal/188` and `4458/normal/189`.

| Source | Dense rank (persisted) | BM25 rank/score | RRF rank (persisted output) | RRF score |
|---|---|---|---|---|
| 4458/normal/188 | 2, distance 0.5938588380813599 | Unavailable | 5 | Unavailable |
| 4458/normal/189 | 3, distance 0.6365214586257935 | Unavailable | Outside Top-5; exact rank unavailable | Unavailable |

B0 order: **193, 188, 189, 194, 181**. B2 order: **193, 30, 235, 76, 188**
(all are normal articles of 4458, chunk 001).
Entrants: **30, 235, 76**. Departures: **189, 194, 181**.
Article **235 occupies the old third position**, but the final rankings do
not support a unique causal claim that one particular entrant replaced 189.
The Top-5 budget admits three entrants while moving 188 from rank 2 to 5;
189 loses its slot, causing ALL@5 to fall from true to false while ANY@5 stays true.

Mechanically, each of 30/235/76 must have a lexical contribution: none was
dense Top-5, and a dense-only rank ≥6 could not beat 189's guaranteed dense
contribution `1/63`. This is a deduction from the saved prefixes and frozen
formula, not reconstructed BM25 ranks. Their exact dense membership, lexical
ranks, dual-list status, scores and 189's full RRF rank cannot be established.
Thus candidate pressure with lexical promotion is supported; the relative
contributions and specific token-level explanation remain unobserved.

### h4458-18: dense rank-1 displacement

Gold: `4458/normal/230`, chunk `4458-madde-230-chunk-001`.
Dense rank **1**, distance **0.5596669316291809**; BM25 rank/score **unavailable**;
RRF rank **outside Top-5, exact rank unavailable**; RRF score **unavailable**.

B0: **230, 13, 196, 50, 229**. B2: **13, 196, 62, gecici/6 chunk 002, 229**.
Entrants: **62** and **4458/gecici/6 (chunk 002)**. Departures: **230** and **50**.
Article 13 now occupies rank 1; there is no unique one-for-one replacement map.
ANY and ALL at 1/3/5 all change from true to false.

The dense distance gap to rank 2 is approximately **0.10778284**; RRF does
not use it. Each of the five B2 winners must have a lexical contribution:
a dense-only candidate at rank ≥2 cannot exceed 230's guaranteed `1/61`.
The observed displacement therefore supports **lexical promotion, fixed RRF
balance and Top-5 candidate pressure**. It does not prove that 230 was outside
BM25 Top-20 or that all winners had dual membership. It also cannot isolate
whether lexical rank magnitude, overlap, or a score tie determined the cutoff.
Calling the effect harmful lexical overpromotion is justified relative to
this question's gold; a token-level cause or exact full ranking would be a guess.

### Successful observed-holdout recoveries

| Question | Gold | B0 rank | B2 rank | Limits |
|---|---|---|---|---|
| h4458-08 | 4458/normal/107 | Outside Top-5 | 3 | Exact dense, BM25 and RRF score unavailable |
| h4458-10 | 4458/normal/38 | Outside Top-5 | 2 | Same limitation |
| h4458-20 | 4458/normal/164 | Outside Top-5 | 2 | Same limitation; duplicate 235 chunks occupy ranks 4–5 |

All three recover ANY/ALL@5. Their existence establishes useful hybrid signal,
but the incomplete cache prevents attribution to lexical-only versus consensus evidence.

### M10E-A cases with complete candidate evidence

| Question / gold source | Dense rank | BM25 rank (score) | RRF rank (score) | Explanation |
|---|---|---|---|---|
| q002 / 5326/normal/4 | Absent Top-20 | 1 (32.908067810153256) | 3 (0.01639344262295082) | Lexical-only recovery; B2 also introduces 4458/normal/5/a at rank 5 |
| gk004 / 4458/normal/163 | 6 | 3 (15.046763529443776) | 2 (0.031024531024531024) | Dual-list evidence promotes a dense near miss |
| gk012 / 4458/normal/57 | Absent Top-20 | 2 (12.976232008372532) | 5 (0.016129032258064516) | Lexical-only recovery at a fragile fifth slot |
| gk022 / 4458/islenemeyen_hukum/1 | 10 | 1 (36.071805986181324) | 3 (0.030679156908665108) | Completes the pair with 5/a |
| gk022 / 4458/normal/5/a | 1 | 2 (34.42315093393335) | 1 (0.03252247488101534) | Strong consensus preserves the other gold source |

For q002, lexical rank-3 4458/normal/5/a and dense rank-3 5326/normal/28
both score `1/63`; ascending chunk ID puts the 4458 chunk fifth. This is a
directly evidenced cross-law intrusion from the frozen tie-break, without
requiring a claim about token semantics.

## 3. Two structural candidates, specified before replay

**C1 — dense anchor then hybrid.** Emit dense rank 1. Scan the unchanged B2
ranking in order, skipping already emitted chunk IDs, until five chunks have
been emitted. Dense rank 1 has precedence; all remaining ties inherit frozen
B2's descending RRF/ascending chunk-ID ordering. No score recomputation,
threshold, law filter or gold access. This protects the strongest dense
rank, not all dense Top-5 evidence. Reserving one anchor is an explicit
structural choice, not a tuned numeric threshold; it can sacrifice B2's fifth
slot when the anchor was outside B2 Top-5.

**C2 — equal-turn dense/hybrid allocation.** Start with a dense turn. On each
turn scan that list from its current position, skipping chunk IDs already
emitted, and emit its next unseen chunk. Alternate dense and B2 turns until
five are emitted; if a list is exhausted, the other continues. Preserve each
input's existing order; dense takes the first turn and thus the extra turn
at an odd output budget. This structural dense-first asymmetry is disclosed,
not selected by sweeping quotas. No score thresholds or additional numeric
parameters. Multiple chunks of the same source remain distinct.

Both use the existing output budget of five. Additional API cost is **zero**
relative to B2; a future actual run would still need B2's original dense
embedding/retrieval and BM25 work. Allocation adds O(d+h) worst-case time and
O(5) output/set memory over lists of lengths d/h, with no new index. For the
current unique-chunk prefixes each needs at most five entries from each input.
Existing B2 fusion remains O((d+l) log(d+l)); no BM25/RRF setting changes.

Neither allocation reads question IDs, gold sources, legislation numbers,
text, distances, score margins, article numbers, or per-law performance.
They are source-agnostic scheduling rules that can operate on future
legislation without law-specific cases. This is a design property, not an
empirical claim of future accuracy. Both can protect incorrect dense evidence.
Threshold/weighted variants are rejected here because their extra cutoffs or
weights lack independent justification. No grid search was run.

**Why exact replay is possible despite missing holdout Top-20:** C1 needs
one dense chunk and at most five B2 chunks. For C2, before the fifth output,
at most four IDs are selected. A unique-chunk prefix of five therefore always
contains a next unseen candidate. No selection needs an unpersisted tail.
Randomized deterministic prefix/full-list equivalence tests cover both rules.
This is an exact replay of these allocation rules, not a reconstruction of
missing BM25 or RRF candidates. Broader full-candidate strategies on M10E-B
cannot be replayed from these artifacts.

## 4. Selection and future use

**Select none.** C1 retains all B2 Top-5 recoveries and restores h4458-18,
but leaves h4458-14 incomplete (observed-holdout multi-source ALL@5 stays 60%).
C2 restores both failures and preserves B0's Top-5 successes, but loses B2's
ANY/ALL@5 recoveries on gk012 and h4458-08 and the ALL@5 gain on q033.
Aggregate improvement cannot substitute for those unmet structural goals.
No post-result quota, weight, threshold or third variant is introduced.

Both preserve 5326 ANY/ALL@5 relative to B0 on the two sets. C2 nevertheless
loses one of B2's 5326 completeness gains (q033). C1 has the same average
cross-law intrusion as B2; C2 lowers the 105-question mean but does not provide
a general law-selection guarantee. Both force B0's Top-1 and therefore give
up B2's net M10E-A Top-1 gains: ANY@1 drops from 77.33% to 68.00% and
Legislation Hit@1 from 97.33% to 96.00%. This is another reason not to equate
anchor protection with a universally better result. No new acceptance gate
is asserted.

Any strategy designed using these results must later use a completely **NEW
unseen holdout** before production adoption. The observed 30-question M10E-B
set can never again be blind validation for such a strategy; it is now
development/diagnostic data for that design. No new holdout is created here.

## 5. Future corpus expansion

The two allocation rules do not depend on there being exactly two laws and
could accept ranked chunks from 5607, 2009/15481, Gümrük Yönetmeliği and
Tasfiye Yönetmeliği. Compatibility requires complete, consistent existing
QualifiedSourceKey metadata for each admitted record; this analysis does not
claim that those corpora are already indexed or their identifiers resolved.

Fragile assumptions as the corpus grows:

- A fixed Top-20 pool covers a smaller share of plausible evidence. More
  similar provisions can crowd either candidate pool and increase dual-list
  competition, including across laws. No limit is adjusted here.
- BM25 document frequency/average length and dense neighbors change with
  corpus composition. Neither these ranks nor today's recoveries are stable
  guarantees across expansion; rank-1 protection can protect the wrong law.
- Related regulations share vocabulary and repeat statutory provisions.
  Chunk-level fusion can allocate several of five slots to one source or
  closely related sources, reducing space for complementary evidence.
- Cross-law presence is not intrinsically an error for future cross-document
  questions. The current metric measures disagreement with expected laws,
  whose future gold sets must represent legitimate cross-document evidence.
- Ascending chunk-ID tie-breaking is deterministic but not semantically
  neutral (q002 illustrates a current effect). More documents and identifier
  namespaces may make ties and source collisions more consequential.
- Existing `(legislation_number, article_type, article_no)` semantics are
  unchanged. Do not assume that regulation titles, decision numbering such
  as 2009/15481, versions, or multiple documents per legislation fit a globally
  unique document identity without further work. Document_id-centered
  generalization remains deferred to **M11**.

## 6. Metric and taxonomy definitions

ANY/ALL at 1/3/5 use frozen QualifiedSourceKey set matching. Legislation Hit
at each cutoff means at least one expected law appears. Single-source ANY@5
uses questions with exactly one gold key; multi-source ALL@5 uses more than
one gold key, not the `multi_part` label. Cross-law intrusion@5 is the mean
per-question share of known-law Top-5 chunks outside expected laws, matching
the frozen reports; it is not the percentage of questions with any intrusion.
Repeated chunks count as separate intrusion slots. All current ranks have
known laws. Tables give percentages, rounded only for display.

Taxonomy is overlapping and evaluates **every saved Top-5 ordering**:

- HYBRID RECOVERY: a gold source enters the prefix at any of 1/3/5.
- DENSE EVIDENCE DISPLACEMENT: a gold source leaves a prefix at any of 1/3/5.
  This includes demotion within Top-5, not only a Top-5 miss; it does not mean
  every displaced nongold chunk was independently verified as relevant.
- MULTI-SOURCE COMPLETENESS LOSS/GAIN: ALL@5 flips on a multi-source question.
- CROSS-LAW INTRUSION: a new known-law foreign chunk enters Top-5, even if
  another foreign chunk leaves and the total share does not increase.
- BENIGN REORDERING: chunk ordering/membership changes without any preceding
  label; benign is relative to persisted gold coverage at measured cutoffs,
  not an assessment of answer quality. Foreign-chunk removals can occur here.

Unchanged chunk sequences are listed separately. Full B0→B2 Top-20 changes
cannot be claimed for M10E-B. The per-question ledger below covers all 105
saved output comparisons, including membership changes and source duplicates;
exact chunk IDs are retained in the structured replay JSON/CSV.

## 7. Exact taxonomy question IDs

### M10E-A

- **HYBRID RECOVERY (20)**: q001, q002, q014, q020, q023, q025, q028, q032, q033, q035, gk002, gk003, gk004, gk012, gk015, gk021, gk022, gk023, gk025, gk027.
- **DENSE EVIDENCE DISPLACEMENT (3)**: q016, q035, gk001.
- **MULTI-SOURCE COMPLETENESS LOSS (0)**: none.
- **MULTI-SOURCE COMPLETENESS GAIN (4)**: q032, q033, q035, gk022.
- **CROSS-LAW INTRUSION (14)**: q002, q005, q006, q021, q024, q026, q028, q029, q030, q036, q041, q044, gk003, gk028.
- **BENIGN REORDERING (42)**: q003, q004, q007, q008, q009, q010, q011, q012, q013, q015, q017, q018, q019, q022, q027, q031, q034, q037, q038, q039, q040, q042, q043, q045, gk005, gk006, gk007, gk008, gk009, gk010, gk011, gk013, gk014, gk016, gk017, gk018, gk019, gk020, gk024, gk026, gk029, gk030.
- **UNCHANGED**: none.

### M10E-B

- **HYBRID RECOVERY (7)**: h5326-10, h4458-05, h4458-08, h4458-10, h4458-12, h4458-15, h4458-20.
- **DENSE EVIDENCE DISPLACEMENT (3)**: h5326-10, h4458-14, h4458-18.
- **MULTI-SOURCE COMPLETENESS LOSS (1)**: h4458-14.
- **MULTI-SOURCE COMPLETENESS GAIN (0)**: none.
- **CROSS-LAW INTRUSION (6)**: h5326-03, h5326-04, h5326-05, h5326-06, h5326-07, h5326-08.
- **BENIGN REORDERING (15)**: h5326-01, h5326-02, h5326-09, h4458-01, h4458-02, h4458-03, h4458-04, h4458-06, h4458-07, h4458-09, h4458-11, h4458-13, h4458-16, h4458-17, h4458-19.
- **UNCHANGED**: none.

## 8. Offline replay metrics — DEVELOPMENT ONLY

The module `python -m src.m10e_failure_analysis` reads only the two frozen JSON reports and writes the diagnostic JSON/CSV. It verifies all B0/B2 Boolean scores and intrusion shares against persisted scores. No retrieval modules or external libraries are imported. JSON stores full precision and denominators; CSV contains 420 question/strategy rows.

### M10E-A/all (development)

Questions: 75; single-source: 63; multi-source: 12.

| Metric | B0 | B2 | C1 | C2 |
|---|---|---|---|---|
| ANY@1 | 68.00% | 77.33% | 68.00% | 68.00% |
| ANY@3 | 81.33% | 90.67% | 92.00% | 86.67% |
| ANY@5 | 89.33% | 93.33% | 93.33% | 92.00% |
| ALL@1 | 57.33% | 68.00% | 57.33% | 57.33% |
| ALL@3 | 76.00% | 89.33% | 90.67% | 80.00% |
| ALL@5 | 84.00% | 93.33% | 93.33% | 90.67% |
| Legislation Hit@1 | 96.00% | 97.33% | 96.00% | 96.00% |
| Legislation Hit@3 | 97.33% | 98.67% | 98.67% | 97.33% |
| Legislation Hit@5 | 97.33% | 100.00% | 100.00% | 98.67% |
| single-source ANY@5 | 90.48% | 95.24% | 95.24% | 93.65% |
| multi-source ALL@5 | 50.00% | 83.33% | 83.33% | 75.00% |
| cross-law intrusion@5 | 6.93% | 8.27% | 8.27% | 6.93% |

### M10E-A/5326 (development)

Questions: 45; single-source: 39; multi-source: 6.

| Metric | B0 | B2 | C1 | C2 |
|---|---|---|---|---|
| ANY@1 | 75.56% | 82.22% | 75.56% | 75.56% |
| ANY@3 | 86.67% | 95.56% | 97.78% | 93.33% |
| ANY@5 | 95.56% | 97.78% | 97.78% | 97.78% |
| ALL@1 | 64.44% | 73.33% | 64.44% | 64.44% |
| ALL@3 | 82.22% | 93.33% | 95.56% | 86.67% |
| ALL@5 | 88.89% | 97.78% | 97.78% | 95.56% |
| Legislation Hit@1 | 97.78% | 100.00% | 97.78% | 97.78% |
| Legislation Hit@3 | 100.00% | 100.00% | 100.00% | 100.00% |
| Legislation Hit@5 | 100.00% | 100.00% | 100.00% | 100.00% |
| single-source ANY@5 | 94.87% | 97.44% | 97.44% | 97.44% |
| multi-source ALL@5 | 50.00% | 100.00% | 100.00% | 83.33% |
| cross-law intrusion@5 | 7.11% | 10.22% | 10.22% | 7.56% |

### M10E-A/4458 (development)

Questions: 30; single-source: 24; multi-source: 6.

| Metric | B0 | B2 | C1 | C2 |
|---|---|---|---|---|
| ANY@1 | 56.67% | 70.00% | 56.67% | 56.67% |
| ANY@3 | 73.33% | 83.33% | 83.33% | 76.67% |
| ANY@5 | 80.00% | 86.67% | 86.67% | 83.33% |
| ALL@1 | 46.67% | 60.00% | 46.67% | 46.67% |
| ALL@3 | 66.67% | 83.33% | 83.33% | 70.00% |
| ALL@5 | 76.67% | 86.67% | 86.67% | 83.33% |
| Legislation Hit@1 | 93.33% | 93.33% | 93.33% | 93.33% |
| Legislation Hit@3 | 93.33% | 96.67% | 96.67% | 93.33% |
| Legislation Hit@5 | 93.33% | 100.00% | 100.00% | 96.67% |
| single-source ANY@5 | 83.33% | 91.67% | 91.67% | 87.50% |
| multi-source ALL@5 | 50.00% | 66.67% | 66.67% | 66.67% |
| cross-law intrusion@5 | 6.67% | 5.33% | 5.33% | 6.00% |

### M10E-B/all (development)

Questions: 30; single-source: 25; multi-source: 5.

| Metric | B0 | B2 | C1 | C2 |
|---|---|---|---|---|
| ANY@1 | 70.00% | 73.33% | 70.00% | 70.00% |
| ANY@3 | 83.33% | 93.33% | 93.33% | 93.33% |
| ANY@5 | 90.00% | 96.67% | 100.00% | 96.67% |
| ALL@1 | 63.33% | 63.33% | 63.33% | 63.33% |
| ALL@3 | 80.00% | 90.00% | 90.00% | 86.67% |
| ALL@5 | 86.67% | 90.00% | 93.33% | 93.33% |
| Legislation Hit@1 | 100.00% | 100.00% | 100.00% | 100.00% |
| Legislation Hit@3 | 100.00% | 100.00% | 100.00% | 100.00% |
| Legislation Hit@5 | 100.00% | 100.00% | 100.00% | 100.00% |
| single-source ANY@5 | 88.00% | 96.00% | 100.00% | 96.00% |
| multi-source ALL@5 | 80.00% | 60.00% | 60.00% | 80.00% |
| cross-law intrusion@5 | 6.67% | 7.33% | 7.33% | 7.33% |

### M10E-B/5326 (development)

Questions: 10; single-source: 9; multi-source: 1.

| Metric | B0 | B2 | C1 | C2 |
|---|---|---|---|---|
| ANY@1 | 100.00% | 100.00% | 100.00% | 100.00% |
| ANY@3 | 100.00% | 100.00% | 100.00% | 100.00% |
| ANY@5 | 100.00% | 100.00% | 100.00% | 100.00% |
| ALL@1 | 90.00% | 90.00% | 90.00% | 90.00% |
| ALL@3 | 100.00% | 100.00% | 100.00% | 100.00% |
| ALL@5 | 100.00% | 100.00% | 100.00% | 100.00% |
| Legislation Hit@1 | 100.00% | 100.00% | 100.00% | 100.00% |
| Legislation Hit@3 | 100.00% | 100.00% | 100.00% | 100.00% |
| Legislation Hit@5 | 100.00% | 100.00% | 100.00% | 100.00% |
| single-source ANY@5 | 100.00% | 100.00% | 100.00% | 100.00% |
| multi-source ALL@5 | 100.00% | 100.00% | 100.00% | 100.00% |
| cross-law intrusion@5 | 20.00% | 22.00% | 22.00% | 22.00% |

### M10E-B/4458 (development)

Questions: 20; single-source: 16; multi-source: 4.

| Metric | B0 | B2 | C1 | C2 |
|---|---|---|---|---|
| ANY@1 | 55.00% | 60.00% | 55.00% | 55.00% |
| ANY@3 | 75.00% | 90.00% | 90.00% | 90.00% |
| ANY@5 | 85.00% | 95.00% | 100.00% | 95.00% |
| ALL@1 | 50.00% | 50.00% | 50.00% | 50.00% |
| ALL@3 | 70.00% | 85.00% | 85.00% | 80.00% |
| ALL@5 | 80.00% | 85.00% | 90.00% | 90.00% |
| Legislation Hit@1 | 100.00% | 100.00% | 100.00% | 100.00% |
| Legislation Hit@3 | 100.00% | 100.00% | 100.00% | 100.00% |
| Legislation Hit@5 | 100.00% | 100.00% | 100.00% | 100.00% |
| single-source ANY@5 | 81.25% | 93.75% | 100.00% | 93.75% |
| multi-source ALL@5 | 75.00% | 50.00% | 50.00% | 75.00% |
| cross-law intrusion@5 | 0.00% | 0.00% | 0.00% | 0.00% |

### combined/all (development)

Questions: 105; single-source: 88; multi-source: 17.

| Metric | B0 | B2 | C1 | C2 |
|---|---|---|---|---|
| ANY@1 | 68.57% | 76.19% | 68.57% | 68.57% |
| ANY@3 | 81.90% | 91.43% | 92.38% | 88.57% |
| ANY@5 | 89.52% | 94.29% | 95.24% | 93.33% |
| ALL@1 | 59.05% | 66.67% | 59.05% | 59.05% |
| ALL@3 | 77.14% | 89.52% | 90.48% | 81.90% |
| ALL@5 | 84.76% | 92.38% | 93.33% | 91.43% |
| Legislation Hit@1 | 97.14% | 98.10% | 97.14% | 97.14% |
| Legislation Hit@3 | 98.10% | 99.05% | 99.05% | 98.10% |
| Legislation Hit@5 | 98.10% | 100.00% | 100.00% | 99.05% |
| single-source ANY@5 | 89.77% | 95.45% | 96.59% | 94.32% |
| multi-source ALL@5 | 58.82% | 76.47% | 76.47% | 76.47% |
| cross-law intrusion@5 | 6.86% | 8.00% | 8.00% | 7.05% |

### combined/5326 (development)

Questions: 55; single-source: 48; multi-source: 7.

| Metric | B0 | B2 | C1 | C2 |
|---|---|---|---|---|
| ANY@1 | 80.00% | 85.45% | 80.00% | 80.00% |
| ANY@3 | 89.09% | 96.36% | 98.18% | 94.55% |
| ANY@5 | 96.36% | 98.18% | 98.18% | 98.18% |
| ALL@1 | 69.09% | 76.36% | 69.09% | 69.09% |
| ALL@3 | 85.45% | 94.55% | 96.36% | 89.09% |
| ALL@5 | 90.91% | 98.18% | 98.18% | 96.36% |
| Legislation Hit@1 | 98.18% | 100.00% | 98.18% | 98.18% |
| Legislation Hit@3 | 100.00% | 100.00% | 100.00% | 100.00% |
| Legislation Hit@5 | 100.00% | 100.00% | 100.00% | 100.00% |
| single-source ANY@5 | 95.83% | 97.92% | 97.92% | 97.92% |
| multi-source ALL@5 | 57.14% | 100.00% | 100.00% | 85.71% |
| cross-law intrusion@5 | 9.45% | 12.36% | 12.36% | 10.18% |

### combined/4458 (development)

Questions: 50; single-source: 40; multi-source: 10.

| Metric | B0 | B2 | C1 | C2 |
|---|---|---|---|---|
| ANY@1 | 56.00% | 66.00% | 56.00% | 56.00% |
| ANY@3 | 74.00% | 86.00% | 86.00% | 82.00% |
| ANY@5 | 82.00% | 90.00% | 92.00% | 88.00% |
| ALL@1 | 48.00% | 56.00% | 48.00% | 48.00% |
| ALL@3 | 68.00% | 84.00% | 84.00% | 74.00% |
| ALL@5 | 78.00% | 86.00% | 88.00% | 86.00% |
| Legislation Hit@1 | 96.00% | 96.00% | 96.00% | 96.00% |
| Legislation Hit@3 | 96.00% | 98.00% | 98.00% | 96.00% |
| Legislation Hit@5 | 96.00% | 100.00% | 100.00% | 98.00% |
| single-source ANY@5 | 82.50% | 92.50% | 95.00% | 90.00% |
| multi-source ALL@5 | 60.00% | 60.00% | 60.00% | 70.00% |
| cross-law intrusion@5 | 4.00% | 3.20% | 3.20% | 3.60% |

## 9. Exact recoveries and regressions

Boolean metric transitions only: recovery = false to true, regression = true to false. Rows with no transitions are omitted; all omitted comparisons have none. Intrusion rows separately list increased/decreased shares, where lower is preferable. Taxonomy prefix source changes can occur even when an aggregate Boolean does not change.

### M10E-A

| Strategy vs baseline | Metric | Recoveries | Regressions |
|---|---|---|---|
| B2 vs B0 | ANY@1 | q001, q014, q020, q025, q028, gk002, gk003, gk023, gk025, gk027 | q016, q035, gk001 |
| B2 vs B0 | ANY@3 | q001, q002, q020, q023, q033, gk004, gk015, gk025 | q016 |
| B2 vs B0 | ANY@5 | q002, gk004, gk012 | none |
| B2 vs B0 | ALL@1 | q001, q014, q020, q025, q028, gk002, gk003, gk023, gk025, gk027 | q016, gk001 |
| B2 vs B0 | ALL@3 | q001, q002, q020, q023, q032, q035, gk004, gk015, gk021, gk022, gk025 | q016 |
| B2 vs B0 | ALL@5 | q002, q032, q033, q035, gk004, gk012, gk022 | none |
| B2 vs B0 | Legislation Hit@1 | q028 | none |
| B2 vs B0 | Legislation Hit@3 | gk020 | none |
| B2 vs B0 | Legislation Hit@5 | gk020, gk028 | none |
| C1 vs B0 | ANY@3 | q001, q002, q020, q023, q033, gk004, gk015, gk025 | none |
| C1 vs B0 | ANY@5 | q002, gk004, gk012 | none |
| C1 vs B0 | ALL@3 | q001, q002, q020, q023, q032, q035, gk004, gk015, gk021, gk022, gk025 | none |
| C1 vs B0 | ALL@5 | q002, q032, q033, q035, gk004, gk012, gk022 | none |
| C1 vs B0 | Legislation Hit@3 | gk020 | none |
| C1 vs B0 | Legislation Hit@5 | gk020, gk028 | none |
| C1 vs B2 | ANY@1 | q016, q035, gk001 | q001, q014, q020, q025, q028, gk002, gk003, gk023, gk025, gk027 |
| C1 vs B2 | ANY@3 | q016 | none |
| C1 vs B2 | ALL@1 | q016, gk001 | q001, q014, q020, q025, q028, gk002, gk003, gk023, gk025, gk027 |
| C1 vs B2 | ALL@3 | q016 | none |
| C1 vs B2 | Legislation Hit@1 | none | q028 |
| C2 vs B0 | ANY@3 | q001, q020, q033, gk025 | none |
| C2 vs B0 | ANY@5 | q002, gk004 | none |
| C2 vs B0 | ALL@3 | q001, q020, gk025 | none |
| C2 vs B0 | ALL@5 | q002, q032, q035, gk004, gk022 | none |
| C2 vs B0 | Legislation Hit@5 | gk020 | none |
| C2 vs B2 | ANY@1 | q016, q035, gk001 | q001, q014, q020, q025, q028, gk002, gk003, gk023, gk025, gk027 |
| C2 vs B2 | ANY@3 | q016 | q002, q023, gk004, gk015 |
| C2 vs B2 | ANY@5 | none | gk012 |
| C2 vs B2 | ALL@1 | q016, gk001 | q001, q014, q020, q025, q028, gk002, gk003, gk023, gk025, gk027 |
| C2 vs B2 | ALL@3 | q016 | q002, q023, q032, q035, gk004, gk015, gk021, gk022 |
| C2 vs B2 | ALL@5 | none | q033, gk012 |
| C2 vs B2 | Legislation Hit@1 | none | q028 |
| C2 vs B2 | Legislation Hit@3 | none | gk020 |
| C2 vs B2 | Legislation Hit@5 | none | gk028 |

| Strategy vs baseline | Intrusion share decreases | Intrusion share increases |
|---|---|---|
| B2 vs B0 | q028, gk020, gk028 | q002, q005, q006, q024, q026, q029, q030, q041, gk003 |
| C1 vs B0 | q028, gk020, gk028 | q002, q005, q006, q024, q026, q029, q030, q041, gk003 |
| C1 vs B2 | none | none |
| C2 vs B0 | q028, gk020 | q030, q041 |
| C2 vs B2 | q002, q005, q006, q024, q026, q029, gk003 | gk020, gk028 |

### M10E-B

| Strategy vs baseline | Metric | Recoveries | Regressions |
|---|---|---|---|
| B2 vs B0 | ANY@1 | h4458-05, h4458-15 | h4458-18 |
| B2 vs B0 | ANY@3 | h4458-05, h4458-08, h4458-10, h4458-12, h4458-20 | h4458-14, h4458-18 |
| B2 vs B0 | ANY@5 | h4458-08, h4458-10, h4458-20 | h4458-18 |
| B2 vs B0 | ALL@1 | h4458-05 | h4458-18 |
| B2 vs B0 | ALL@3 | h4458-05, h4458-08, h4458-10, h4458-12, h4458-20 | h4458-14, h4458-18 |
| B2 vs B0 | ALL@5 | h4458-08, h4458-10, h4458-20 | h4458-14, h4458-18 |
| C1 vs B0 | ANY@3 | h4458-05, h4458-10, h4458-12, h4458-20 | h4458-14 |
| C1 vs B0 | ANY@5 | h4458-08, h4458-10, h4458-20 | none |
| C1 vs B0 | ALL@3 | h4458-05, h4458-10, h4458-12, h4458-20 | h4458-14 |
| C1 vs B0 | ALL@5 | h4458-08, h4458-10, h4458-20 | h4458-14 |
| C1 vs B2 | ANY@1 | h4458-18 | h4458-05, h4458-15 |
| C1 vs B2 | ANY@3 | h4458-18 | h4458-08 |
| C1 vs B2 | ANY@5 | h4458-18 | none |
| C1 vs B2 | ALL@1 | h4458-18 | h4458-05 |
| C1 vs B2 | ALL@3 | h4458-18 | h4458-08 |
| C1 vs B2 | ALL@5 | h4458-18 | none |
| C2 vs B0 | ANY@3 | h4458-05, h4458-10, h4458-20 | none |
| C2 vs B0 | ANY@5 | h4458-10, h4458-20 | none |
| C2 vs B0 | ALL@3 | h4458-05, h4458-10, h4458-20 | h4458-14 |
| C2 vs B0 | ALL@5 | h4458-10, h4458-20 | none |
| C2 vs B2 | ANY@1 | h4458-18 | h4458-05, h4458-15 |
| C2 vs B2 | ANY@3 | h4458-14, h4458-18 | h4458-08, h4458-12 |
| C2 vs B2 | ANY@5 | h4458-18 | h4458-08 |
| C2 vs B2 | ALL@1 | h4458-18 | h4458-05 |
| C2 vs B2 | ALL@3 | h4458-18 | h4458-08, h4458-12 |
| C2 vs B2 | ALL@5 | h4458-14, h4458-18 | h4458-08 |

| Strategy vs baseline | Intrusion share decreases | Intrusion share increases |
|---|---|---|
| B2 vs B0 | h5326-04, h5326-05, h5326-09 | h5326-03, h5326-07, h5326-08 |
| C1 vs B0 | h5326-04, h5326-05, h5326-09 | h5326-03, h5326-07, h5326-08 |
| C1 vs B2 | none | none |
| C2 vs B0 | none | h5326-08 |
| C2 vs B2 | h5326-03, h5326-07, h5326-08 | h5326-04, h5326-05, h5326-09 |

## 10. Complete B0 to B2 output ledger

Lists show QualifiedSourceKeys in rank order, including repeated keys from distinct chunks. Chunk-level identities and all candidate replay outputs are available in the companion JSON/CSV.

| Benchmark / question | B0 Top-5 | B2 Top-5 | Taxonomy |
|---|---|---|---|
| M10E-A / q001 | 5326/normal/7, 5326/normal/1, 5326/normal/14, 5326/normal/2, 5326/normal/9 | 5326/normal/2, 5326/normal/7, 5326/normal/4, 5326/normal/15, 5326/normal/5 | HYBRID RECOVERY |
| M10E-A / q002 | 5326/normal/16, 5326/normal/27, 5326/normal/28, 5326/normal/15, 5326/normal/25 | 5326/normal/21, 5326/normal/16, 5326/normal/4, 5326/normal/27, 4458/normal/5/a | HYBRID RECOVERY; CROSS-LAW INTRUSION |
| M10E-A / q003 | 5326/normal/9, 5326/normal/41, 5326/normal/39, 5326/normal/43/a, 5326/normal/15 | 5326/normal/9, 5326/normal/39, 5326/normal/15, 5326/normal/14, 5326/normal/41 | BENIGN REORDERING |
| M10E-A / q004 | 5326/normal/11, 5326/normal/21, 5326/normal/20, 5326/normal/43/a, 5326/gecici/3 | 5326/normal/11, 5326/normal/43/c, 5326/normal/20, 5326/normal/17, 5326/normal/41 | BENIGN REORDERING |
| M10E-A / q005 | 5326/normal/12, 5326/normal/19, 5326/normal/28, 5326/normal/27, 5326/normal/5 | 5326/normal/12, 5326/normal/27, 5326/normal/28, 5326/normal/19, 4458/gecici/6 | CROSS-LAW INTRUSION |
| M10E-A / q006 | 5326/normal/13, 5326/normal/14, 5326/normal/37, 5326/normal/43/a, 5326/normal/36 | 5326/normal/13, 5326/normal/37, 5326/normal/14, 5326/normal/20, 4458/normal/239 | CROSS-LAW INTRUSION |
| M10E-A / q007 | 5326/normal/14, 5326/normal/8, 5326/normal/41, 5326/normal/43/a, 5326/normal/7 | 5326/normal/14, 5326/normal/15, 5326/normal/7, 5326/normal/8, 5326/normal/23 | BENIGN REORDERING |
| M10E-A / q008 | 5326/normal/15, 5326/normal/27, 5326/normal/28, 5326/normal/25, 5326/normal/16 | 5326/normal/15, 5326/normal/27, 5326/normal/25, 5326/normal/14, 5326/normal/24 | BENIGN REORDERING |
| M10E-A / q009 | 5326/normal/16, 5326/normal/27, 5326/normal/25, 5326/normal/28, 5326/normal/17 | 5326/normal/16, 5326/normal/27, 5326/normal/25, 5326/normal/28, 5326/normal/22 | BENIGN REORDERING |
| M10E-A / q010 | 5326/normal/17, 5326/normal/28, 5326/normal/27, 5326/normal/43/a, 5326/normal/20 | 5326/normal/17, 5326/normal/28, 5326/normal/41, 5326/normal/27, 5326/normal/16 | BENIGN REORDERING |
| M10E-A / q011 | 5326/normal/20, 5326/normal/21, 5326/normal/5, 5326/normal/27, 5326/normal/23 | 5326/normal/20, 5326/normal/21, 5326/normal/23, 5326/normal/15, 5326/normal/27 | BENIGN REORDERING |
| M10E-A / q012 | 5326/normal/21, 5326/normal/26, 5326/normal/27, 5326/normal/25, 5326/normal/28 | 5326/normal/21, 5326/normal/27, 5326/normal/26, 5326/normal/25, 5326/normal/20 | BENIGN REORDERING |
| M10E-A / q013 | 5326/normal/25, 5326/normal/27, 5326/normal/26, 5326/normal/28, 5326/normal/16 | 5326/normal/25, 5326/normal/27, 5326/normal/26, 5326/normal/28, 5326/normal/22 | BENIGN REORDERING |
| M10E-A / q014 | 5326/normal/17, 5326/normal/27, 5326/normal/28, 5326/gecici/3, 5326/normal/20 | 5326/normal/27, 5326/gecici/3, 5326/normal/21, 5326/normal/28, 5326/normal/17 | HYBRID RECOVERY |
| M10E-A / q015 | 5326/normal/32, 5326/normal/37, 5326/normal/41, 5326/normal/27, 5326/normal/28 | 5326/normal/32, 5326/normal/28, 5326/normal/12, 5326/normal/14, 5326/normal/42 | BENIGN REORDERING |
| M10E-A / q016 | 5326/normal/3, 5326/gecici/3, 5326/normal/15, 5326/normal/28, 5326/normal/1 | 5326/normal/1, 5326/normal/13, 5326/normal/17, 5326/normal/3, 5326/normal/41 | DENSE EVIDENCE DISPLACEMENT |
| M10E-A / q017 | 5326/normal/5, 5326/normal/7, 5326/normal/2, 5326/normal/14, 5326/normal/20 | 5326/normal/5, 5326/normal/7, 5326/normal/15, 5326/normal/14, 5326/normal/4 | BENIGN REORDERING |
| M10E-A / q018 | 5326/normal/7, 5326/normal/14, 5326/normal/2, 5326/normal/41, 5326/normal/15 | 5326/normal/7, 5326/normal/2, 5326/normal/15, 5326/normal/4, 5326/normal/14 | BENIGN REORDERING |
| M10E-A / q019 | 5326/normal/8, 5326/normal/27, 5326/normal/16, 5326/normal/15, 5326/normal/14 | 5326/normal/8, 5326/normal/15, 5326/normal/27, 5326/normal/24, 5326/normal/25 | BENIGN REORDERING |
| M10E-A / q020 | 5326/normal/5, 5326/normal/12, 5326/normal/28, 5326/normal/10, 5326/normal/20 | 5326/normal/10, 5326/normal/22, 5326/normal/14, 5326/normal/12, 5326/normal/5 | HYBRID RECOVERY |
| M10E-A / q021 | 5326/normal/18, 4458/normal/57, 5326/normal/14, 5326/normal/27, 4458/normal/180 | 5326/normal/18, 5326/normal/27, 4458/normal/237, 5326/normal/28, 4458/normal/231 | CROSS-LAW INTRUSION |
| M10E-A / q022 | 5326/normal/25, 5326/normal/26, 5326/normal/22, 5326/normal/27, 5326/normal/43/a | 5326/normal/26, 5326/normal/22, 5326/normal/23, 5326/normal/28, 5326/normal/27 | BENIGN REORDERING |
| M10E-A / q023 | 5326/normal/29, 5326/normal/27, 4458/normal/242, 5326/normal/26, 5326/normal/25 | 5326/normal/27, 5326/normal/26, 4458/normal/242, 5326/normal/29, 5326/normal/25 | HYBRID RECOVERY |
| M10E-A / q024 | 5326/normal/13, 5326/normal/14, 5326/normal/43/a, 5326/normal/41, 5326/normal/37 | 5326/normal/13, 5326/normal/14, 5326/normal/20, 5326/normal/43/c, 4458/normal/146 | CROSS-LAW INTRUSION |
| M10E-A / q025 | 5326/normal/43/a, 5326/normal/15, 5326/normal/27, 5326/normal/28, 5326/normal/14 | 5326/normal/15, 5326/normal/27, 5326/normal/23, 5326/normal/14, 5326/normal/28 | HYBRID RECOVERY |
| M10E-A / q026 | 5326/normal/17, 5326/normal/28, 4458/normal/242, 5326/normal/27, 5326/normal/29 | 5326/normal/17, 4458/normal/242, 5326/normal/27, 4458/normal/231, 5326/normal/20 | CROSS-LAW INTRUSION |
| M10E-A / q027 | 5326/normal/20, 5326/gecici/3, 5326/normal/21, 5326/normal/28, 5326/normal/27 | 5326/normal/20, 5326/normal/21, 5326/normal/17, 5326/normal/43/a, 5326/normal/23 | BENIGN REORDERING |
| M10E-A / q028 | 4458/normal/227, 5326/normal/27, 5326/normal/28, 4458/gecici/6, 4458/gecici/10 | 5326/normal/27, 5326/normal/21, 5326/normal/28, 4458/normal/242, 4458/normal/197 | HYBRID RECOVERY; CROSS-LAW INTRUSION |
| M10E-A / q029 | 5326/normal/30, 5326/normal/29, 5326/normal/31, 5326/normal/27, 5326/gecici/3 | 5326/normal/30, 5326/normal/27, 5326/normal/31, 5326/normal/26, 4458/normal/232 | CROSS-LAW INTRUSION |
| M10E-A / q030 | 5326/normal/39, 4458/normal/191, 5326/normal/43/c, 5326/normal/42, 4458/normal/232 | 5326/normal/39, 4458/normal/238, 4458/normal/55, 5326/normal/23, 4458/normal/191 | CROSS-LAW INTRUSION |
| M10E-A / q031 | 5326/normal/41, 5326/normal/36, 5326/normal/43/a, 5326/normal/32, 5326/normal/33 | 5326/normal/41, 5326/normal/37, 5326/normal/43/a, 5326/normal/17, 5326/normal/42/a | BENIGN REORDERING |
| M10E-A / q032 | 5326/normal/25, 5326/normal/27, 5326/normal/26, 5326/normal/28, 5326/normal/24 | 5326/normal/25, 5326/normal/26, 5326/normal/22, 5326/normal/23, 5326/normal/28 | HYBRID RECOVERY; MULTI-SOURCE COMPLETENESS GAIN |
| M10E-A / q033 | 5326/normal/27, 5326/normal/15, 5326/normal/20, 5326/normal/24, 5326/normal/28 | 5326/normal/27, 5326/normal/24, 5326/normal/20, 5326/normal/23, 5326/normal/28 | HYBRID RECOVERY; MULTI-SOURCE COMPLETENESS GAIN |
| M10E-A / q034 | 5326/normal/26, 5326/normal/27, 5326/normal/28, 5326/normal/29, 4458/normal/242 | 5326/normal/26, 5326/normal/27, 4458/normal/242, 5326/normal/28, 5326/normal/29 | BENIGN REORDERING |
| M10E-A / q035 | 5326/normal/17, 5326/normal/28, 5326/normal/27, 5326/normal/21, 5326/normal/43/a | 5326/normal/27, 5326/normal/17, 5326/normal/31, 5326/normal/28, 5326/normal/20 | HYBRID RECOVERY; DENSE EVIDENCE DISPLACEMENT; MULTI-SOURCE COMPLETENESS GAIN |
| M10E-A / q036 | 5326/normal/18, 5326/normal/21, 4458/normal/17, 4458/normal/64, 4458/normal/57 | 5326/normal/18, 5326/normal/21, 4458/normal/17, 4458/normal/231, 4458/gecici/9 | CROSS-LAW INTRUSION |
| M10E-A / q037 | 5326/normal/34, 5326/normal/33, 5326/normal/18, 5326/normal/27, 5326/normal/28 | 5326/normal/34, 5326/normal/33, 5326/normal/18, 5326/normal/21, 5326/normal/41 | BENIGN REORDERING |
| M10E-A / q038 | 5326/normal/42/a, 5326/normal/43/a, 5326/normal/15, 5326/normal/20, 5326/normal/17 | 5326/normal/42/a, 5326/normal/11, 5326/normal/28, 5326/normal/40, 5326/normal/14 | BENIGN REORDERING |
| M10E-A / q039 | 5326/normal/43/a, 5326/normal/37, 4458/normal/218/a, 5326/normal/14, 5326/normal/41 | 5326/normal/43/a, 5326/normal/28, 5326/normal/41, 5326/normal/33, 4458/normal/218/a | BENIGN REORDERING |
| M10E-A / q040 | 5326/normal/43/b, 5326/normal/43/a, 5326/normal/40, 5326/normal/37, 5326/normal/32 | 5326/normal/43/b, 5326/normal/26, 5326/normal/43/a, 5326/normal/42/a, 5326/normal/41 | BENIGN REORDERING |
| M10E-A / q041 | 5326/normal/43/c, 5326/normal/43, 5326/normal/11, 4458/normal/167, 5326/normal/41 | 5326/normal/43/c, 4458/gecici/6, 4458/normal/167, 5326/normal/19, 5326/normal/43 | CROSS-LAW INTRUSION |
| M10E-A / q042 | 5326/normal/7, 5326/normal/5, 5326/normal/1, 5326/normal/10, 5326/normal/2 | 5326/normal/4, 5326/normal/13, 5326/normal/16, 5326/normal/1, 5326/normal/22 | BENIGN REORDERING |
| M10E-A / q043 | 5326/normal/19, 5326/gecici/2, 5326/normal/13, 5326/normal/21, 5326/normal/30 | 5326/normal/19, 5326/normal/12, 5326/normal/16, 5326/normal/5, 5326/gecici/2 | BENIGN REORDERING |
| M10E-A / q044 | 5326/normal/28, 5326/normal/17, 5326/normal/43/a, 5326/normal/27, 4458/normal/233 | 5326/normal/28, 5326/normal/17, 5326/normal/43/a, 4458/normal/231, 5326/gecici/3 | CROSS-LAW INTRUSION |
| M10E-A / q045 | 5326/normal/28, 5326/normal/27, 5326/normal/29, 5326/gecici/3, 5326/normal/21 | 5326/normal/28, 5326/normal/29, 5326/normal/27, 5326/gecici/3, 5326/normal/26 | BENIGN REORDERING |
| M10E-A / gk001 | 4458/normal/210, 4458/normal/215, 4458/normal/216, 4458/normal/214, 4458/normal/168 | 4458/normal/215, 4458/normal/210, 4458/normal/216, 4458/normal/214, 4458/normal/211 | DENSE EVIDENCE DISPLACEMENT |
| M10E-A / gk002 | 4458/normal/111, 4458/normal/150, 4458/normal/123, 4458/normal/136, 4458/normal/135 | 4458/normal/150, 4458/normal/144, 4458/normal/135, 4458/normal/120, 4458/normal/141 | HYBRID RECOVERY |
| M10E-A / gk003 | 4458/normal/25, 4458/normal/26, 4458/normal/15, 4458/normal/114, 4458/normal/194 | 4458/normal/15, 4458/normal/25, 4458/normal/3, 5326/normal/31, 4458/normal/26 | HYBRID RECOVERY; CROSS-LAW INTRUSION |
| M10E-A / gk004 | 4458/normal/161, 4458/normal/74, 4458/normal/155, 4458/normal/160, 4458/normal/159 | 4458/normal/160, 4458/normal/163, 4458/normal/168, 4458/normal/161, 4458/normal/189 | HYBRID RECOVERY |
| M10E-A / gk005 | 4458/normal/84, 4458/normal/87, 4458/normal/51, 4458/normal/88, 4458/normal/85 | 4458/normal/84, 4458/normal/51, 4458/normal/88, 4458/normal/52, 4458/normal/83 | BENIGN REORDERING |
| M10E-A / gk006 | 4458/normal/172, 4458/normal/33, 4458/normal/153, 4458/normal/91, 4458/normal/10/a | 4458/normal/172, 4458/normal/74, 4458/normal/37, 4458/normal/139, 4458/normal/10 | BENIGN REORDERING |
| M10E-A / gk007 | 4458/normal/60, 4458/normal/71, 4458/normal/62, 4458/normal/65, 4458/normal/61 | 4458/normal/60, 4458/normal/71, 4458/normal/61, 4458/normal/165/b, 4458/normal/181 | BENIGN REORDERING |
| M10E-A / gk008 | 4458/normal/35/a, 4458/normal/165/a, 4458/normal/165/d, 4458/normal/35/b, 4458/normal/175 | 4458/normal/35/a, 4458/normal/165/a, 4458/normal/35/b, 4458/normal/165/d, 4458/normal/165/c | BENIGN REORDERING |
| M10E-A / gk009 | 4458/normal/5/a, 4458/normal/227, 4458/normal/228, 4458/normal/95, 4458/normal/229 | 4458/normal/5/a, 4458/normal/5, 4458/normal/62, 4458/normal/10, 4458/normal/181 | BENIGN REORDERING |
| M10E-A / gk010 | 4458/normal/24, 4458/normal/28, 4458/normal/27, 4458/normal/25, 4458/normal/236 | 4458/normal/24, 4458/normal/27, 4458/normal/28, 4458/normal/25, 4458/normal/26 | BENIGN REORDERING |
| M10E-A / gk011 | 4458/normal/9, 4458/normal/191/a, 4458/normal/198, 4458/normal/114, 4458/normal/181 | 4458/normal/9, 4458/normal/191/a, 4458/normal/198, 4458/normal/194, 4458/normal/114 | BENIGN REORDERING |
| M10E-A / gk012 | 4458/normal/167, 4458/normal/235, 4458/normal/167, 4458/normal/158, 4458/normal/56 | 4458/normal/167, 4458/normal/235, 4458/normal/109, 4458/normal/167, 4458/normal/57 | HYBRID RECOVERY |
| M10E-A / gk013 | 4458/normal/46, 4458/normal/50, 4458/normal/165/d, 4458/normal/35/a, 4458/normal/130 | 4458/normal/46, 4458/normal/35/a, 4458/normal/70, 4458/normal/237, 4458/normal/241 | BENIGN REORDERING |
| M10E-A / gk014 | 4458/normal/78, 4458/normal/161, 4458/normal/121, 4458/normal/158, 4458/normal/113 | 4458/normal/168, 4458/normal/142, 4458/normal/157, 4458/normal/115, 4458/normal/187 | BENIGN REORDERING |
| M10E-A / gk015 | 4458/normal/170, 4458/normal/146, 4458/normal/121, 4458/normal/142, 4458/normal/168 | 4458/normal/121, 4458/normal/168, 4458/normal/142, 4458/normal/186, 4458/normal/146 | HYBRID RECOVERY |
| M10E-A / gk016 | 4458/normal/191/a, 4458/normal/198, 4458/normal/114, 4458/normal/82, 4458/normal/126 | 4458/normal/191/a, 4458/normal/198, 4458/normal/114, 4458/normal/127, 4458/normal/184 | BENIGN REORDERING |
| M10E-A / gk017 | 4458/normal/24, 4458/normal/25, 4458/normal/27, 4458/normal/26, 4458/normal/28 | 4458/normal/24, 4458/normal/25, 4458/normal/27, 4458/normal/26, 4458/normal/104 | BENIGN REORDERING |
| M10E-A / gk018 | 4458/normal/35/a, 4458/normal/165/d, 4458/normal/35/b, 4458/normal/56, 4458/normal/62 | 4458/normal/35/a, 4458/normal/165/d, 4458/normal/35/b, 4458/normal/165/a, 4458/normal/237 | BENIGN REORDERING |
| M10E-A / gk019 | 4458/normal/133, 4458/normal/194, 4458/normal/135, 4458/normal/141, 4458/normal/168 | 4458/normal/133, 4458/normal/168, 4458/normal/184, 4458/normal/141, 4458/normal/134 | BENIGN REORDERING |
| M10E-A / gk020 | 5326/normal/28, 5326/normal/43/a, 5326/normal/15, 5326/normal/32, 5326/normal/41 | 5326/normal/32, 4458/normal/235, 5326/normal/41, 4458/normal/236, 5326/normal/15 | BENIGN REORDERING |
| M10E-A / gk021 | 4458/normal/165/a, 4458/normal/35/a, 4458/normal/165/b, 4458/normal/165/c, 4458/normal/62 | 4458/normal/165/a, 4458/normal/165/c, 4458/normal/165/b, 4458/normal/35/a, 4458/normal/35/c | HYBRID RECOVERY |
| M10E-A / gk022 | 4458/normal/5/a, 4458/normal/227, 4458/gecici/6, 4458/normal/228, 4458/gecici/5 | 4458/normal/5/a, 4458/gecici/6, 4458/islenemeyen_hukum/1, 4458/normal/10, 4458/normal/227 | HYBRID RECOVERY; MULTI-SOURCE COMPLETENESS GAIN |
| M10E-A / gk023 | 4458/normal/180, 4458/gecici/9, 4458/normal/235, 4458/normal/45, 4458/gecici/10 | 4458/gecici/9, 4458/normal/180, 4458/gecici/10, 4458/normal/39, 4458/normal/235 | HYBRID RECOVERY |
| M10E-A / gk024 | 4458/normal/202, 4458/normal/205, 4458/normal/60, 4458/normal/85, 4458/normal/225 | 4458/normal/202, 4458/normal/205, 4458/normal/60, 4458/normal/85, 4458/normal/56 | BENIGN REORDERING |
| M10E-A / gk025 | 4458/normal/230, 4458/normal/41, 4458/gecici/2, 4458/gecici/5, 4458/normal/76 | 4458/gecici/5, 4458/gecici/2, 4458/normal/82, 4458/normal/62, 4458/normal/230 | HYBRID RECOVERY |
| M10E-A / gk026 | 4458/gecici/6, 4458/gecici/6, 4458/normal/230, 4458/normal/227, 4458/normal/233 | 4458/gecici/6, 4458/gecici/6, 4458/normal/227, 4458/normal/226, 4458/normal/213 | BENIGN REORDERING |
| M10E-A / gk027 | 4458/normal/133, 4458/normal/119, 4458/normal/108, 4458/normal/194, 4458/normal/114 | 4458/normal/108, 4458/normal/119, 4458/normal/136, 4458/normal/121, 4458/normal/144 | HYBRID RECOVERY |
| M10E-A / gk028 | 5326/normal/43/a, 5326/normal/32, 5326/normal/17, 5326/normal/15, 5326/normal/28 | 5326/normal/32, 5326/normal/14, 5326/gecici/3, 4458/normal/238, 5326/normal/42 | CROSS-LAW INTRUSION |
| M10E-A / gk029 | 4458/gecici/1, 4458/normal/50, 4458/normal/46, 4458/normal/70, 4458/normal/69 | 4458/gecici/1, 4458/gecici/2, 4458/normal/66, 4458/normal/190, 4458/normal/50 | BENIGN REORDERING |
| M10E-A / gk030 | 4458/normal/9, 4458/normal/8, 4458/normal/214, 4458/normal/198, 4458/normal/196 | 4458/normal/9, 4458/normal/35/c, 4458/normal/114, 4458/normal/195, 4458/normal/8 | BENIGN REORDERING |
| M10E-B / h5326-01 | 5326/normal/1, 5326/normal/4, 5326/normal/7, 5326/normal/5, 5326/normal/3 | 5326/normal/1, 5326/normal/4, 5326/normal/5, 5326/normal/3, 5326/normal/6 | BENIGN REORDERING |
| M10E-B / h5326-02 | 5326/normal/35, 5326/normal/43/a, 5326/normal/37, 5326/normal/41, 5326/normal/36 | 5326/normal/35, 5326/normal/41, 5326/normal/36, 5326/normal/20, 5326/normal/43/a | BENIGN REORDERING |
| M10E-B / h5326-03 | 5326/normal/36, 5326/normal/43/a, 5326/normal/41, 5326/normal/38, 4458/normal/238 | 5326/normal/36, 5326/normal/43/a, 4458/normal/231, 5326/normal/41, 4458/normal/234 | CROSS-LAW INTRUSION |
| M10E-B / h5326-04 | 5326/normal/37, 4458/normal/234, 4458/normal/236, 5326/normal/38, 4458/normal/179 | 5326/normal/37, 5326/normal/38, 4458/normal/24, 5326/normal/8, 4458/normal/234 | CROSS-LAW INTRUSION |
| M10E-B / h5326-05 | 5326/normal/38, 4458/normal/234, 5326/normal/41, 4458/normal/235, 4458/normal/236 | 5326/normal/38, 5326/normal/41, 4458/gecici/6, 5326/normal/37, 5326/normal/39 | CROSS-LAW INTRUSION |
| M10E-B / h5326-06 | 5326/normal/40, 5326/normal/43/b, 4458/normal/21, 5326/normal/25, 4458/gecici/6 | 5326/normal/40, 5326/normal/25, 4458/normal/13, 4458/normal/77, 5326/normal/43/b | CROSS-LAW INTRUSION |
| M10E-B / h5326-07 | 5326/normal/42, 5326/normal/38, 5326/normal/41, 5326/normal/21, 5326/normal/20 | 5326/normal/42, 5326/normal/20, 5326/normal/42/a, 4458/normal/235, 4458/normal/235 | CROSS-LAW INTRUSION |
| M10E-B / h5326-08 | 5326/normal/43, 5326/normal/43/c, 5326/normal/38, 5326/normal/19, 5326/normal/37 | 5326/normal/43, 5326/normal/42/a, 4458/normal/182, 5326/normal/43/c, 4458/normal/233 | CROSS-LAW INTRUSION |
| M10E-B / h5326-09 | 5326/gecici/1, 5326/normal/33, 4458/normal/30, 5326/normal/21, 5326/normal/42 | 5326/gecici/1, 5326/normal/21, 5326/normal/36, 5326/normal/41, 5326/normal/37 | BENIGN REORDERING |
| M10E-B / h5326-10 | 5326/gecici/2, 5326/gecici/3, 5326/normal/5, 5326/normal/27, 5326/normal/21 | 5326/gecici/3, 5326/normal/27, 5326/gecici/2, 5326/normal/20, 5326/normal/26 | HYBRID RECOVERY; DENSE EVIDENCE DISPLACEMENT |
| M10E-B / h4458-01 | 4458/normal/2, 4458/normal/37, 4458/normal/33, 4458/normal/152, 4458/normal/165/a | 4458/normal/2, 4458/normal/37, 4458/normal/165/a, 4458/normal/39, 4458/normal/172 | BENIGN REORDERING |
| M10E-B / h4458-02 | 4458/normal/33, 4458/normal/153, 4458/normal/74, 4458/normal/35, 4458/normal/37 | 4458/normal/33, 4458/normal/35, 4458/normal/153, 4458/normal/74, 4458/normal/173 | BENIGN REORDERING |
| M10E-B / h4458-03 | 4458/normal/56, 4458/normal/241, 4458/normal/128, 4458/normal/135, 4458/normal/186 | 4458/normal/241, 4458/normal/128, 4458/normal/129, 4458/gecici/11, 4458/normal/194 | BENIGN REORDERING |
| M10E-B / h4458-04 | 4458/normal/152, 4458/normal/2, 4458/normal/37, 4458/normal/159, 4458/normal/161 | 4458/normal/152, 4458/normal/159, 4458/normal/160, 4458/normal/37, 4458/normal/172 | BENIGN REORDERING |
| M10E-B / h4458-05 | 4458/normal/25, 4458/normal/26, 4458/normal/1, 4458/normal/23, 4458/normal/200 | 4458/normal/23, 4458/normal/25, 4458/normal/3, 4458/normal/26, 4458/normal/24 | HYBRID RECOVERY |
| M10E-B / h4458-06 | 4458/normal/218, 4458/normal/10/a, 4458/normal/35, 4458/normal/10, 4458/normal/225 | 4458/normal/218, 4458/normal/10, 4458/normal/80, 4458/normal/4, 4458/normal/5/a | BENIGN REORDERING |
| M10E-B / h4458-07 | 4458/normal/32, 4458/normal/114, 4458/normal/104, 4458/normal/115, 4458/normal/236 | 4458/normal/32, 4458/normal/104, 4458/normal/234, 4458/normal/76, 4458/normal/194 | BENIGN REORDERING |
| M10E-B / h4458-08 | 4458/normal/96, 4458/normal/157, 4458/normal/100, 4458/normal/163, 4458/normal/93 | 4458/normal/93, 4458/normal/163, 4458/normal/107, 4458/normal/104, 4458/normal/157 | HYBRID RECOVERY |
| M10E-B / h4458-09 | 4458/normal/226, 4458/normal/229, 4458/normal/227, 4458/normal/230, 4458/normal/5 | 4458/normal/226, 4458/normal/227, 4458/normal/229, 4458/normal/228, 4458/gecici/6 | BENIGN REORDERING |
| M10E-B / h4458-10 | 4458/normal/35, 4458/normal/33, 4458/normal/92, 4458/normal/10, 4458/normal/5/a | 4458/normal/35, 4458/normal/38, 4458/normal/153, 4458/normal/33, 4458/normal/211 | HYBRID RECOVERY |
| M10E-B / h4458-11 | 4458/normal/199, 4458/normal/61, 4458/normal/213, 4458/normal/198, 4458/normal/70 | 4458/normal/199, 4458/normal/70, 4458/normal/198, 4458/normal/69, 4458/normal/71 | BENIGN REORDERING |
| M10E-B / h4458-12 | 4458/normal/168, 4458/normal/170, 4458/normal/143, 4458/normal/169, 4458/normal/104 | 4458/normal/168, 4458/normal/170, 4458/normal/169, 4458/normal/194, 4458/normal/78 | HYBRID RECOVERY |
| M10E-B / h4458-13 | 4458/normal/74, 4458/normal/161, 4458/normal/101, 4458/normal/155, 4458/normal/104 | 4458/normal/161, 4458/normal/101, 4458/normal/104, 4458/normal/182, 4458/normal/152 | BENIGN REORDERING |
| M10E-B / h4458-14 | 4458/normal/193, 4458/normal/188, 4458/normal/189, 4458/normal/194, 4458/normal/181 | 4458/normal/193, 4458/normal/30, 4458/normal/235, 4458/normal/76, 4458/normal/188 | DENSE EVIDENCE DISPLACEMENT; MULTI-SOURCE COMPLETENESS LOSS |
| M10E-B / h4458-15 | 4458/normal/216, 4458/normal/211, 4458/normal/212, 4458/normal/199, 4458/normal/197 | 4458/normal/211, 4458/normal/216, 4458/normal/212, 4458/gecici/10, 4458/normal/210 | HYBRID RECOVERY |
| M10E-B / h4458-16 | 4458/normal/243, 4458/normal/242, 4458/normal/232, 4458/normal/231, 4458/normal/197 | 4458/normal/243, 4458/normal/242, 4458/normal/231, 4458/normal/232, 4458/normal/244 | BENIGN REORDERING |
| M10E-B / h4458-17 | 4458/normal/220, 4458/normal/35, 4458/normal/224, 4458/normal/221, 4458/normal/14 | 4458/normal/220, 4458/normal/35, 4458/normal/221, 4458/normal/224, 4458/normal/14 | BENIGN REORDERING |
| M10E-B / h4458-18 | 4458/normal/230, 4458/normal/13, 4458/normal/196, 4458/normal/50, 4458/normal/229 | 4458/normal/13, 4458/normal/196, 4458/normal/62, 4458/gecici/6, 4458/normal/229 | DENSE EVIDENCE DISPLACEMENT |
| M10E-B / h4458-19 | 4458/normal/192, 4458/normal/232, 4458/normal/234, 4458/normal/211, 4458/normal/216 | 4458/normal/192, 4458/normal/232, 4458/normal/229, 4458/normal/75, 4458/normal/3 | BENIGN REORDERING |
| M10E-B / h4458-20 | 4458/normal/78, 4458/normal/161, 4458/normal/104, 4458/normal/53, 4458/normal/235 | 4458/normal/78, 4458/normal/164, 4458/normal/213, 4458/normal/235, 4458/normal/235 | HYBRID RECOVERY |

## 11. Input provenance

- `m10e-retrieval-experiments.json`: SHA-256 `a2d5850c08e6b2f579e0cf268f7202497df9fc02c8b88bd0b8a7ff4d255510d3`.
- `m10e-holdout-b0-vs-b2.json`: SHA-256 `efb99395894c1ef0cc053d1e9e8d81e73b187fd149ce6c75059975e3b4fa6030`.

## 12. Verification and working-tree boundary before closure

- `RUN_OPENAI_INTEGRATION_TESTS=0 python -m pytest -q`: **456 passed, 2 skipped**
  (448 baseline passes plus eight new offline tests).
- `git diff --check`: passed. New artifacts were also checked for trailing whitespace.
- Deterministic replay output equality, all 420 CSV question/strategy rows,
  and all 108 Markdown metric rows were checked against the structured JSON.
- No tracked file has changed. Both frozen question files, all M10E-A/M10E-B
  artifacts, production behavior files, central configuration and frozen B2
  implementation remain unchanged. Frozen holdout SHA-256 was rechecked.
- Five new, untracked files only: this Markdown report, its diagnostic JSON
  and CSV companions, `src/m10e_failure_analysis.py`, and
  `tests/test_m10e_failure_analysis.py`. Nothing staged or committed.
- HEAD remains `5f33c56d59be923d232012d493ccd8f0077a8e69`. No new holdout,
  OpenAI request or Chroma access occurred. M10E-B remains **NOT VALIDATED**.

## 13. Accepted final decision

**NO NEW RETRIEVAL CANDIDATE SELECTED.**

- B2 remains NOT VALIDATED.
- C1 dense-anchor is not selected.
- C2 dense/B2 alternation is not selected.
- No third candidate was invented.
- No parameter tuning occurred.
- No future production adoption is authorized from M10E-C.

C1 protects dense rank-1 and restores h4458-18 but does not restore
h4458-14 multi-source completeness.

C2 restores h4458-14 and h4458-18 but loses useful B2 recoveries such as
gk012 and h4458-08 and loses q033 completeness improvement.

Therefore: `selected_candidate = null`.

Closure authorizes committing only the five M10E-C files listed above;
the pre-closure working-tree observations in section 12 are historical.
