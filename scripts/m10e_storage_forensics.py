"""One-shot M10E POST inspection; never query, embed, or mutate a collection."""

from __future__ import annotations

import hashlib
import json
import os
import socket
import struct
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src import config


def canonical(value: Any) -> bytes:
    """Encode canonical compact UTF-8 JSON without nonfinite numbers."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def hashes(root: Path) -> dict[str, str]:
    """Hash every physical file, keyed by storage-relative POSIX path."""
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file()}


def main() -> None:
    """Perform exactly one get and persist only hashes and forensic summaries."""
    output = Path("reports/evaluation/m10e-storage-forensics.json")
    # An exclusive reservation prevents accidental repeat, even after failure.
    with output.open("x", encoding="utf-8") as stream:
        json.dump({"status": "reserved_do_not_repeat"}, stream)
    os.environ["RUN_OPENAI_INTEGRATION_TESTS"] = "0"
    os.environ["ANONYMIZED_TELEMETRY"] = "False"

    def forbidden(*args: Any, **kwargs: Any) -> Any:
        raise RuntimeError("Network forbidden during forensic inspection")

    socket.socket.connect = forbidden
    socket.socket.connect_ex = forbidden
    socket.getaddrinfo = forbidden
    import chromadb
    import numpy as np
    from chromadb.config import Settings

    root = Path(config.CHROMA_PATH).resolve()
    artifacts = [Path("reports/evaluation/m10e-retrieval-experiments" + ext)
                 for ext in (".json", ".csv", ".md")]
    report: dict[str, Any] = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "storage_path": str(root), "collection": config.COLLECTION_NAME,
        "chroma_version": chromadb.__version__,
        "authoritative_artifacts_before": {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                                            for p in artifacts},
        "serialization": {
            "json": "UTF-8, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False",
            "order": "All records sorted by ID ascending, without Unicode normalization",
            "ids": "SHA256(canonical JSON array of sorted IDs)",
            "documents_metadata": "SHA256(canonical JSON array of [ID, document, metadata]); compatible with M10E snapshot",
            "embedding_only": "SHA256(concatenated vectors in sorted-ID order; little-endian float32 C-order)",
            "full": "SHA256(concatenation per sorted record: uint64 little-endian JSON byte length, canonical [ID, document, metadata] bytes, uint64 little-endian vector byte length, vector bytes)",
        },
        "collection_get_calls": 1, "query_calls": 0, "openai_calls": 0,
        "explicit_mutation_api_calls": 0,
    }
    report["physical_before"] = hashes(root)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    client = chromadb.PersistentClient(path=str(root), settings=Settings(anonymized_telemetry=False))
    report["backend"] = client.get_settings().chroma_api_impl
    try:
        collection = client.get_collection(config.COLLECTION_NAME, embedding_function=None)
        payload = collection.get(include=["documents", "metadatas", "embeddings"])
    finally:
        client.close()
    report["physical_after"] = hashes(root)
    before, after = report["physical_before"], report["physical_after"]
    report["changed_files"] = [p for p in sorted(before.keys() | after.keys()) if before.get(p) != after.get(p)]
    ids = payload["ids"]
    assert len(ids) == len(set(ids)) == 329
    assert all(len(payload[k]) == 329 for k in ("documents", "metadatas", "embeddings"))
    rows = []
    embedding_hash, full_hash = hashlib.sha256(), hashlib.sha256()
    dimensions: Counter[int] = Counter()
    for i in sorted(range(len(ids)), key=lambda i: ids[i]):
        row = [ids[i], payload["documents"][i], payload["metadatas"][i]]
        assert isinstance(row[1], str) and isinstance(row[2], dict)
        vector = np.asarray(payload["embeddings"][i], dtype="<f4")
        assert vector.ndim == 1 and np.isfinite(vector).all()
        dimensions[len(vector)] += 1
        vector_bytes = vector.tobytes(order="C")
        row_bytes = canonical(row)
        embedding_hash.update(vector_bytes)
        for part in (row_bytes, vector_bytes):
            full_hash.update(struct.pack("<Q", len(part)))
            full_hash.update(part)
        rows.append(row)
    assert dimensions == {1536: 329}
    report.update(embedding_vector_count=len(rows), vector_dimensions=dict(dimensions),
                  all_embeddings_finite=True,
                  per_law_counts=dict(Counter(r[2]["legislation_number"] for r in rows)),
                  id_set_sha256=hashlib.sha256(canonical([r[0] for r in rows])).hexdigest(),
                  document_metadata_sha256=hashlib.sha256(canonical(rows)).hexdigest(),
                  embedding_only_post_sha256=embedding_hash.hexdigest(),
                  full_logical_post_sha256=full_hash.hexdigest())
    original = json.loads(artifacts[0].read_text(encoding="utf-8"))
    report["matches_original_nonvector_pre_and_post"] = all(
        report["document_metadata_sha256"] == original[k]["content_sha256"]
        and [r[0] for r in rows] == original[k]["ids"]
        and report["per_law_counts"] == original[k]["counts"]
        and len(rows) == original[k]["total"]
        for k in ("inventory_before", "inventory_after"))
    report["status"] = "completed_single_post_inspection"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
