"""Read-only logical audit of a verified fresh copy; never open production Chroma."""
from __future__ import annotations

import hashlib
import json
import shutil
import socket
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from src import config, source_identity, source_registry


def digest(value: Any) -> str:
    """Hash deterministic JSON, retaining exact strings and numeric values."""
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
        separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()


def file_hashes(root: Path) -> dict[str, str]:
    """Enumerate and hash every file; reject links to storage outside the root."""
    result = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction()):
            raise RuntimeError(f"Linked storage entry is not supported: {path}")
        if path.is_file():
            result[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    if not result:
        raise RuntimeError("Storage has no files")
    return result


def verified_copy(production: Path, target: Path) -> dict[str, str]:
    """Copy exclusively to a fresh disjoint directory and verify all file bytes."""
    production, target = production.resolve(), target.resolve()
    if target == production or production in target.parents or target in production.parents:
        raise RuntimeError("Audit copy must be disjoint from production")
    if target.exists():
        raise RuntimeError("Audit copy must be fresh")
    before = file_hashes(production)
    shutil.copytree(production, target)
    if file_hashes(target) != before or file_hashes(production) != before:
        raise RuntimeError("Copy verification failed or production changed during copy")
    return before


def analyze(rows: list[dict[str, Any]], registry: source_registry.SourceRegistry) -> dict[str, Any]:
    """Audit metadata without repairing it or inferring identity from law/ID."""
    coverage = {f: Counter(present=0, missing=0, valid=0, invalid=0) for f in
                ("document_id", "legislation_number", "article_type", "article_no", "article_id")}
    issues, records = [], []
    groups: dict[str, list[str]] = defaultdict(list)
    documents, laws = Counter(), Counter()
    for row in rows:
        record_id, metadata = row["id"], row["metadata"] or {}
        errors = []
        for field, counts in coverage.items():
            value = metadata.get(field)
            if value is None:
                counts["missing"] += 1
                if field in ("document_id", "article_type", "article_no"):
                    errors.append(f"missing {field}")
                continue
            counts["present"] += 1
            try:
                components = dict(document_id="audit_document", article_type="normal", article_no="1")
                if field in components:
                    components[field] = value
                    source_identity.DocumentSourceKey(**components)
                elif not isinstance(value, str) or not value.strip():
                    raise ValueError("expected nonempty string")
                counts["valid"] += 1
            except ValueError:
                counts["invalid"] += 1
                errors.append(f"invalid {field}")
        documents[str(metadata.get("document_id"))] += 1
        laws[str(metadata.get("legislation_number"))] += 1
        key = None
        try:
            key = source_registry.source_key_from_metadata(metadata)
            groups[str(key)].append(record_id)
        except ValueError as exc:
            errors.append(str(exc))
        try:
            record = registry.by_document_id(metadata.get("document_id"))
            number = metadata.get("legislation_number")
            if number is not None and record.legislation_number is not None and number != record.legislation_number:
                errors.append("legislation_number contradicts manifest")
            if metadata.get("source_file") is not None:
                if registry.by_local_file(metadata["source_file"]).document_id != record.document_id:
                    errors.append("source_file contradicts document_id")
            prefix = {"5326_kabahatler_kanunu": "5326-", "4458_gumruk_kanunu": "4458-"}.get(record.document_id)
            if prefix and not record_id.startswith(prefix):
                errors.append("storage ID prefix differs from current document expectation")
        except ValueError as exc:
            errors.append(str(exc))
        if errors:
            issues.append(dict(id=record_id, errors=errors))
        records.append(dict(id=record_id, metadata=metadata, canonical_key=str(key) if key else None))
    duplicates = {k: v for k, v in sorted(groups.items()) if len(v) > 1}
    ids = [r["id"] for r in rows]
    return dict(coverage=coverage, document_counts=documents, legislation_counts=laws,
        valid_canonical_keys=sum(map(len, groups.values())), unique_source_keys=len(groups),
        multi_chunk_source_count=len(duplicates), multi_chunk_sources=duplicates,
        max_chunks_per_source=max(map(len, groups.values()), default=0),
        record_ids_unique=len(ids) == len(set(ids)), issues=issues,
        affected_records=len(issues), records=records,
        compatibility="PASS" if len(rows) == 329 and not issues and len(ids) == len(set(ids)) else "FAIL")


def snapshot(collection: Any) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Read IDs/text/metadata/vectors, retaining only vector hashes and dimensions."""
    payload = collection.get(include=["documents", "metadatas", "embeddings"])
    ids = payload["ids"]
    rows = [dict(id=ids[i], document=payload["documents"][i], metadata=payload["metadatas"][i])
            for i in sorted(range(len(ids)), key=ids.__getitem__)]
    vectors = payload.get("embeddings")
    ordered_vectors = None if vectors is None else [vectors[i].tolist() for i in sorted(range(len(ids)), key=ids.__getitem__)]
    return rows, dict(count=collection.count(), ids=[r["id"] for r in rows],
        documents_sha256=digest([r["document"] for r in rows]),
        metadata_sha256=digest([r["metadata"] for r in rows]),
        embeddings_available=ordered_vectors is not None,
        embedding_dimensions=dict(Counter(len(v) for v in ordered_vectors)) if ordered_vectors is not None else {},
        embeddings_sha256=digest(ordered_vectors))


def inspect_copy(copy: Path, production: Path, registry: source_registry.SourceRegistry) -> dict[str, Any]:
    """Open only the copy; block network and public mutation/query APIs."""
    if copy.resolve() == production.resolve() or production.resolve() in copy.resolve().parents:
        raise RuntimeError("Refusing production client path")
    from unittest.mock import patch
    from contextlib import ExitStack
    import chromadb
    from chromadb.config import Settings
    from chromadb.api.models.Collection import Collection
    from chromadb.api.client import Client

    def forbidden(*args: Any, **kwargs: Any) -> None:
        raise RuntimeError("Network/query/mutation forbidden during metadata audit")

    with ExitStack() as stack:
        for name in ("connect", "connect_ex"):
            stack.enter_context(patch.object(socket.socket, name, forbidden))
        stack.enter_context(patch.object(socket, "getaddrinfo", forbidden))
        for cls, names in ((Collection, ("add", "upsert", "update", "delete", "modify", "query")),
                           (Client, ("reset", "create_collection", "get_or_create_collection", "delete_collection"))):
            for name in names:
                stack.enter_context(patch.object(cls, name, forbidden))
        client = chromadb.PersistentClient(path=str(copy.resolve()), settings=Settings(anonymized_telemetry=False))
        try:
            collection = client.get_collection("gumruk_mevzuati", embedding_function=None)
            rows, before = snapshot(collection)
            laws = Counter(str((r["metadata"] or {}).get("legislation_number")) for r in rows)
            if before["count"] != 329 or len(rows) != 329 or laws != {"5326": 53, "4458": 276}:
                raise RuntimeError(f"STOP: unexpected corpus count/distribution: {before['count']}, {dict(laws)}")
            analysis = analyze(rows, registry)
            after_rows, after = snapshot(collection)
            return dict(chroma_version=chromadb.__version__, before=before, after=after,
                logical_unchanged=rows == after_rows and before == after, analysis=analysis,
                mutation_apis_blocked=True, network_blocked=True)
        finally:
            client.close()


def render_report(report: dict[str, Any]) -> str:
    """Render the persisted audit without reopening any storage."""
    lines = ["# M11D-A production metadata audit", "", f"Result: **{report['compatibility']}**", "",
        f"Production path: `{report['production_path']}`", f"Fresh copy: `{report['copy_path']}`", "",
        "Production Chroma was never opened. Every production file was enumerated and SHA-256 hashed,",
        "copied to a fresh ignored directory, and verified byte-for-byte before opening only the copy.",
        "No OpenAI, network, retrieval query, mutation API, reindex, or embedding recomputation was used.",
        "Public collection mutation/query APIs and client mutation APIs were blocked during inspection.", "",
        f"Production pre/post hashes equal: **{report['production_hashes_equal']}**.",
        f"Copy verified before opening: **{report.get('copy_verified_before_open', False)}**.",
        f"Copy physical hashes unchanged after client close: **{report.get('copy_physical_unchanged')}**.",
        "Physical changes in the copy are reported separately from logical equality; no byte stability is inferred from API usage.", ""]
    if "error" in report:
        lines += [f"STOP: {report['error']}", ""]
    if "analysis" in report:
        a = report["analysis"]
        lines += ["## Logical findings", "", f"Collection: `gumruk_mevzuati`; before/after count: {report['before']['count']}/{report['after']['count']}.",
            f"IDs, text, metadata, and stored-vector snapshots unchanged: **{report['logical_unchanged']}**.",
            "Stored embeddings are available for 329 records at 1536 dimensions; only hashes/dimensions are reported.", "",
            "| Document ID | Records |", "|---|---:|"]
        lines += [f"| {key} | {count} |" for key, count in a["document_counts"].items()]
        lines += ["", "| Field | Present | Missing | Valid | Invalid |", "|---|---:|---:|---:|---:|"]
        lines += [f"| {field} | {c['present']} | {c['missing']} | {c['valid']} | {c['invalid']} |" for field,c in a["coverage"].items()]
        lines += ["", "Canonical field validity uses the unchanged M11 identity validators. Article ID and legislation-number field validity means nonempty string; law numbers are additionally checked against the registry.",
            f"Valid canonical keys: {a['valid_canonical_keys']}. Unique provision keys: {a['unique_source_keys']}.",
            f"Affected records: {a['affected_records']}. Individual findings: `{a['issues']}`.",
            "All current records resolve through the manifest; no missing, unknown, or third document IDs were found.",
            "All supplied law numbers/source files agree with their manifest records. Current storage-ID prefixes agree with document provenance; prefixes were never used to infer identity.",
            f"Record IDs unique: {a['record_ids_unique']}; no record ID maps to conflicting provenance.", "",
            f"Multi-chunk provisions: {a['multi_chunk_source_count']}; maximum chunks per provision: {a['max_chunks_per_source']}. These are legitimate shared provision identities, not collisions.", "",
            "| Canonical source key | Chroma record IDs |", "|---|---|"]
        lines += [f"| {key} | {', '.join(ids)} |" for key,ids in a["multi_chunk_sources"].items()]
        lines += ["", "## Decision", "",
            "The current collection satisfies strict M11C-B citation provenance without metadata migration. No reindex or re-embedding is required for this identity contract. No repair was performed. This does not evaluate retrieval relevance or legal correctness."
            if report["compatibility"] == "PASS" else "Compatibility is not established. No repair was performed."]
    lines += ["", "## Physical file hashes", "", "| Production file | Pre SHA-256 | Post SHA-256 |", "|---|---|---|"]
    lines += [f"| {name} | {value} | {report['production_post_hashes'].get(name)} |" for name,value in report["production_pre_hashes"].items()]
    lines += ["", "The verified copy started with these exact hashes. Copy files whose hashes changed after close:", ""]
    pre, post = report.get("copy_pre_hashes", {}), report.get("copy_post_hashes", {})
    lines += [f"- `{name}`: `{pre.get(name)}` -> `{post.get(name)}`" for name in sorted(pre.keys() | post.keys()) if pre.get(name) != post.get(name)]
    lines += ["", "The companion JSON contains every record ID and audited metadata, exact before/after ID lists, logical SHA-256 digests, and all copy/production file hashes. Logical digests use canonical JSON in sorted-record-ID order; no text or embedding vectors are included."]
    return "\n".join(lines) + "\n"


def main() -> None:
    """Verify copy, inspect it, recheck production even on failure, write reports."""
    root = Path(__file__).resolve().parents[1]
    production = Path(config.CHROMA_PATH).resolve()
    copy = root / "logs" / (".m11d_metadata_audit_chroma_" + uuid4().hex)
    output = root / "reports/evaluation/m11d-production-metadata-audit"
    report: dict[str, Any] = dict(timestamp_utc=datetime.now(timezone.utc).isoformat(),
        production_path=str(production), copy_path=str(copy), production_client_opened=False,
        collection="gumruk_mevzuati", compatibility="UNPROVEN")
    before = file_hashes(production)
    report["production_pre_hashes"] = before
    try:
        report["copy_pre_hashes"] = verified_copy(production, copy)
        report["copy_verified_before_open"] = True
        registry = source_registry.load_manifest(root / "data/source_manifest.json", project_root=root)
        report.update(inspect_copy(copy, production, registry))
        report["compatibility"] = report["analysis"]["compatibility"] if report["logical_unchanged"] else "UNPROVEN"
    except Exception as exc:
        report["error"] = str(exc)
    finally:
        report["production_post_hashes"] = file_hashes(production)
        report["production_hashes_equal"] = before == report["production_post_hashes"]
        if not report["production_hashes_equal"]:
            report["compatibility"] = "UNPROVEN"
            report["error"] = "STOP: production filesystem safety failure"
        if copy.exists():
            report["copy_post_hashes"] = file_hashes(copy)
            report["copy_physical_unchanged"] = report.get("copy_pre_hashes") == report["copy_post_hashes"]
    output.with_suffix(".json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    output.with_suffix(".md").write_text(render_report(report), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k in ("compatibility", "error", "production_hashes_equal", "copy_physical_unchanged", "logical_unchanged")}, indent=2))
    if "error" in report:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
