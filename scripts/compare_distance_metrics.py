"""
Milestone M5B follow-up - one-off controlled experiment.

Compares the real Chroma collection's `hnsw:space = "l2"` configuration
against an otherwise-identical `hnsw:space = "cosine"` replica, to see
whether the distance metric alone changes retrieval quality (Recall@K) on
the same 5326 corpus and the same evaluation question set.

This script is analysis tooling only. It is intentionally kept out of
`src/` (like `scripts/inspect_docx_structure.py`) so it is never mistaken
for the production chunk -> embed -> index -> retrieve -> generate pipeline
(see docs/architecture.md, AGENTS.md). It never writes to the real
`chroma/` directory and never re-runs indexing.

SINGLE-VARIABLE DESIGN - everything except `hnsw:space` is held fixed:

1. Document vectors are never re-embedded. `build_cosine_replica()` reads
   every id/embedding/document/metadata straight out of the existing real
   L2 collection (one `.get()` call, read-only) and `.upsert()`s that exact
   data - unchanged - into a fresh collection created with
   `configuration={"hnsw": {"space": "cosine"}}`.

2. `verify_replica_matches_source()` confirms, BEFORE any retrieval
   comparison is trusted, that: record counts match, id sets match, and
   every document/metadata/embedding is identical between the two
   collections (embeddings compared with a tight float tolerance, since
   Chroma round-trips vectors through float32 storage).

3. Each evaluation question is embedded EXACTLY ONCE via
   `retrieve.embed_query()`. The resulting vector is reused, unmodified, to
   query BOTH collections via `retrieve.retrieve_by_embedding()` - never a
   second embedding call per question, and never `retrieve()` called twice
   end-to-end (which would re-embed).

4. Recall@K is computed with the exact same pure metric functions as M5B
   (`src.evaluate.evaluate_question` / `summarize`) for both result sets, so
   the only thing that can differ between the "L2" and "cosine" columns is
   the collection's distance metric.

Requires explicit opt-in (same convention as src/embed.py, src/index.py,
src/retrieve.py, src/evaluate.py) since it makes real OpenAI embedding
calls for the 15 evaluation questions:

    RUN_OPENAI_INTEGRATION_TESTS=1 python scripts/compare_distance_metrics.py

The cosine replica is written to a fresh temporary directory (default:
`tempfile.mkdtemp()`, never the project's `chroma/` directory) so repeated
runs never reuse a stale/partial copy from a previous run.
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import chromadb  # noqa: E402
from chromadb.api.models.Collection import Collection  # noqa: E402

from src import config, evaluate, index, retrieve  # noqa: E402

if __name__ == "__main__":  # pragma: no cover - script entry point, not unit-tested
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


class ExperimentError(RuntimeError):
    """Raised when the controlled-experiment invariants (an exact copy of
    the source collection's ids/vectors/documents/metadata) cannot be
    verified. Retrieval-quality numbers are never compared across the two
    collections unless this check has passed - otherwise a copy bug, not
    the distance metric, could explain any observed difference.
    """


def _real_experiment_opt_in() -> bool:
    """Same explicit opt-in gate as src/embed.py, src/index.py,
    src/retrieve.py and src/evaluate.py: BOTH `OPENAI_API_KEY` and
    `RUN_OPENAI_INTEGRATION_TESTS=1` must be set before this script embeds a
    single real question."""
    return bool(config.OPENAI_API_KEY) and os.getenv("RUN_OPENAI_INTEGRATION_TESTS") == "1"


# ============================================================================
# Step 1: copy the real L2 collection's records into a fresh cosine replica
# (no re-embedding - the exact stored vectors are read back and reused)
# ============================================================================


def _fetch_all_records(collection: Collection) -> dict[str, list[Any]]:
    """Read every id/embedding/document/metadata out of `collection` in one
    `.get()` call - the ONLY operation this script ever performs against the
    real source collection (never `.upsert()`/`.add()`/`.delete()` on it)."""
    data = collection.get(include=["embeddings", "documents", "metadatas"])
    return {
        "ids": list(data["ids"]),
        "embeddings": [list(vector) for vector in data["embeddings"]],
        "documents": list(data["documents"]),
        "metadatas": [dict(m) if m else {} for m in data["metadatas"]],
    }


def build_cosine_replica(
    source_collection: Collection,
    *,
    cosine_path: str | Path,
    collection_name: str,
) -> tuple[Collection, dict[str, list[Any]]]:
    """Create a fresh Chroma collection at `cosine_path`, configured with
    `hnsw:space = "cosine"`, and copy `source_collection`'s exact records
    into it verbatim - same ids, same precomputed vectors (never
    re-embedded through OpenAI), same documents, same metadata. The ONLY
    intended difference from `source_collection` is the distance metric.

    Returns the new collection plus the exact records read from the source,
    so the caller can verify the copy (`verify_replica_matches_source`)
    without a second read of the source collection.
    """
    source_records = _fetch_all_records(source_collection)

    client = chromadb.PersistentClient(path=str(cosine_path))
    cosine_collection = client.get_or_create_collection(
        name=collection_name,
        embedding_function=None,
        configuration={"hnsw": {"space": "cosine"}},
    )

    if source_records["ids"]:
        cosine_collection.upsert(
            ids=source_records["ids"],
            embeddings=source_records["embeddings"],
            documents=source_records["documents"],
            metadatas=source_records["metadatas"],
        )

    return cosine_collection, source_records


def verify_replica_matches_source(
    source_records: dict[str, list[Any]],
    cosine_collection: Collection,
    *,
    tolerance: float = 1e-4,
) -> None:
    """Confirm the cosine replica is an exact copy of the source records
    BEFORE any retrieval-quality comparison is trusted: equal count, equal
    id sets, identical documents/metadata per id, and numerically identical
    vectors (within `tolerance`, to allow only the float32 storage
    round-trip Chroma itself performs on write - never a semantic
    difference). Raises `ExperimentError` on any mismatch.
    """
    source_ids = source_records["ids"]
    source_count = len(source_ids)
    cosine_count = cosine_collection.count()
    if source_count != cosine_count:
        raise ExperimentError(f"Record count mismatch: source={source_count} cosine={cosine_count}")

    cosine_data = cosine_collection.get(include=["embeddings", "documents", "metadatas"])
    if set(cosine_data["ids"]) != set(source_ids):
        raise ExperimentError("id sets differ between the source collection and the cosine replica")

    cosine_by_id = {
        chunk_id: (doc, meta, embedding)
        for chunk_id, doc, meta, embedding in zip(
            cosine_data["ids"], cosine_data["documents"], cosine_data["metadatas"], cosine_data["embeddings"]
        )
    }

    for i, chunk_id in enumerate(source_ids):
        source_document = source_records["documents"][i]
        source_metadata = source_records["metadatas"][i]
        source_embedding = source_records["embeddings"][i]
        cosine_document, cosine_metadata, cosine_embedding = cosine_by_id[chunk_id]

        if cosine_document != source_document:
            raise ExperimentError(f"document mismatch for chunk_id {chunk_id!r}")
        if cosine_metadata != source_metadata:
            raise ExperimentError(f"metadata mismatch for chunk_id {chunk_id!r}")
        if len(cosine_embedding) != len(source_embedding):
            raise ExperimentError(f"embedding dimensionality mismatch for chunk_id {chunk_id!r}")
        for source_value, cosine_value in zip(source_embedding, cosine_embedding):
            if abs(float(source_value) - float(cosine_value)) > tolerance:
                raise ExperimentError(
                    f"embedding value mismatch for chunk_id {chunk_id!r}: "
                    f"{source_value!r} (source) vs {cosine_value!r} (cosine)"
                )


# ============================================================================
# Steps 2-3: embed each question ONCE, query BOTH collections with that
# same vector, and score both with the M5B metric functions unchanged
# ============================================================================


def compare_metric(
    questions: list[evaluate.EvaluationQuestion],
    *,
    l2_collection: Collection,
    cosine_collection: Collection,
    client: Any = None,
    top_k: int = evaluate.EVAL_TOP_K,
) -> tuple[evaluate.EvaluationSummary, evaluate.EvaluationSummary]:
    """For every question: embed it exactly once (`retrieve.embed_query`),
    then reuse that one vector to query both `l2_collection` and
    `cosine_collection` via `retrieve.retrieve_by_embedding` - never a
    second embedding call for the same question. Returns
    `(l2_summary, cosine_summary)` computed with the identical M5B metric
    functions (`src.evaluate`), so only the collection's distance metric can
    explain any difference between the two summaries.
    """
    l2_evaluations: list[evaluate.QuestionEvaluation] = []
    cosine_evaluations: list[evaluate.QuestionEvaluation] = []

    for question in questions:
        vector, _model, _usage = retrieve.embed_query(question.question, client=client)

        l2_results = retrieve.retrieve_by_embedding(vector, collection=l2_collection, top_k=top_k)
        cosine_results = retrieve.retrieve_by_embedding(vector, collection=cosine_collection, top_k=top_k)

        l2_evaluations.append(
            evaluate.evaluate_question(
                question,
                retrieved_article_nos=[c.metadata.get("article_no") for c in l2_results],
                retrieved_chunk_ids=[c.chunk_id for c in l2_results],
                retrieved_distances=[c.distance for c in l2_results],
            )
        )
        cosine_evaluations.append(
            evaluate.evaluate_question(
                question,
                retrieved_article_nos=[c.metadata.get("article_no") for c in cosine_results],
                retrieved_chunk_ids=[c.chunk_id for c in cosine_results],
                retrieved_distances=[c.distance for c in cosine_results],
            )
        )

    return evaluate.summarize(l2_evaluations), evaluate.summarize(cosine_evaluations)


# ============================================================================
# CLI
# ============================================================================


def _pct(fraction: float) -> str:
    return f"{fraction * 100:.1f}%"


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Controlled experiment: Chroma hnsw:space l2 vs cosine on the real 5326 collection."
    )
    parser.add_argument(
        "questions_json",
        nargs="?",
        type=Path,
        default=evaluate.DEFAULT_QUESTIONS_PATH,
        help=f"Path to an evaluation questions JSON file (default: {evaluate.DEFAULT_QUESTIONS_PATH})",
    )
    parser.add_argument(
        "--cosine-path",
        type=Path,
        default=None,
        help="Directory for the cosine replica's PersistentClient (default: a fresh temp directory per run)",
    )
    parser.add_argument(
        "--cosine-collection-name",
        default=f"{config.COLLECTION_NAME}_cosine_experiment",
        help="Name for the cosine replica collection",
    )
    args = parser.parse_args(argv)

    if not _real_experiment_opt_in():
        print(
            "Experiment skipped: requires both OPENAI_API_KEY and "
            "RUN_OPENAI_INTEGRATION_TESTS=1 (explicit opt-in not enabled or "
            "credentials unavailable)."
        )
        return

    questions = evaluate.load_questions(args.questions_json)

    l2_client = index.get_client()
    l2_collection = index.get_collection(l2_client)
    l2_count = l2_collection.count()
    if l2_count == 0:
        print(f"Real collection '{l2_collection.name}' is empty - nothing to compare.")
        return

    cosine_path = args.cosine_path or Path(tempfile.mkdtemp(prefix="gumruk_chatbot_cosine_experiment_"))

    print(f"Source (L2) collection: {l2_collection.name}")
    print(f"Source distance metric: {retrieve.distance_metric(l2_collection)}")
    print(f"Source record count: {l2_count}")
    print()

    cosine_collection, source_records = build_cosine_replica(
        l2_collection, cosine_path=cosine_path, collection_name=args.cosine_collection_name
    )
    print(f"Cosine replica collection: {cosine_collection.name}")
    print(f"Cosine replica path: {cosine_path}")
    print(f"Cosine replica distance metric: {retrieve.distance_metric(cosine_collection)}")
    print(f"Cosine replica record count: {cosine_collection.count()}")
    print()

    verify_replica_matches_source(source_records, cosine_collection)
    print("Verified: ids, documents, metadata, and vectors are identical between the L2")
    print("source and the cosine replica; record counts match. No re-embedding occurred.")
    print()

    l2_summary, cosine_summary = compare_metric(
        questions, l2_collection=l2_collection, cosine_collection=cosine_collection
    )

    print(f"Questions evaluated: {len(questions)} (each embedded exactly once, query vector reused for both collections)")
    print()
    print(f"{'':<16}{'L2':>16}{'cosine':>16}")
    for label, l2_val, cos_val in [
        ("Recall@1", l2_summary.any_hit_count_at_1, cosine_summary.any_hit_count_at_1),
        ("Recall@3", l2_summary.any_hit_count_at_3, cosine_summary.any_hit_count_at_3),
        ("Recall@5", l2_summary.any_hit_count_at_5, cosine_summary.any_hit_count_at_5),
    ]:
        l2_str = f"{l2_val}/{l2_summary.total_questions} ({_pct(l2_val / l2_summary.total_questions)})"
        cos_str = f"{cos_val}/{cosine_summary.total_questions} ({_pct(cos_val / cosine_summary.total_questions)})"
        print(f"{label:<16}{l2_str:>16}{cos_str:>16}")

    print()
    print("Per-question first expected rank (L2 vs cosine):")
    print(f"{'ID':<6}{'Expected':<10}{'L2 rank':<14}{'cosine rank':<14}")
    for l2_qe, cosine_qe in zip(l2_summary.question_results, cosine_summary.question_results):
        l2_rank = str(l2_qe.first_expected_rank) if l2_qe.first_expected_rank is not None else "not in Top-5"
        cosine_rank = (
            str(cosine_qe.first_expected_rank) if cosine_qe.first_expected_rank is not None else "not in Top-5"
        )
        expected_str = ", ".join(l2_qe.expected_articles)
        marker = "  <-- differs" if l2_rank != cosine_rank else ""
        print(f"{l2_qe.question_id:<6}{expected_str:<10}{l2_rank:<14}{cosine_rank:<14}{marker}")


if __name__ == "__main__":
    main()
