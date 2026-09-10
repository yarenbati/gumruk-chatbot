# M11A — Document-centered source identity audit and design

Status: **M11 implemented; closure audit complete with documentation update**.
Final implementation HEAD: `ff93ad5a50b6ef1369d42c09d2cc534649a8c4e6`.
No storage migration was needed or performed. The original M11A audit below was against HEAD
`00dc862d9803a16c9b5619ba8167081dcb911c57`.
M10E-C is closed with `selected_candidate = null`; B2 remains NOT VALIDATED.
Production retrieval remains the existing dense implementation.

## Final M11 state (supersedes planned-status statements below)

Sections 1–14 and Appendix A preserve the original M11A evidence, design and
line inventory at its stated HEAD. Their references to missing citation fields,
unverified storage, future implementation and test plans are historical, not
descriptions of the completed system. M11A itself did not inspect Chroma;
M11D-A later inspected only a verified copy under separate authorization.

| Milestone | Implemented outcome |
|---|---|
| M11A | Original identity audit/design retained below |
| M11B | `source_identity.DocumentSourceKey`: frozen canonical document/type/normalized-number value, deterministic serialization, explicit reviewed legacy registry/adapter |
| M11C-A | `SourceRegistry`/immutable `DocumentRecord`, explicit manifest loading, strict paragraph-root admission, pure Article/Chunk/RetrievedChunk key views |
| M11C-B | Strict production citation builder, injected registry, typed citation provenance and canonical-string UI serialization |
| M11D-A | Persisted production-copy metadata audit PASS; no metadata migration, vector reindex or re-embedding required |
| M11C-C | Separate pure `evaluate_documents` layer, `document-source-v1` schema and legacy parity tests; no new benchmark |

### Boundary-by-boundary closure audit

| Boundary | Canonical fields | Descriptive/storage fields and fallback/failure behavior |
|---|---|---|
| Manifest → SourceRegistry | Validated unique `document_id` | Title/type/local_file required; legislation number optional. Explicit loading rejects malformed/duplicate JSON fields, duplicate IDs/files and ambiguous supplied numbers. No import-time I/O or identity guessing. |
| Paragraph root → admission | Root `document_id` must equal the record resolved once by `source_file` | Missing/unregistered/mismatched root fails closed. Number comes from that same record. Older ingestion alone still uses a first matching file entry or emits no ID; it is not the trusted admission boundary. |
| Admission → Article → Chunk | Admitted ID copied unchanged; `article_type`/raw `article_no` preserved | Number is optional. Lower-level pure constructors/parser remain permissive; canonical helper access validates and fails on missing/invalid fields. Storage IDs are not canonical source keys. |
| Chunk → Chroma metadata | `document_id`, `article_type`, `article_no` transported | Generic index builder omits None values, retains article ID and descriptive/section provenance. It is not a strict admission gate. Chroma record ID remains chunk ID. No storage migration occurred. |
| Chroma → RetrievedChunk | Metadata transported unchanged | Rank, chunk ID, text and distance preserved. Retrieval itself does not validate canonical identity or substitute a law number. |
| RetrievedChunk → DocumentSourceKey | Exact document ID/type plus normalized article number | Pure key helper rejects missing/malformed identity. No title, law-number, record-prefix or model-prose fallback; manifest existence is checked separately. |
| Key → ValidatedCitation | Typed canonical key and matching document ID | `run_rag` injects a registry or loads it once for nonempty context. Strict generation validates all context provenance before the model call, resolves title/type by document ID, checks supplied law number and source_file consistency. Errors fail closed; model labels only select admitted context positions. |
| Citation → SerializedCitation | Document ID and canonical key string | Title/type, nullable number, article fields and source label/display are JSON-safe. No Python key object or persistent Python hash is exposed. Serialization trusts an already validated citation; it does not re-admit metadata. |
| SerializedCitation → UI | Machine fields remain distinct from display | App renders the prepared display. Current canonical display uses trusted document title plus type-sensitive article label; optional article title is appended. Numberless display requires no fabricated law number. UI does not parse model prose to establish provenance. |

Document identity, provision identity, canonical key, descriptive legal metadata,
human display, historical QualifiedSourceKey, and article/chunk/record storage
IDs remain distinct. `normal`, `ek`, `gecici`, `islenemeyen_hukum` are the four
accepted machine namespaces; the last retains the existing Geçici Madde display
and is not a newly invented legal category.

Strictness lives in the active builder, not every historical dataclass constructor.
Manual `ValidatedCitation` instances may have all document fields absent. An
explicit `legacy_citations=True` builder option preserves historical unit callers;
the default production RAG path does not select it or silently fall back to it.
RAG checks source number/context position and chunk membership for all citations,
and canonical key/document/provision agreement when document provenance is present.
Legacy conversion uses only the reviewed 5326/4458 registry; unknown mappings fail.

### Storage, retrieval and evaluation evidence

The persisted [M11D-A report](../reports/evaluation/m11d-production-metadata-audit.md)
records 329 chunks: 53 for `5326_kabahatler_kanunu`, 276 for
`4458_gumruk_kanunu`; 329/329 valid canonical provenance, 324 unique source keys,
five legitimate two-chunk provisions and zero manifest inconsistencies. Production
was never opened by a Chroma client; recorded production PRE/POST hashes match.
The audit copy's logical snapshots match despite recorded physical housekeeping
changes. Stored vectors were readable at 1536 dimensions, but the report is not a
vector backup or proof of historical embedding-input/model provenance. Closure
uses that persisted evidence only; it does not reopen storage or rerun the audit.

Comparison with pre-M11 HEAD `00dc862d9803a16c9b5619ba8167081dcb911c57`
shows no changes to retrieve/embed/index/config or historical evaluation modules.
Query/document embedding inputs, distance metric, TOP_K, ordering, filters and
dense ranking are unchanged. B2 remains NOT VALIDATED and non-production;
M10E-C selected no candidate. No retrieval optimization belongs to M11.

The additive evaluator separates Source ANY/ALL from Document Hit/ALL/Intrusion
at 1/3/5. Duplicate chunks consume slots; only coverage sets deduplicate provisions.
Intrusion divides by actual retrieved slots (None for zero slots); malformed
canonical results fail, even beyond Top-5. Summaries cover overall, per document,
single/multi-source and single/multi-document. A multi-document question contributes
to each expected document's diagnostic group with its full gold set unchanged.
Historical bare-article, QualifiedSourceKey and legislation metrics/artifacts remain
unchanged; explicit adaptation has synthetic ANY/ALL parity tests for both laws.

### Readiness and remaining boundaries

