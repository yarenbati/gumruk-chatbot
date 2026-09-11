# M12F Retrieval Optimization Closure

## Executive Summary

M12F investigated persistent three-source dense retrieval failures across the accepted 105-question development benchmark. The work identified two distinct failure modes: cross-document competition and within-document provision selection.

M12F-A through M12F-E2 produced enough evidence to separate those layers. The LLM question-only router was promising for document classification, but its retrieval integration was mixed: R1 improved some document targeting while regressing source coverage, and R2 returned to B0-level coverage without paired gains.

M12F is now closed. Production retrieval is unchanged, no M12F candidate was adopted, and the next milestone is M13A — Gümrük Yönetmeliği Official Source Admission + Structure Audit.

## Starting Problem

The existing dense retrieval path used the raw user question with `text-embedding-3-small`, a shared Chroma collection, L2 distance, and `TOP_K=5`. Persistent failures included questions whose expected provisions were absent from the global top results, especially in the 5607 corpus.

The investigation asked whether those failures came from candidate-pool size, document discrimination, query enrichment, or provision-level representation and selection.

## Experiments and Outcomes

### M12F-A

**Explicit-Law Signal Experiment**
Commit: `ab9969ac7f6cb05e33a25e2e04e9431133073a8f`

Only 6 of 105 questions explicitly named a supported law. The signal therefore had too little scope. Title enrichment and filtering did not provide a robust general solution.

**Conclusion:** No candidate selected. No production adoption.

### M12F-B

**Candidate Pool Completeness Diagnostic**
Commit: `55100c5d6830eb51a45c85ab167af534e6e8b5c2`

The primary 5607 failures were not caused by Top5 being too small. For persistent failures, expected sources were often absent even from Top50. The primary 5607 group was classified as CATEGORY 3 — representation/discrimination problem; the full benchmark was CATEGORY 2 — mixed.

**Conclusion:** Larger candidate pools were not selected as the solution.

### M12F-C

**Oracle Retrieval Decomposition**
Commit: `289dd59c74e2eb22193e936bdd4d16aadbc2e8b9`

Gold document identity was used diagnostically only.

- `k5607-003`: G0 Madde 3 `>50`; oracle raw 5607-only rank `2/46`.
- `k5607-004`: G0 Madde 3 `>50`; oracle raw 5607-only rank `2/46`.

These cases strongly exhibited document discrimination.

The decomposition also showed a second failure mode:

- `k5607-026`: Madde 3 `11/46`.
- `k5607-029`: Madde 3 `16/46`.
- `k5607-025`: partially incomplete after document restriction.

Thus correct document restriction did not guarantee correct provision selection. Simple title enrichment was rejected as a general strategy: 5 required-source pairs improved, 19 were unchanged, and 12 regressed. Oracle filtering remained diagnostic only and was not considered deployable.

### M12F-D

**Centroid Document Router**
Commit: `05fecc99973c0d81fd84d777f3298ffd51126ed3`

The fixed unsupervised centroid router achieved 88/105 overall Top1 accuracy (83.81%) and 18/30 5607 Top1 accuracy (60.00%). All six critical 5607 cases ranked 4458 first and 5607 second.

R1 hard routing caused retrieval regressions. R2 Top2 routing limited the damage but produced no paired retrieval gain.

**Conclusion:** Centroid router not sufficient and rejected.

### M12F-E

**LLM Question-Only Document Router**
Commit: `65155481f29f5648156e9925c602edf67f34cec8`

This was classification-only; no retrieval was performed. The model was `gpt-5.6-terra`.

- Overall Top1: 100/105 (95.24%).
- Overall Top2: 105/105 (100%).
- Implicit Top1: 94/99 (94.95%).
- 5607 Top1: 27/30 (90.00%).
- LLM-only corrections versus centroid-only corrections: 15 versus 3.

All six critical 5607 cases ranked 5607 first.

**Conclusion:** LLM document classification was a promising development signal, but classification success alone was insufficient for adoption.

### M12F-E2

**LLM Router Retrieval Integration**
Commit: `6579512ec5559faddafa2e6e3dac826f1b3b1b7a`

Saved M12F-E predictions were reused. No new LLM router calls were made. R1 used the saved LLM Top1 document; R2 used the saved LLM Top2 documents.

At Top5:

| Variant | Source ANY | Source ALL |
|---|---:|---:|
| B0 | 92/105 | 87/105 |
| R1 | 93/105 | 85/105 |
| R2 | 92/105 | 87/105 |

Document Hit was 98/105 for B0, 105/105 for R1, and 98/105 for R2.

