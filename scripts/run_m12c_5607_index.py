"""Run the authorized M12C 5607 embedding and additive indexing operation."""

from __future__ import annotations

import hashlib
import json
import math
import shutil
import sys
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

import chromadb

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import config, embed, index, source_identity


ROOT = Path(__file__).resolve().parents[1]
CHUNKS_PATH = ROOT / "data/processed/5607-kacakcilikla-mucadele-kanunu.chunks.json"
PRODUCTION_PATH = ROOT / config.CHROMA_PATH
REPORT_DIR = ROOT / "reports/evaluation"
MODEL = "text-embedding-3-small"
DIMENSIONS = 1536
BATCH_SIZE = 64


def _json_hash(value: Any) -> str:
    """Hash deterministic UTF-8 JSON without exposing the value."""
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _tree_fingerprint(path: Path) -> tuple[str, int]:
    """Hash every production-store file by relative path, size, and bytes."""
    rows: list[str] = []
    for file_path in sorted(p for p in path.rglob("*") if p.is_file()):
        relative = file_path.relative_to(path).as_posix()
        rows.append(f"{relative}|{file_path.stat().st_size}|{hashlib.sha256(file_path.read_bytes()).hexdigest()}")
    return _json_hash(rows), len(rows)


def _collection_records(collection: Any) -> dict[str, tuple[Any, Any, Any]]:
    """Return records keyed by ID for logical comparison, including vectors."""
    data = collection.get(include=["documents", "metadatas", "embeddings"])
    vectors = [list(vector) for vector in data["embeddings"]]
    return dict(zip(data["ids"], zip(data["documents"], data["metadatas"], vectors)))


def _logical_hash(records: dict[str, tuple[Any, Any, Any]]) -> str:
    """Hash sorted IDs, documents, metadata, and vectors without storing them."""
    ordered = [[key, *records[key]] for key in sorted(records)]
    return _json_hash(ordered)


def _distribution(records: dict[str, tuple[Any, Any, Any]]) -> dict[str, int]:
    """Count records by canonical document ID."""
    return dict(Counter(value[1].get("document_id") for value in records.values()))


def _validate_vectors(results: embed.EmbeddingRunResult, expected: int) -> None:
    """Validate count, dimensions, finiteness, and model of API results."""
    assert results.input_count == expected
    assert results.model == MODEL
    assert all(len(result.embedding) == DIMENSIONS for result in results.results)
    assert all(math.isfinite(float(value)) for result in results.results for value in result.embedding)