Identity, generic registry records, citations and the new evaluation layer support
numbered laws, numberless regulations and decisions with canonical document IDs.
A decision identifier such as `2009/15481` is not itself a valid slash-containing
document ID; a reviewed canonical ID such as `2009_15481_bkk` can represent it.
No future document is added to the legacy bridge automatically. These are identity
capabilities, not proof that a future source's structure parses correctly.

Deferred items are limited to:

- Per-source parser/structure review before onboarding, including tables,
  footnote bodies and unsupported provision namespaces where relevant.
- A collision-safe storage-ID/admission policy before numberless or otherwise
  colliding documents are indexed. Existing law-prefixed article/chunk IDs remain
  compatibility aliases; lower-level missing-number IDs still use `unknown`.
- Document-specific descriptive fields (for example decision_number) only when
  justified by an actual source; the current manifest schema does not accept them.
- Older ingestion lookup and embedding-title lookup remain unchanged. The latter
  can fall back to legislation number/identifier for descriptive embedding text,
  never for DocumentSourceKey. Review before broader onboarding; changing it may
  change full embedding input and must not be treated as identity-only work.
- Retrieval optimization remains paused after M10E. Results-informed candidates
  require a new unseen holdout; the observed M10E-B set is not blind validation.

No metadata migration, reindex or re-embedding is required for the current corpus.
Any future identity-only vector reuse still requires byte-identical **full derived
embedding input**, unchanged model/dimensions, and safely recoverable/aligned
vectors; unchanged Chunk.text alone is insufficient.

## Original M11A audit and design (historical)

M11A adds only this document. No OpenAI request, network access, Chroma
inspection/query/reindex, vector metadata migration, new statute, new benchmark,
or commit is authorized by this design. Local paragraph JSON was parsed and
chunked **in memory** with existing functions solely to audit field propagation;
no processed output was written. LegalDocument → Article → Chunk is preserved.

## 1. Findings and problem statement

The system already has document identity metadata, but does not consistently
use it as machine source identity. Ingestion obtains a manifest `document_id`;
Article and Chunk copy it; indexing emits it when present. In contrast,
article/chunk ID construction is legislation-number-prefixed, M10 evaluation
requires legislation-number-based keys, older evaluation uses bare article
numbers, and validated citations omit document identity altogether.

Recommend an immutable **DocumentSourceKey(document_id, article_type,
normalized_article_no)**, distinct from storage chunk IDs and display citations.
Keep the current QualifiedSourceKey unchanged as a historical legacy type;
convert explicitly at new interfaces using a reviewed, unambiguous registry.
`legislation_number` becomes optional descriptive metadata for general document
interfaces, while remaining required in legacy evaluation formats and for
manifest records that represent numbered laws. No re-embedding is inherently
needed when the actual embedding input and embedding model/dimensions remain
identical. Current indexing accepts precomputed vectors; its CLI nevertheless
embeds again, so it is not a metadata-migration command.

## 2. Existing local metadata coverage

The ignored processed directory was explicitly enumerated (ordinary `rg --files`
hides its ignored JSON). There are four JSON files, plus `.gitkeep`:

| Local evidence | Rows | document_id coverage | legislation_number / article_type / article_no coverage |
|---|---:|---|---|
| `data/processed/5326-kabahatler-kanunu.articles.json` | 53 Articles | 53/53: `5326_kabahatler_kanunu` | Each 53/53 nonempty strings |
| `data/processed/5326-kabahatler-kanunu.chunks.json` | 53 Chunks | 53/53: `5326_kabahatler_kanunu` | Each 53/53 nonempty strings |
| `data/processed/5326-kabahatler-kanunu.paragraphs.json` | Paragraph document | Root `document_id` present | These are not per-paragraph identity fields |
| `data/processed/4458-gumruk-kanunu.paragraphs.json` | Paragraph document | Root `4458_gumruk_kanunu` present | These are not per-paragraph identity fields |
| Existing parser applied in memory to 4458 paragraphs | 271 Articles | 271/271: `4458_gumruk_kanunu` | Each 271/271 nonempty strings |
| Existing chunker applied in memory to those Articles | 276 Chunks | 276/276: `4458_gumruk_kanunu` | Each 276/276 nonempty strings |

**There is no persisted 4458 Article or Chunk JSON in this directory.** The
271/276 counts establish current local parser output, not field presence in
uninspected stored vectors. No claim is made about live Chroma metadata coverage.
The 5326 in-memory Article and Chunk outputs exactly equal their existing JSON
row lists. All 324 locally available/derived Articles have distinct
document/type/raw-number triples; all 329 available/derived Chunks have unique
chunk IDs. These checks are not a vector-store audit.

5326 Article/Chunk types: 49 normal, one ek, three gecici. 4458 Article types:
259 normal, 11 gecici, one islenemeyen_hukum; Chunk types: 263 normal,
12 gecici, one islenemeyen_hukum.

### Stability and scope

- Manifest IDs are explicitly assigned, not generated from title or content.
  `ingest._load_source_metadata` selects by resolved `local_file`; ingestion
  copies that entry's ID. Determinism is conditional on the same manifest/path.
  A missing/unmatched manifest returns no ID, and no uniqueness or conflicting
  entry validation currently enforces the intended global identity contract.
- `_load_and_parse_articles` copies the paragraph root's document ID, but looks
  up legislation number separately using `source_file`. It does not verify that
  the two identify the same manifest record. A stale root/path combination could
  therefore combine inconsistent identities. This needs future fail-closed validation.
- `parse_articles` copies document ID to every Article; `build_chunks` copies it
  from the parent. Chunking changes do not intrinsically change document identity.
- `article_id` uses `legislation_number or "unknown"`, article type and a
  lowercased slash-to-hyphen article number. `chunk_id` appends `-chunk-NNN` in
  source order. IDs are deterministic for fixed inputs/chunk settings, and
  unique for today's two laws, but **not document_id-scoped by construction**.
  Two documents sharing a number (or both missing it) can generate the same ID.
  A number containing `/` also contradicts the helper's broad "no slash" claim:
  only article-number slashes are replaced; the legislation prefix is unchanged.
- `ValidatedCitation` carries chunk ID but no document ID or document title.
  Rendering uses `"{number} sayılı Kanun"`; the UI adds article title. That does
  not expose a canonical document identity or the manifest's full document title.

### Reproducible local input fingerprints

