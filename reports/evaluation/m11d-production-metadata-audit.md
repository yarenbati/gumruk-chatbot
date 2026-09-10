# M11D-A production metadata audit

Result: **PASS**

Production path: `C:\gumruk-chatbot\chroma`
Fresh copy: `C:\gumruk-chatbot\logs\.m11d_metadata_audit_chroma_622e3985cb1740caaf880a01e9b9822d`

Production Chroma was never opened. Every production file was enumerated and SHA-256 hashed,
copied to a fresh ignored directory, and verified byte-for-byte before opening only the copy.
No OpenAI, network, retrieval query, mutation API, reindex, or embedding recomputation was used.
Public collection mutation/query APIs and client mutation APIs were blocked during inspection.

Production pre/post hashes equal: **True**.
Copy verified before opening: **True**.
Copy physical hashes unchanged after client close: **False**.
Physical changes in the copy are reported separately from logical equality; no byte stability is inferred from API usage.

## Logical findings

Collection: `gumruk_mevzuati`; before/after count: 329/329.
IDs, text, metadata, and stored-vector snapshots unchanged: **True**.
Stored embeddings are available for 329 records at 1536 dimensions; only hashes/dimensions are reported.

| Document ID | Records |
|---|---:|
| 4458_gumruk_kanunu | 276 |
| 5326_kabahatler_kanunu | 53 |

| Field | Present | Missing | Valid | Invalid |
|---|---:|---:|---:|---:|
| document_id | 329 | 0 | 329 | 0 |
| legislation_number | 329 | 0 | 329 | 0 |
| article_type | 329 | 0 | 329 | 0 |
| article_no | 329 | 0 | 329 | 0 |
| article_id | 329 | 0 | 329 | 0 |

Canonical field validity uses the unchanged M11 identity validators. Article ID and legislation-number field validity means nonempty string; law numbers are additionally checked against the registry.
Valid canonical keys: 329. Unique provision keys: 324.
Affected records: 0. Individual findings: `[]`.
All current records resolve through the manifest; no missing, unknown, or third document IDs were found.
All supplied law numbers/source files agree with their manifest records. Current storage-ID prefixes agree with document provenance; prefixes were never used to infer identity.
Record IDs unique: True; no record ID maps to conflicting provenance.

Multi-chunk provisions: 5; maximum chunks per provision: 2. These are legitimate shared provision identities, not collisions.

| Canonical source key | Chroma record IDs |
|---|---|
| 4458_gumruk_kanunu/gecici/6 | 4458-gecici-madde-6-chunk-001, 4458-gecici-madde-6-chunk-002 |
| 4458_gumruk_kanunu/normal/167 | 4458-madde-167-chunk-001, 4458-madde-167-chunk-002 |
| 4458_gumruk_kanunu/normal/235 | 4458-madde-235-chunk-001, 4458-madde-235-chunk-002 |
| 4458_gumruk_kanunu/normal/241 | 4458-madde-241-chunk-001, 4458-madde-241-chunk-002 |
| 4458_gumruk_kanunu/normal/3 | 4458-madde-3-chunk-001, 4458-madde-3-chunk-002 |

## Decision

The current collection satisfies strict M11C-B citation provenance without metadata migration. No reindex or re-embedding is required for this identity contract. No repair was performed. This does not evaluate retrieval relevance or legal correctness.

## Physical file hashes

| Production file | Pre SHA-256 | Post SHA-256 |
|---|---|---|
| 448e5756-391d-4ede-87e8-7792e286ce3b/data_level0.bin | d4c2b22fe82c96e0e95d8e04e6a001e4ab6389d2e9b3fd1203ed948a1b9c3276 | d4c2b22fe82c96e0e95d8e04e6a001e4ab6389d2e9b3fd1203ed948a1b9c3276 |
| 448e5756-391d-4ede-87e8-7792e286ce3b/header.bin | b081be2c2276a57e995075c7de2f3cb25e903798aac36d98042045533ab28f7d | b081be2c2276a57e995075c7de2f3cb25e903798aac36d98042045533ab28f7d |
| 448e5756-391d-4ede-87e8-7792e286ce3b/length.bin | dce69fe0b66190d79c7847d28c6e2b9795abe6f8d5758e2715e9f409349f7809 | dce69fe0b66190d79c7847d28c6e2b9795abe6f8d5758e2715e9f409349f7809 |
| 448e5756-391d-4ede-87e8-7792e286ce3b/link_lists.bin | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| chroma.sqlite3 | e758c270221cb128f3df0fb08d2301733148450d7d73c98595281f02f3f7988c | e758c270221cb128f3df0fb08d2301733148450d7d73c98595281f02f3f7988c |

The verified copy started with these exact hashes. Copy files whose hashes changed after close:

- `448e5756-391d-4ede-87e8-7792e286ce3b/data_level0.bin`: `d4c2b22fe82c96e0e95d8e04e6a001e4ab6389d2e9b3fd1203ed948a1b9c3276` -> `63c5ccc74f1b1825afdb47c80ec24bec6f7f93241fd54b2d35952bf9595ab48a`
- `448e5756-391d-4ede-87e8-7792e286ce3b/length.bin`: `dce69fe0b66190d79c7847d28c6e2b9795abe6f8d5758e2715e9f409349f7809` -> `fa54a084027ac96328b1bcfed7e649e1016cf6fa8d86567535f95af320b8c9b5`
- `chroma.sqlite3`: `e758c270221cb128f3df0fb08d2301733148450d7d73c98595281f02f3f7988c` -> `5a1f43c9e989bc3251b693f87a78de5b20bdad410d1cffe0bd679ed639e8a5bf`

The companion JSON contains every record ID and audited metadata, exact before/after ID lists, logical SHA-256 digests, and all copy/production file hashes. Logical digests use canonical JSON in sorted-record-ID order; no text or embedding vectors are included.