def main() -> None:
    """Perform one embedding call, one additive write, idempotence, and reopen checks."""
    chunks = embed._load_chunks_from_json(CHUNKS_PATH)
    assert len(chunks) == 46
    assert len({chunk.article_id for chunk in chunks}) == 43
    assert len({chunk.chunk_id for chunk in chunks}) == 46
    assert all(
        chunk.document_id == "5607_kacakcilikla_mucadele_kanunu"
        and chunk.legislation_number == "5607"
        and chunk.text
        for chunk in chunks
    )
    for chunk in chunks:
        source_identity.DocumentSourceKey(chunk.document_id, chunk.article_type, chunk.article_no)

    embedding_inputs = [embed.build_embedding_text(chunk) for chunk in chunks]
    input_hash = _json_hash(embedding_inputs)
    chunk_id_hash = _json_hash([chunk.chunk_id for chunk in chunks])
    model_dimensions_hash = _json_hash({"model": MODEL, "dimensions": DIMENSIONS})

    # The one real embedding operation in M12C.
    run = embed.embed_chunks(
        chunks,
        model=MODEL,
        batch_size=BATCH_SIZE,
        include_embedding_text=True,
    )
    _validate_vectors(run, len(chunks))
    assert [result.chunk_id for result in run.results] == [chunk.chunk_id for chunk in chunks]
    assert [result.embedding_text for result in run.results] == embedding_inputs

    copy_root = Path(tempfile.mkdtemp(prefix="m12c-chroma-copy-"))
    copy_path = copy_root / PRODUCTION_PATH.name
    shutil.copytree(PRODUCTION_PATH, copy_path)
    production_tree_hash, production_file_count = _tree_fingerprint(PRODUCTION_PATH)
    copy_tree_hash, copy_file_count = _tree_fingerprint(copy_path)
    assert (production_tree_hash, production_file_count) == (copy_tree_hash, copy_file_count)

    copy_client = chromadb.PersistentClient(path=str(copy_path))
    copy_collection = copy_client.get_collection(name=config.COLLECTION_NAME, embedding_function=None)
    baseline_records = _collection_records(copy_collection)
    assert len(baseline_records) == 329
    assert _distribution(baseline_records) == {
        "5326_kabahatler_kanunu": 53,
        "4458_gumruk_kanunu": 276,
    }
    assert all(len(vector) == DIMENSIONS for _, _, vector in baseline_records.values())
    baseline_hash = _logical_hash(baseline_records)
    assert copy_collection.configuration["hnsw"]["space"] == "l2"

    existing_ids = set(baseline_records)
    new_ids = {chunk.chunk_id for chunk in chunks}
    assert not existing_ids & new_ids

    # Production is opened only after embedding validation and copy verification.
    production_client = index.get_client()
    production_collection = production_client.get_collection(
        name=config.COLLECTION_NAME, embedding_function=None
    )
    assert production_collection.count() == 329
    assert _logical_hash(_collection_records(production_collection)) == baseline_hash

    first_index = index.index_chunks(
        chunks, run.results, collection=production_collection, batch_size=BATCH_SIZE
    )
    assert first_index.collection_count == 375
    post_records = _collection_records(production_collection)
    assert len(post_records) == 375
    assert _distribution(post_records) == {
        "5326_kabahatler_kanunu": 53,
        "4458_gumruk_kanunu": 276,
        "5607_kacakcilikla_mucadele_kanunu": 46,
    }
    assert all(post_records[key] == baseline_records[key] for key in existing_ids)

    for chunk in chunks:
        document, metadata, vector = post_records[chunk.chunk_id]
        assert document == chunk.text
        assert metadata == index.build_chroma_metadata(chunk)
        assert metadata["document_id"] == chunk.document_id
        assert metadata["legislation_number"] == chunk.legislation_number
        assert metadata["article_type"] == chunk.article_type
        assert metadata["article_no"] == chunk.article_no
        assert metadata["article_id"] == chunk.article_id
        source_identity.DocumentSourceKey(metadata["document_id"], metadata["article_type"], metadata["article_no"])
        assert len(vector) == DIMENSIONS
        assert all(math.isfinite(float(value)) for value in vector)

    stored_5607_hash_before_idempotence = _logical_hash({key: post_records[key] for key in new_ids})
    second_index = index.index_chunks(
        chunks, run.results, collection=production_collection, batch_size=BATCH_SIZE
    )
    assert second_index.collection_count == 375
    post_idempotence = _collection_records(production_collection)
    assert _logical_hash({key: post_idempotence[key] for key in new_ids}) == stored_5607_hash_before_idempotence
    assert len(post_idempotence) == 375

    reopened = chromadb.PersistentClient(path=str(PRODUCTION_PATH))
    reopened_collection = reopened.get_collection(name=config.COLLECTION_NAME, embedding_function=None)
    reopened_records = _collection_records(reopened_collection)
    assert len(reopened_records) == 375
    assert _logical_hash(reopened_records) == _logical_hash(post_idempotence)

    report = {
        "source_head": "56591895fcdec8c85fac72c97d5c3329e858bb82",
        "document_id": "5607_kacakcilikla_mucadele_kanunu",
        "accepted_articles": 43,
        "accepted_chunks": 46,
        "embedding_model": MODEL,
        "dimensions": DIMENSIONS,
        "embedding_input_sha256": input_hash,
        "ordered_chunk_id_sha256": chunk_id_hash,
        "model_dimensions_sha256": model_dimensions_hash,
        "embedding_api_calls": run.batch_count,
        "embedding_batch_size": BATCH_SIZE,
        "prompt_tokens": run.usage.prompt_tokens,
        "total_tokens": run.usage.total_tokens,
        "pre_count": 329,
        "post_count": 375,
        "distribution": _distribution(reopened_records),
        "collection_name": config.COLLECTION_NAME,
        "chroma_path": str(config.CHROMA_PATH),
        "distance_metric": "l2",
        "production_tree_sha256_before": production_tree_hash,
        "copy_tree_sha256": copy_tree_hash,
        "existing_329_logical_sha256": baseline_hash,
        "existing_329_preserved": True,
        "new_5607_ids": len(new_ids),
        "new_5607_validation": "46/46 PASS",
        "canonical_provenance_validation": "46/46 PASS",
        "cross_document_id_collisions": 0,
        "idempotence_embedding_api_calls": 0,
        "idempotence_collection_count": 375,
        "idempotence_duplicate_ids": 0,
        "persistence_reopen": "PASS",
        "retrieval_evaluation_run": False,
        "openai_generation_calls": 0,
        "raw_vectors_in_report": False,
    }
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (REPORT_DIR / "m12c-5607-indexing.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    markdown = "\n".join(
        [
            "# M12C — 5607 Additive Embedding and Chroma Indexing",
            "",
            "- Source HEAD: `56591895fcdec8c85fac72c97d5c3329e858bb82`",
            "- Document: `5607_kacakcilikla_mucadele_kanunu`",
            "- Accepted input: 43 Articles / 46 Chunks",
            f"- Embedding model/dimensions: `{MODEL}` / `{DIMENSIONS}`",
            f"- Full embedding-input SHA-256: `{input_hash}`",
            f"- API calls/batches: `{run.batch_count}`; batch size `{BATCH_SIZE}`",
            f"- Token usage: prompt `{run.usage.prompt_tokens}`, total `{run.usage.total_tokens}`",
            "",
            "## Chroma verification",
            "",
            "- Pre-write count: `329`",
            "- Post-write count: `375`",
            "- Distribution: 5326=`53`, 4458=`276`, 5607=`46`",
            f"- Existing-329 logical fingerprint: `{baseline_hash}`",
            "- Existing 329 IDs, documents, metadata, and vectors: preserved",
            "- 5607 stored-record validation: `46/46 PASS`",
            "- Canonical provenance validation: `46/46 PASS`",
            "- Cross-document storage-ID collisions: `0`",
            "- Idempotence: second indexing reused the 46 vectors; embedding API calls `0`; count `375`; duplicate IDs `0`",
            "- Persistence reopen: `PASS`",
            "",
            "Footnote bodies and the historical table remain deferred as documented in M12A/M12B.",
            "Retrieval evaluation and semantic queries were not run. Raw vectors and API secrets are not included.",
        ]
    ) + "\n"
    (REPORT_DIR / "m12c-5607-indexing.md").write_text(markdown, encoding="utf-8")
    print(json.dumps({"status": "PASS", "report": str(REPORT_DIR / "m12c-5607-indexing.json"), "api_calls": run.batch_count, "post_count": len(reopened_records)}))


if __name__ == "__main__":
    main()