| File under `data/processed/` | SHA-256 |
|---|---|
| `5326-kabahatler-kanunu.paragraphs.json` | `d9ec2810bc2e6e18f618333b74be051e374f53243db75526a3db9556596a4684` |
| `5326-kabahatler-kanunu.articles.json` | `258888bb943fb51fba40f9c0e03e2319bab0b2969c8f4a7c2693f2040bc5e53b` |
| `5326-kabahatler-kanunu.chunks.json` | `39db86bcc749add3dd1bec5b49f29bfa647ecef762d554143d08cfaed4efd036` |
| `4458-gumruk-kanunu.paragraphs.json` | `213f4b86da60ae60420ab720bbfbedc46bdb0b1f54c162781886240a548a134a` |

## 3. Code and documentation audit

References below identify current behavior, not proposed changes to historical
modules. The appendix indexes every literal identity-field occurrence in the
audited source/test files, including helper fixtures and reporting paths.

| File / responsible symbols | Current identity behavior and assumptions | Existing document_id use |
|---|---|---|
| `src/ingest.py`: `_load_source_metadata`, `ingest_document` | Manifest lookup by local file; returns first match or empty dict; no canonical source-key validation | Copies manifest ID into paragraph-document root |
| `src/chunk.py`: `Article`, `Chunk`, `_canonical_article_id`, `parse_articles`, `_load_and_parse_articles`, `parse_document`, `build_chunks`, `build_chunks_document`, CLI | Optional number and document ID; required type/no strings. IDs use number/type/no; missing number becomes `unknown`; special-section gecici becomes `islenemeyen_hukum`. Root metadata and parent fields are copied, not cross-validated | Both frozen dataclasses, all Article/Chunk construction, JSON roots |
| `src/embed.py`: `_find_manifest_entry`, `build_document_display_title`, `build_article_label`, `build_embedding_text`, `embed_chunks`, `EmbeddingResult` | Document lookup falls back to first matching legislation number; title fallback can be number/ID. Article labels depend on type/no; normal and special gecici display alike. Vector input includes derived title and label, not just text. EmbeddingResult links by chunk ID | Primary manifest lookup and title fallback; no canonical key in EmbeddingResult |
| `src/index.py`: `build_chroma_metadata`, `_validate_alignment`, `index_chunks`, CLI | Emits article ID/type/no and optional number/document ID. Omits None fields. Upsert/alignment identity is chunk ID; duplicate IDs rejected. Does not require number or document ID. CLI calls embed_chunks first | Explicit metadata field when non-None |
| `src/retrieve.py`: `RetrievedChunk`, result construction, `retrieve`, `_format_result_line` | Generic metadata dict and chunk ID are preserved; optional caller-supplied `where` forwarded. No QualifiedSourceKey, law-specific ranking, or document-key validation. CLI displays article label/title, defaults missing type to normal for display | Can transport document_id inside metadata; no explicit accessor/typed field |
| `src/generate.py`: `ValidatedCitation`, context formatting, `build_validated_citations`, `render_citation` | Context exposes number/no and chunk provenance. Citation fields copied from trusted chunks; numbered citation rendering assumes Kanun. Neither human text nor LLM prose establishes identity | None in citation/context identity model |
| `src/rag.py`: `RAGResult`, `_validate_cross_layer_invariants`, CLI | Context order and citation membership checked by chunk IDs; citation object passed through. CLI prints bare Madde/no. No canonical source comparison | Indirectly preserved in retrieval metadata, not added to citations |
| `src/evaluate.py`: `normalize_article_no`, question loading, `evaluate_question`, `evaluate_all`, reports | Historical single-law gold/matching uses bare normalized article_no; ignores document, law and type. Chunk IDs retained diagnostically, not gold identity | None |
| `src/evaluate_e2e.py`: `_article_values`, question evaluation, summaries/reports | Retrieved and cited article numbers compared to bare expected_articles; inherits old normalization and single-law scope | None |
| `src/evaluate_multilaw.py`: `QualifiedSourceKey`, `MultiLawQuestion`, `RetrievedRankInfo`, loaders, `_extract_rank_info`, scoring, grouping/confusion, historical adapters, writers, `_collection_law_counts` | Required nonempty legislation number + allowed type + normalized no. Frozen 5326 gold wrapped as 5326/normal; 4458 gold enforced as 4458. Source and legislation metrics are separate. Historical chunk lookup is chunk_id → legacy triple. Collection accounting validates legacy keys and groups by number | None in canonical matching/output types |
| `src/evaluate_retrieval_experiments.py`: `Document.key`, `deduplicate`, `score`, `summarize`, `breakdown`, `snapshot`, ranking/report assembly | Builds legacy keys from number/type/no metadata; B3 deduplicates on them. ANY/ALL use those key strings; law hits/intrusion use number. Inventory fixed to 5326/4458. BM25/RRF rank chunk IDs, with no document-key semantics | Generic Document.metadata can contain it; ranking projections do not expose it |
| `src/m10e_holdout.py`: question type/loaders, `compute_dev_gold_keys`, `compute_full_corpus_keys`, eligible/gold/overlap validation | Gold is a frozenset of legacy keys. 5326 JSON and parsed 4458 Articles provide legacy triples; source law must equal dataset, restricted to two laws | Not used in source matching |
| `src/evaluate_m10e_holdout.py`: question adaptation, gates, diagnostics, summaries/writers, main rank construction | Legacy source strings and expected laws derived from keys. Per-law gates explicitly use 5326/4458. Saved ranks project chunk ID, legacy source key and number; no document ID. B0/B2 source completeness uses legacy sets | None in rank projections |
| `src/m10e_failure_analysis.py`: `measure`, `classify`, `analyze`, CSV writer | Consumes frozen legacy strings as opaque source keys; number drives law hit/intrusion; hard-coded law groups. C1/C2 allocate chunk IDs, not source identities | None |
| `src/config.py` | Models, TOP_K, collection path/name, chunk target and frozen experimental constants only; no source-identity registry or number rule | None; future environment/path configuration remains centralized here |
| `src/evaluation_dataset.py` (dependency) | Reuses old expected_articles and normalization; historical dataset validation must remain interpretable | None |
| `src/ui.py`, `app.py` (display boundary) | SerializedCitation includes source label/display, number, article no/type/title. Excludes chunk ID, paragraph numbers and document provenance; app renders the prepared display string | None |

Production dense retrieval itself does **not** match by the legacy triple;
the number-centered assumptions live in ID construction, evaluation, and some
presentation/manifest fallback paths. Changing source identity must not be used
as an opportunity to alter ranking, retrieval parameters or B2 adoption.

Documentation findings:

- `docs/data-model.md` already gives LegalDocument and Article a document ID.
  Its Chunk field list/diagram omit document ID despite code containing it;
  its Article list omits legislation number despite code containing it. It
  describes conceptual Citation(document_name, number, no, paragraph_no, page,
  chunk_id), not the actual ValidatedCitation. It also predates implemented
  parsing and describes generic metadata differently from the current dataclass.