R1 paired Source ANY had 5 improvements, 96 unchanged questions, and 4 regressions. The improvements were `gk020`, `k5607-003`, `k5607-004`, `k5607-025`, and `k5607-026`; regressions were `q040`, `k5607-010`, `k5607-014`, and `k5607-028`.

R1 paired Source ALL had 2 improvements (`k5607-003`, `k5607-004`), 99 unchanged questions, and 4 regressions. R2 had zero paired improvements, zero regressions, and 105 unchanged questions for Source ANY, Source ALL, and Document Hit.

The primary cases showed:

- `k5607-003`: Madde 3 recovered at R1 rank 4.
- `k5607-004`: Madde 3 recovered at R1 rank 2.
- `k5607-025`: only Madde 3 recovered.
- `k5607-026`: only Madde 5 recovered.
- `k5607-029`: Geçici Madde 10 recovered, but Madde 3 remained missing.

**Conclusion:** Routed retrieval was mixed. R1 validated the document-discrimination diagnosis for 003/004, but did not produce a clean source-retrieval gain. R2 was safer but returned to B0-level coverage without paired gains.

## Final Failure Model

M12F identified two distinct retrieval failure modes. They must not be collapsed into a generic conclusion that retrieval is simply poor.

### Document Discrimination

The raw dense query can represent the correct provision reasonably well while another document dominates global retrieval. `k5607-003` and `k5607-004` are strong examples: both had global Madde 3 ranks beyond 50 and oracle raw 5607-only rank 2/46. LLM routing followed by R1 recovered them at ranks 4 and 2.

### Within-Document Provision Selection

Even when the correct document is known or restricted, the correct provision can rank too low. `k5607-026` Madde 3 ranked 11/46 under oracle restriction, and `k5607-029` Madde 3 ranked 16/46. `k5607-025` remained partially incomplete. These results establish a separate provision-selection problem.

## Rejected / Non-Adopted Approaches

M12F did not adopt:

- explicit-law routing or filtering;
- larger-K retrieval as the solution;
- title enrichment as a general strategy;
- oracle document filtering as deployable retrieval;
- centroid routing;
- LLM routing;
- hybrid, BM25, RRF, or B2 candidates;
- any production routing implementation.

The LLM question-only router remains a promising development signal for document classification. Its retrieval integration did not demonstrate a sufficiently clean net source-retrieval gain, so it is not a production candidate at closure.

## Production Decision

Production retrieval remains the existing dense retrieval architecture:

```text
raw user question
-> text-embedding-3-small
-> shared Chroma collection
-> dense L2 retrieval
-> TOP_K=5
-> generation/citation pipeline
```

M12F did not change production retrieval. No centroid router, LLM router, title enrichment, larger-K retrieval, oracle filter, or hybrid candidate was adopted.

## Development Benchmark and Holdout Policy

The 105-question benchmark has been repeatedly used for M12 development analysis and must now be treated as DEVELOPMENT-INFORMED.

Any future candidate informed by M12D, M12E, M12F-A, M12F-B, M12F-C, M12F-D, M12F-E, or M12F-E2 requires a NEW UNSEEN HOLDOUT before production adoption. The current 105 questions must not be reused as proof of final production quality.

## Deferred Research

No provision-selection work is started or selected in this closure. Future research may investigate provision/fıkra-aware representation, article-level versus fıkra-level retrieval, representations for long composite provisions, two-stage document-to-provision retrieval, and query/provision semantic representation.

None of these approaches has been proven or implemented by M12F.

## Why M12F Stops Here

M12F produced enough evidence to identify the dominant failure layers. Additional router iteration on the same development benchmark risks overfitting to the known 105 questions. No M12F-G or M12F-H is opened. The project now returns to corpus expansion.

## Next Milestone — M13 Gümrük Yönetmeliği

The next milestone is **M13 — Gümrük Yönetmeliği Onboarding**.

The first step is **M13A — Official Source Admission + Structure Audit**, which will admit the official source, establish provenance, determine document structure, count articles, temporary articles, sections, and annex-related structures, identify tables, footnotes, amendment history, and parser risks, and assess compatibility with the current ingestion, parser, and chunker architecture.

M13A is not started during this closure.

## Final Status

**M12F CLOSED**

- Production retrieval unchanged.
- No M12F candidate adopted.
- The LLM router is promising for classification but not production-ready.
- The two confirmed failure modes are document discrimination and within-document provision selection.
- Next milestone: **M13A — Gümrük Yönetmeliği Official Source Admission + Structure Audit**.
