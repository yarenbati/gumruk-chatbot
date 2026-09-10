# M10E-B Blind Holdout: B0 vs B2

Frozen holdout SHA-256: `6c38c04ef73cc8aee755e5e97c748b6b141ad55da888f9fde5a2af51ad17af48`
Git commit: `fa75f48cad1de9a1cc5a1a3ca1ca75f4ac783946`
Experimental copy: `C:\gumruk-chatbot\.m10e_holdout_chroma_retry1`

## Attempt history

- Execution attempts total: **2**
  - Attempt 1: `failed_infrastructure` — 30 dense calls, failed at report serialization (write_json_report) - AFTER all 30 dense/scoring operations completed (TypeError: Object of type set is not JSON serializable); results_persisted=False, results_inspected=False
- Attempt 2 (this run): `completed` — 30 dense calls — **valid benchmark attempt**
- Total dense calls across all attempts: **60**
- Valid-run dense calls (this attempt only): **30**

## Combined / per-law summary

| Metric | B0 5326 | B2 5326 | B0 4458 | B2 4458 | B0 combined | B2 combined |
|---|---|---|---|---|---|---|
| ANY@1 | 100.0% | 100.0% | 55.0% | 60.0% | 70.0% | 73.3% |
| ANY@3 | 100.0% | 100.0% | 75.0% | 90.0% | 83.3% | 93.3% |
| ANY@5 | 100.0% | 100.0% | 85.0% | 95.0% | 90.0% | 96.7% |
| ALL@1 | 90.0% | 90.0% | 50.0% | 50.0% | 63.3% | 63.3% |
| ALL@3 | 100.0% | 100.0% | 70.0% | 85.0% | 80.0% | 90.0% |
| ALL@5 | 100.0% | 100.0% | 80.0% | 85.0% | 86.7% | 90.0% |
| Legislation Hit@1 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| Legislation Hit@3 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| Legislation Hit@5 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |

## Success gates

- **A_5326_preservation**: PASS — `{"any_at_5": {"b0": 10, "b2": 10}, "all_at_5": {"b0": 10, "b2": 10}}`
- **B_4458_improves_without_material_degradation**: PASS — `{"any_at_5": {"b0": 17, "b2": 19}, "all_at_5": {"b0": 16, "b2": 17}}`
- **C_combined_all_at_5**: PASS — `{"all_at_5": {"b0": 26, "b2": 27}}`
- **D_legislation_hit_at_1**: PASS — `{"legislation_hit_at_1": {"b0": 30, "b2": 30}}`
- **E_multi_source_all_at_5**: FAIL — `{"multi_source_count": 5, "all_at_5": {"b0": 4, "b2": 3}}`
- **F_deterministic_no_generation**: PASS — `{}`

## Final decision: **NOT VALIDATED**

B2 demonstrates useful hybrid-retrieval signal but is NOT approved as a
production replacement in its current form. M10F production adoption is
therefore blocked. Gate E remains FAIL under its original predeclared rule;
it has not been reinterpreted or weakened after observing the results.

## Closure record

The frozen holdout contains **30 questions: 10 × 5326 and 20 × 4458**, with
**35 distinct QualifiedSourceKeys** and **DEV gold overlap = 0**.

Attempt 1 was an **invalid benchmark attempt**: 30 real dense/API calls
completed retrieval/scoring before an infrastructure failure in JSON report
serialization. Its results were not persisted and were not inspected.
Attempt 2 was the **explicitly authorized replacement**, completed successfully
with 30 real dense/API calls, and is the **ONLY valid benchmark result**.
The total across both attempts is **60 real dense/API calls**; the valid
benchmark accounts for **30** of those calls and **1,556 embedding tokens**.

Additional final metrics (B0 → B2):

| Metric | B0 | B2 |
|---|---|---|
| Average non-expected-legislation share@5 | 6.7% | 7.3% |
| Multi-source ALL@5 | 80.0% | 60.0% |

Top-5 regressions are **h4458-18** (ANY and ALL) and **h4458-14**
(ALL multi-source regression). Top-5 recoveries are **h4458-08**,
**h4458-10**, and **h4458-20** (ANY and ALL).

## Holdout status going forward

The M10E-B holdout has now been observed. If its failures/results are used
to design a future retrieval strategy, this 30-question set becomes
development/diagnostic data for that strategy and cannot serve as its blind
validation set. Any future candidate derived using these results requires
a **NEW unseen holdout** before production adoption.

M10E-B is closed as **NOT VALIDATED**. Production retrieval remains unchanged.