- `docs/architecture.md` preserves the desired document → Article → Chunk flow
  but has no canonical identity contract. References to generic PDF/text extraction
  and planned features should not be read as implemented ingestion capabilities.
- `docs/evaluation.md` explicitly defines the M10D legacy triple, separate law
  metrics, frozen 5326 adapters and source-type collision handling. Leave those
  historical definitions in place; add future document metrics under new names.
- `docs/indexing.md` already proposes document_id metadata and shared-collection
  separation. Its planned table includes a redundant `chunk_id` metadata field;
  current `build_chroma_metadata` instead includes `article_id` and does not copy
  chunk_id into metadata (it is the Chroma record ID). Treat code as current
  behavior. Optional number/document values are omitted by code, even though the
  planned table lists str. Its proposed list fallback is not the current native-list
  implementation. No storage API behavior was verified over the network here.

Test audit, grouped by assumption (literal locations in appendix):

- `test_ingest.py`: manifest/root document-ID propagation via ingestion and fixture output.
- `test_chunk.py`, `test_chunk_4458.py`: law-prefixed deterministic IDs; normal,
  ek, gecici and special namespaces; document-ID fixture fields; local inventory
  and lossless chunk reconstruction. No general cross-document missing-number
  collision contract is implemented yet.
- `test_embed.py`: document-first manifest title lookup, number prefix/fallback,
  type labels, exact derived embedding text, immutable source text and chunk-ID alignment.
- `test_index.py`, `test_retrieve.py`: number/document metadata fixtures, exact
  metadata/vector round trips, chunk-ID alignment; a legislation_number `where`
  test is a caller-filter example, not a production hard-coded law restriction.
- `test_evaluate.py`, `test_evaluate_e2e.py`, `test_evaluation_dataset.py`: bare
  article-number fixtures, normalization, old expected_articles metrics.
- `test_evaluate_multilaw.py`: legacy key equality/normalization, required triple,
  law/type collisions, 5326 adapter, historical outcome reconstruction, law metrics.
  `tests/fixtures/m10d_5326_chunk_metadata.json` has 53 chunk records with legacy
  number/type/no metadata and **no document_id**; do not label it complete provenance.
- `test_evaluate_retrieval_experiments.py`, `test_m10e_holdout.py`,
  `test_evaluate_m10e_holdout.py`, `test_m10e_failure_analysis.py`: legacy key strings,
  two-law gold/grouping, source completeness, candidate/holdout immutability and
  chunk-identity allocation. They are historical/diagnostic compatibility tests.
- `test_generate.py`, `test_rag.py`, `test_app.py`: trusted citation metadata,
  generic numbered-Kanun rendering, chunk-ID context membership and serialized
  citation fields. Existing fixtures often lack document metadata by design;
  migration tests need explicit legacy handling rather than fabricating IDs.

## 4. Identity layers — keep them distinct

| Concept | Example | Meaning |
|---|---|---|
| A. Document identity | `4458_gumruk_kanunu` | Stable manifest-assigned identity of an instrument, independent of title spelling/local path |
| B. Provision identity inside that document | `(normal, 27)` | Structural namespace and normalized provision number; insufficient globally |
| C. Canonical source key | `(4458_gumruk_kanunu, normal, 27)` | Identity of a provision within a document; one provision may own several chunks |
| D. Human legal citation | `4458 sayılı Gümrük Kanunu Madde 27` | Trusted display metadata and provision label, not a parseable machine identifier |
| E. Legacy evaluation key | `(4458, normal, 27)` | Historical M10 semantics; retains its type and serialized representation |
| Storage chunk identity | `4458-madde-27-chunk-001` | A particular chunk layout/output record; not the provision or document itself |

Document identity is not a raw-file hash, snapshot date, title slug recomputed
on every run, or citation label. A content digest identifies a specific input
artifact, not the enduring legal instrument. `[KAYNAK N]` is response-local
position, not any of these global identities.

## 5. Proposed canonical type: DocumentSourceKey

Proposed location: a small pure module such as `src/source_identity.py` in M11B;
no framework, registry I/O, Chroma or OpenAI dependency. No prototype is needed in M11A.

Fields are exactly `document_id: str`, `article_type: str`, `article_no: str`.
Use an immutable dataclass with value equality/hash and lexicographic ordering
by this three-field tuple if deterministic report sorting is needed. Ordering
is technical, not source order, chronology or legal precedence. Equality must
be type-specific: a DocumentSourceKey is never equal to a QualifiedSourceKey.
Python's process-local hash is suitable for sets/maps, **not** a persisted digest;
use deterministic serialization (or its SHA-256) for portable fingerprints.

### Construction, validation and normalization

1. Require real nonempty strings; never coerce None, numbers or booleans to strings.
   Both direct construction and factories must enforce the same canonical invariants.
   No `unknown` document key and no default normal article type on missing metadata.
2. `document_id` is the exact stable registered ID, not derived from number/title.
   Existing IDs use lowercase ASCII words/digits separated by underscores. Proposed
   admission grammar: `[a-z0-9]+(?:[_-][a-z0-9]+)*`, also allowing explicit hyphenated
   IDs without merging them with underscored IDs. Reject surrounding whitespace,
   uppercase, slash, percent escapes and control characters rather than silently
   rewriting an identifier. Pure key syntax validation is separate from manifest
   existence/uniqueness validation at the admission boundary.
3. `article_type` must be exactly one of the existing four values: `normal`, `ek`,
   `gecici`, `islenemeyen_hukum`. Do not infer it from article text or citation labels.
   New provision namespaces need an explicit later schema decision; do not squeeze
   annexes or other structures into these values just to pass validation.
4. Normalize `article_no` using the current algorithm, in the same order: strip,
   lowercase, replace ASCII `-` and `_` with `/`, collapse whitespace around `/`,
   strip again. Thus `42/A`, `42-a`, `42_A`, `42 / A` → `42/a`; preserve digits,
   leading zeros and segment order. Do not add stemming, Unicode lookalike folding,
   number parsing or removal of `Madde` prefixes. New canonical validation then
   rejects empty slash segments, remaining whitespace/control characters and
   non-alphanumeric segment characters. This admits current numeric/lettered
   values without pretending every future provision label is already supported.
5. Preserve source `Article.article_no`/`Chunk.article_no` for display and embedding
   input; normalization occurs in the key, never by rewriting those fields.
   Keep the historical normalizer/type untouched in M11B. A pure equivalent
   implementation must have parity tests; later extraction into shared code
   requires the same historical behavior, including edge cases. Canonical stricter
   validation must not be backported into old evaluators under the same contract.

The current QualifiedSourceKey factory normalizes only article number; it validates
that legislation number has non-whitespace content but retains the original string.
Its direct dataclass constructor can bypass factory normalization. Preserve these
historical behaviors; the new type need not repeat that construction loophole.

### Serialization and parsing

Recommend the readable canonical string
`4458_gumruk_kanunu/normal/27`; a lettered article is
`4458_gumruk_kanunu/normal/165/b`. Because document ID and type cannot contain
slashes, split **at most twice** (`split("/", 2)`): the entire remainder is article
number. Do not require exactly three slash-separated tokens. New string parsing
should accept only canonical encodings (re-serialize and compare); factories
accept the documented article aliases. No percent-decoding or title-based guessing.

For persisted new data, prefer explicit JSON objects:

```json
{"document_id":"4458_gumruk_kanunu","article_type":"normal","article_no":"27"}
```

The containing report/dataset declares its identity schema, e.g.
`source_identity_schema: "document-source-v1"`. Do not overload a frozen
`qualified_source_key` field with the new string. In new CSV use separate component
columns and optionally `document_source_key`; parsers must know the schema rather
than guessing identity type from the first string component.

## 6. Legacy compatibility recommendation

Recommend an **explicit adapter layer**, consisting of small pure conversion
helpers and an injected, reviewed resolution registry. Retain QualifiedSourceKey
as a separate legacy type at its current location. These are complementary roles,
not a silent alias or a broad new abstraction framework.

The initial audited registry is:

| Legacy legislation number | Canonical document ID |
|---|---|
| `5326` | `5326_kabahatler_kanunu` |
| `4458` | `4458_gumruk_kanunu` |

Manifest entries justify these mappings. Pin/snapshot the resolution used by an
adapter run and record its provenance in **new** outputs; do not depend on whichever
entry happens to appear first in a growing manifest. Unknown numbers, duplicate
number mappings, inconsistent document/number pairs and unresolved document IDs
fail explicitly. A valid explicit document ID must not be overridden by a number
fallback. Do not automatically resolve future documents through this two-law bridge.

Proposed operation: `to_document_source_key(legacy_key, registry)` converts only
after validating a well-formed legacy value and unique document resolution;
article namespace is copied, number uses the documented normalization. No I/O
inside the pure conversion. Do not parse arbitrary legacy strings as three
slash-delimited fields: legacy legislation numbers themselves have no slash ban.
New consumers should use known structured legacy records or the reviewed historical
two-law schema, rejecting ambiguous strings. A reverse conversion, if actually
needed, is partial and permitted only for a uniquely mapped legacy law; do not
invent a number for a regulation.

M9 bare expected_articles require a separate explicit dataset adapter carrying
the known 5326/normal scope. Do not generalize that default to arbitrary old data.
Historical ranked chunk IDs can be joined to their frozen metadata lookup as
today; an absent type/document join is an error, not a guessed normal source.
All M9/M10 JSON/CSV/Markdown and gold files remain immutable. New adapter views
must be named separately with source hashes/schema and are not new blind validation.

## 7. legislation_number policy

| Layer | Future general-document policy | Compatibility behavior |
|---|---|---|
| Manifest | Optional nullable string at generic schema level; required nonempty metadata for numbered-law entries such as 5326/4458/5607 | Preserve existing values. Missing/non-applicable may be omitted or null at input; canonical manifest representation can use null. Never assign parent-law number to a regulation as its identity |
| Article | `str \| None` descriptive metadata; canonical document_id required for admitted documents | Already optional in code; new strict admission is about document ID, not forcing a number |
| Chunk | `str \| None`, inherited from its Article | Already optional; keep consistent parent metadata |
| Citation | Nullable/optional number, with title/type/document ID from trusted provenance | Never infer a number from model prose or label every numbered instrument Kanun |
| Retrieval metadata | Optional number; omit key when None in stored metadata, expose None through typed adapters | Index builder already omits None. Generic document matching uses required document_id independently |
| New evaluation identity | Number is not a key field and is not required for source matching | May support supplemental law-specific reports when meaningful; document-level metrics must not drop numberless sources |
| Legacy evaluation identity | Required under existing QualifiedSourceKey/benchmark contract | Leave historical schema, validation and metrics unchanged |

Canonical DocumentSourceKey never contains a nullable document ID. Old raw domain
objects may remain permissive temporarily, but a canonical-admission interface
must reject/quarantine missing identity with a diagnostic. This prevents changing
historical fixtures into fabricated documents merely to satisfy a new type.

## 8. Manifest implications and future-source compatibility

`data/source_manifest.json` contains exactly two entries. Both already have
document_id, title, document_type (`Kanun`), legislation_number, issuing_authority
(`TBMM`), official_source_url, retrieved_at, local_file and notes. The document
IDs are unique; numbers currently map one-to-one. Retrieval dates are 2026-09-01
and 2026-09-03. URLs are recorded provenance, not fetched or legally verified by
M11A. There is **no effective_date, version, snapshot identifier or content hash
field** in the current manifest.

This is sufficient for today's document_id → title/type/number/source-URL mapping.
The first implementation need is validation and uniqueness, not a speculative
large schema: require stable ID, title, type and source provenance at admission;
verify local_file mapping/root ID consistency; handle number absence explicitly.
Keep existing fields/names instead of adding redundant aliases such as another
source_url beside official_source_url.

| Future source named in scope | What must be established at later onboarding | Identity consequence |
|---|---|---|
| 5607 Kaçakçılıkla Mücadele Kanunu | Reviewed manifest ID, title/type, law number, authority, official source URL and retrieved file/date | Same numbered-law metadata policy, document ID remains canonical |
| 2009/15481 Kararı | Reviewed stable slash-free document ID; decision type, actual title/authority and official decision-number provenance | Do not force a law number. A `decision_number` optional metadata field is justified when recording this decision's actual designation; do not put `/` into document_id |
| Gümrük Yönetmeliği | Reviewed stable ID, regulation title/type/authority and official source provenance; verify any actual designation rather than assume one | No legislation_number needed for identity; do not borrow `4458` from its parent law |
| Tasfiye Yönetmeliği | Same independent manifest/provenance review | Distinct document ID even if it cites the same enabling law or article numbers |

No IDs, source URLs, authorities, dates or corpus records for these future
documents are assigned by M11A. Their names are planning inputs, not assertions
about onboarded content. A generalized `official_number` field is not necessary
just to implement DocumentSourceKey; choose a broader identifier schema only
when actual heterogeneous metadata requires it.

Add snapshot/effective information only for a clear provenance need: retrieved_at
is an acquisition date, not a legal effective date. A source-file content SHA-256
and explicit snapshot/version label would allow later replays to identify the
exact consolidation; effective_date/effective interval should be stored only when
verified. Do not invent dates or one global effective date for provisions that
change independently. A document ID should remain stable across title/path fixes.

The proposed three-field source key identifies a provision of an instrument,
**not its text at every historical time**. Initial admission must prevent competing
snapshots of the same provision in one active corpus. If multiple versions must
coexist, introduce an explicit snapshot dimension/context under a separate reviewed
schema before admission; do not claim this key alone distinguishes versions.

## 9. Citation provenance design

Actual `ValidatedCitation` fields: source_number, source_label, chunk_id,
legislation_number, article_no, article_type, article_title, paragraph_numbers.
It has no document_id, document title/type, page or source URL. Construction
copies trusted retrieved fields after validating `[KAYNAK N]` membership; the
model never supplies authority for these fields. Keep that security/integrity
boundary and exact context order.

Future citation should retain those fields and add trusted document_id plus
DocumentSourceKey (or its explicit components), document title and document type;
source URL/snapshot reference can resolve from a verified manifest snapshot by
document ID. Avoid independently mutable duplicate identities: any stored key and
component fields must agree. Missing legacy metadata stays explicitly unresolved
until the adapter can prove a unique mapping.

Display full title, number **where applicable**, type-sensitive article label,
and paragraph numbers when actually known. Paragraph_numbers currently describe
the source chunk's available fıkra numbers, not proof that the model cited a
particular fıkra; never fabricate a pinpoint paragraph. Chunk ID remains traceable
internally and may be shown in source details. Do not treat article_title as
document title. Special `islenemeyen_hukum` and main gecici currently both render
Geçici Madde; add trusted section-context provenance when needed to disambiguate
display, without inventing a new legal label.

Machine identity is not the display string. UI serialization must eventually
carry the new safe provenance fields; `app.py` can continue rendering a prepared
label. Human citations must not be parsed back into canonical keys. No generation,
prompt, rendering or UI behavior changes in M11A.

## 10. Collision examples and namespace limits

These are identity examples, not newly invented corpus records or legal claims.

1. **Existing different documents:** 5326 normal/27 and 4458 normal/27 are distinct.
   Bare article_no matching conflates them; both legacy and document keys separate
   these two laws. This case alone does not expose the legacy triple's limitation.
2. **Numberless regulations (hypothetical same-number provisions):** if two
   independently admitted regulations each have normal/27 and no law-style number,
   the legacy key factory rejects both missing numbers. Replacing the number with
   `unknown` would conflate them; current article-ID generation actually uses that
   fallback. Independent document IDs distinguish them without fabricated numbers.
3. **Law and implementing regulation (hypothetical equal article number):** assigning
   both a parent-law number such as 4458 would produce identical legacy triples and
   storage ID prefixes. That is why enabling legislation is not document identity.
4. **Decision designation 2009/15481:** the legacy factory technically accepts a
   nonempty string containing `/`; it does not enforce digits-only law numbers.
   But `2009/15481/normal/27` is unsafe for naive three-component parsing, and the
   article-ID helper preserves the prefix slash. A reviewed slash-free document ID
   plus optional decision-number display metadata separates designation from key
   encoding. No decision provision is claimed to exist in today's corpus.
5. **Existing 4458 special namespaces:** `4458-gecici-madde-1` and
   `4458-islenemeyen-hukum-gecici-madde-1` are different parsed Articles. Future keys
   `4458_gumruk_kanunu/gecici/1` and
   `4458_gumruk_kanunu/islenemeyen_hukum/1` retain that distinction. Ek/normal/gecici
   numbers also remain distinct. The current four article_type values are sufficient
   for the audited 324 Articles, but not proven sufficient for future annexes,
   repeated special subsections or versions. Reject a detected duplicate canonical
   provision key rather than merging records; escalate a schema extension when needed.

## 11. Staged migration and cost analysis

| Stage | Required scope | Explicit exclusions / stop boundary |
|---|---|---|
| M11A | This offline audit/design and baseline tests | No implementation, data changes, Chroma or commit before review |
| M11B | Pure DocumentSourceKey, explicit legacy adapter/registry validation and compatibility tests | No retrieval/generation behavior, vector metadata migration, source onboarding, frozen artifact rewrite or re-embedding |
| M11C | Propagate canonical document identity through new admission/evaluation/retrieval-result/citation interfaces; validate consistent manifest/root/parent metadata; document-oriented metrics; compatible UI provenance | Dense ranking/order/query path unchanged; frozen evaluators/outputs stay historical. No implicit Chroma opening or API operation; tests use supplied records |
| M11D, conditional | Separately authorized stored-metadata inventory, determine actual gaps, plan metadata patch or rebuilt collection using verified existing vectors; storage-ID migration only if needed | No automatic blanket reindex/re-embed. Review exact before/after mapping, snapshot, backup/rollback and comparison plan before storage mutations |

M11C also needs a deliberate storage-ID/admission rule before non-law onboarding.
If an authorized later audit finds document_id/type/no already complete and
consistent on stored records, canonical keys can be derived at the interface:
**no metadata migration or vector rebuild is necessary merely to add the type**.
Existing article/chunk IDs should remain stable compatibility aliases. New keys
can be carried separately without renaming existing records. A new document-scoped
article/chunk ID format for future records must be versioned, injective and tested;
do not simply replace the prefix in old JSON or assume concatenated values are
unambiguous. If existing storage IDs are ever renamed, M11D must use a bijective
old-ID → new-ID map and handle stale old records explicitly; upsert under new IDs
alone would leave duplicates. This is separate from defining DocumentSourceKey.

### Three different operations

- **Metadata migration:** change identity/provenance fields associated with a
  record. It does not intrinsically change source text or vectors.
- **Vector reindex/rebuild:** reconstruct records/search structures or a collection
  from existing vectors and documents. This may affect approximate-search output
  even when vectors are identical; equality of keys is not a retrieval-equivalence
  guarantee. It is not synonymous with making embedding API calls.
- **Embedding recomputation:** derive new vectors from embedding input/model.
  Needed when the desired embedding representation/model changes or usable vectors
  cannot be recovered and no alternative verified copy exists, not merely because
  a metadata key was renamed.

Implementation evidence: `embed.build_embedding_text` returns display title +
article label + optional article title + blank line + original Chunk.text.
The display title can depend on both manifest identity fields. Therefore unchanged
Chunk.text **alone is insufficient** to guarantee vector reuse: changing lookup
fallback/title, case of article labels or article_title can change embedding bytes.
Verify the full derived input, model and dimensions before claiming equivalence.

Under the user's stated condition — unchanged Chunk.text **and byte-for-byte
unchanged embedding input**, with unchanged embedding model/dimensions — **no new
OpenAI embedding is required for an identity-only change**. Current
`index.index_chunks(chunks, results, collection=...)` validates matching chunk IDs
and dimensions, then supplies explicit embeddings/documents/metadatas to upsert;
it does not call OpenAI. `get_collection` uses `embedding_function=None`.
Existing vectors could therefore be wrapped/aligned as EmbeddingResult records
and reused through the existing indexing primitive or a carefully scoped future
metadata-only path. Whether a metadata-only storage API suffices must be checked
against the installed backend in an authorized M11D task; no such API is claimed
to have been exercised here.

Do **not** run `src.index.main` as a migration shortcut: it calls embed_chunks
before indexing. No metadata migration/export tool currently proves byte/model
equivalence or safely renames record IDs. Current indexing alignment validates
IDs and vector dimensions, not historical embedding-input hashes/model consistency.
M11D must add those provenance checks before reuse, not assume them from dimensions.
Availability of recoverable existing vectors is unverified because Chroma was not
opened; the inspected processed JSON contains no stored vector archive. This is
a theoretical reuse conclusion from code, not a promise that a rebuild is already
possible from the report artifacts alone.

## 12. Backward-compatibility test plan (future implementation)

No new tests or pure prototype are implemented in M11A. Future tests should cover:

1. Exact 5326 and 4458 legacy mappings above, including a lettered article; reverse
   conversion only where uniquely defined. Unknown/ambiguous numbers fail closed.
2. Different document IDs with identical normal/27 do not collide; missing/None
   legislation_number does not affect a valid document key, equality or hash.
3. Main gecici/1 and islenemeyen_hukum/1 stay distinct; normal/ek remain distinct;
   multiple chunks of one provision produce one source key but distinct chunk IDs.
4. Article alias normalization parity; preserve leading zeros; unrelated numbers
   and suffixes remain distinct. Reject empty components, invalid types, reserved
   document-ID separators, remaining whitespace/control characters and empty
   article segments. Test direct construction as well as factories.
5. Deterministic serialization, `split('/', 2)` lettered-article round trip, JSON
   object round trip, wrong-schema rejection, no automatic legacy/canonical equality.
   Never assert Python's numeric hash is stable across processes.
6. All historical QualifiedSourceKey/normalize_article_no behavior stays unchanged,
   including number whitespace retention and direct-constructor behavior. Hash all
   frozen artifacts before/after. Verify new adapter views preserve historical
   source-set outcomes on the audited two-law records without rewriting reports.
7. Manifest unique document ID/local-file resolution, missing metadata handling,
   contradictory paragraph root versus manifest, copied parent/child document ID,
   ambiguous number fallback rejection. Renaming title/path must not reassign ID.
8. Admission collision detection across law/decision/regulation and repeated
   namespaces/snapshots, using clearly synthetic fixtures only, not new legal gold.
9. Byte-for-byte old/new embedding-input comparison for an identity-only mapping,
   exact vector reuse with fake supplied embeddings, preserved IDs/order/text and
   metadata omission of None; spy asserts no embedding call in a migration path.
   Changing a header/title must invalidate the assumed input-equivalence check.
10. Citation document key matches its trusted context chunk; title/number fallback
    never fabricates provenance. Optional law number and unknown legacy document
    produce explicit behavior. Preserve paragraph/source-position caveats and
    response-label validation. UI serialization retains intended safe fields.
11. New document-hit/intrusion metrics include numberless documents and distinguish
    multi-source within one document from genuinely multi-document questions;
    missing document metadata has an explicit error/denominator policy.
12. Existing dense retrieval query parameters and ordered supplied results remain
    unchanged through new interfaces. Any later storage rebuild requires a separate
    controlled ranking-equivalence audit, not an assumption or a holdout rerun.

## 13. Future retrieval/evaluation impact and compatibility table

| Current field/type | Future role | Required change | Compatibility impact |
|---|---|---|---|
| Article/Chunk.document_id (optional) | Canonical document provenance | Required at new admission boundary; validate propagation | Old raw fixtures/readers may remain permissive; no fabricated IDs |
| legislation_number | Optional legal/display metadata | Remove general identity dependency, not historical law reports | Existing 5326/4458 metadata preserved |
| article_type + raw article_no | Provision namespace + source/display label | New key normalizes number separately | Do not rewrite chunk text, labels or legacy normalization |
| QualifiedSourceKey | Historical evaluation identity | Explicit adapter to separate DocumentSourceKey | No semantic rename or frozen report rewrite |
| article_id / chunk_id | Existing record/provenance aliases | Future document-scoped admission scheme; migrate old IDs only if necessary | Changing IDs is a distinct storage operation |
| RetrievedChunk.metadata | Trusted retrieved provenance | Typed document-key view/accessor with explicit legacy mode | Preserve text, distance, order and dense algorithm |
| expected_sources | New gold source keys under declared schema | New versioned dataset/adapter view | Historical datasets remain immutable |
| expected_legislations / law Hit@K | Legacy/supplemental law diagnostics | Add expected_document_ids, document Hit@K/confusion/intrusion | Do not relabel old metrics as document metrics |
| ValidatedCitation / SerializedCitation | Trusted machine provenance plus display | Carry document identity/title/type and optional number | Rendering/serialization change requires M11C tests |

Required M11 interface work: canonical matching, explicit legacy adapters,
document provenance on retrieved/cited records, strict admission consistency,
and separately named document-based diagnostics. Multi-source ALL@K remains
set completeness over provisions; it is not automatically multi-document
completeness. Define document-hit (at least one expected document), document-set
completeness (all expected documents) and provision ALL separately. Missing
canonical metadata should fail/report an identity error, not silently lower the
intrusion denominator or disappear as a numberless document.

Future data/benchmark work, **not M11A**: verify and onboard the four named future
sources; resolve any new provision namespaces/version dimensions; author expert-
reviewed cross-document gold and expected-document sets; produce new schema-labeled
benchmark artifacts. New IDs alone do not authorize new retrieval strategies.
M10E-B is observed development/diagnostic data for designs informed by it; any
such future retrieval candidate requires a completely new unseen holdout. None
is created, rerun or selected here.

## 14. M11A verification and review boundary

- `RUN_OPENAI_INTEGRATION_TESTS=0 python -m pytest -q`: **456 passed, 2 skipped**.
  No new tests were added. The requested existing suite uses fake API clients
  and isolated temporary local Chroma fixtures; no production collection was
  opened or queried. The audit itself only read source/JSON and parsed in memory.
- `git diff --check`: passed; this new document also checked for trailing whitespace.
- All four processed JSON fingerprints above were rechecked unchanged.
- No tracked modifications or staged files. The only new file is
  `docs/source-identity-m11.md`. Frozen M9/M10 artifacts, manifest, production
  source files, tests and configuration remain unchanged.
- HEAD remains `00dc862d9803a16c9b5619ba8167081dcb911c57`.
  No migration, new holdout/source, reindex, embedding call or commit performed.
  M11B/M11C/M11D are proposed review boundaries, not work started by M11A.

## Appendix A. Literal field-reference inventory at audited HEAD

Line numbers include declarations, metadata access, fixtures, comments and docstrings; references are not all identity comparisons. The functional audit above distinguishes identity use from transport/display. Files with no direct field reference can still forward metadata through another object. Number ranges are inclusive.

| File | document_id lines | legislation_number lines | article_type lines | article_no lines |
|---|---|---|---|---|
| `src/chunk.py` | 68, 264, 298, 434, 438, 447, 449, 454, 456, 458, 498, 703, 723, 727, 730, 789, 791, 800 | 69, 237, 245, 265, 296, 299, 431, 441, 444, 447, 499, 704 | 71, 147, 237, 240, 247, 249, 251, 296, 301, 350, 352-353, 357, 366, 501, 706, 807 | 70, 147, 159-160, 237, 246, 296, 300, 350, 365, 500, 705 |
| `src/ingest.py` | 144, 161, 170 | none | none | none |
| `src/embed.py` | 163, 166, 171, 173, 182, 185, 194, 198, 208, 238 | 163, 167, 175, 177, 182, 186, 194, 198, 200, 238 | 137, 211, 215, 218, 220, 239 | 211, 221, 239 |
| `src/index.py` | 141, 148 | 142, 149 | 144 | 143 |
| `src/retrieve.py` | none | none | 367, 369 | 366, 369 |
| `src/generate.py` | none | 44, 172, 262-264, 602, 622-623 | 174, 604, 626, 628 | 45, 160, 173, 266-268, 603, 625, 628, 630, 632 |
| `src/rag.py` | none | none | none | 147-148 |
| `src/evaluate.py` | none | none | none | 24, 36, 38, 103, 121-123, 245, 248, 418 |
| `src/evaluate_e2e.py` | none | none | none | 219, 227 |
| `src/evaluate_multilaw.py` | none | 18, 21, 30, 138, 142, 147, 152, 154-155, 161, 167, 229, 283, 285, 356, 396, 401, 407, 436, 444, 447, 450, 505, 638, 642, 735, 812, 814 | 19, 21, 31, 49, 138, 142, 148, 152, 156-157, 162, 167, 229, 286, 357, 396, 402, 408, 638, 642, 736, 812 | 13, 18, 22, 33, 46, 138-139, 143, 149, 152, 158-159, 163, 167, 194, 229, 286, 358, 396, 403, 408, 638, 642, 652, 736, 812 |
| `src/evaluate_retrieval_experiments.py` | none | 59, 156, 161-163, 220, 362, 383 | 60 | 60 |
| `src/evaluate_m10e_holdout.py` | none | 114, 490, 503 | none | none |
| `src/m10e_holdout.py` | none | 97, 101, 158, 160 | 97, 101, 161 | 97, 101, 161 |
| `src/m10e_failure_analysis.py` | none | 69-71, 92-93 | none | none |
| `src/config.py` | none | none | none | none |
| `src/evaluation_dataset.py` | none | none | none | none |
| `src/ui.py` | none | 33, 62 | 35, 64 | 34, 63 |
| `app.py` | none | none | none | none |
| `tests/conftest.py` | none | none | none | none |
| `tests/test_app.py` | none | 23, 53 | 25, 53 | 24, 53, 61, 111 |
| `tests/test_chunk.py` | 80, 95, 137, 157, 184, 199-200, 275, 291, 305, 316, 318, 350, 593, 604, 606, 627, 653 | 80, 95, 137, 157, 184, 199-200, 275, 291, 351, 627, 654 | 83, 85, 87, 98, 111, 118, 139, 190, 340, 353, 503-504, 507, 659, 662-663 | 83, 85, 87, 97, 138, 190, 337, 349, 352, 409, 470, 480, 492, 503-504, 506, 527, 530, 574, 576, 579, 583, 659, 665 |
| `tests/test_chunk_4458.py` | 22, 39, 131 | 22, 39, 131 | 40, 103, 134 | 28, 34, 40, 138 |
| `tests/test_embed.py` | 126, 136, 232 | 127, 137, 232 | 122, 139, 166, 204 | 120, 135, 138, 166, 489 |
| `tests/test_evaluate.py` | 362 | 363 | 365 | 358, 361, 364, 368 |
| `tests/test_evaluate_e2e.py` | none | none | none | 14-15 |
| `tests/test_evaluate_m10e_holdout.py` | none | 32, 315 | 315 | 315 |
| `tests/test_evaluate_multilaw.py` | none | 24, 29, 49, 164 | 29, 49, 164 | 29, 49, 164 |
| `tests/test_evaluate_retrieval_experiments.py` | none | 18, 109-110 | 18 | 18 |
| `tests/test_evaluation_dataset.py` | none | none | none | none |
| `tests/test_generate.py` | none | 180, 694, 696, 714, 743, 755, 767 | 716, 744, 756, 768 | 185, 700, 702, 715, 745, 757, 769, 895, 897, 902 |
| `tests/test_index.py` | 42, 52, 87 | 43, 53, 88 | 38, 55, 84, 90 | 35, 51, 54, 84, 89, 192, 204, 280, 291, 315, 451 |
| `tests/test_ingest.py` | 201, 230 | none | none | none |
| `tests/test_m10e_failure_analysis.py` | none | 16, 56 | none | none |
| `tests/test_m10e_holdout.py` | none | 24, 140, 152, 156, 167, 186 | 24, 140, 153, 167, 186 | 24, 140, 154, 167, 186 |
| `tests/test_rag.py` | none | 21 | 21 | 16, 21, 258, 260 |
| `tests/test_retrieve.py` | 43, 53 | 44, 54, 388 | 39, 56 | 36, 52, 55, 202, 233-235, 287-289 |

`tests/fixtures/m10d_5326_chunk_metadata.json` repeats legislation_number/article_type/article_no for 53 chunks; it contains no document_id. Frozen benchmark expected_sources and ranked-output projections are legacy data, not new domain-model declarations.
