"""Offline manifest admission, canonical views and unchanged ranking contracts."""

from __future__ import annotations

import ast
import builtins
import copy
import io
import json
import sys
from dataclasses import FrozenInstanceError, asdict, replace
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest

from src import chunk, index, ingest, retrieve, source_registry as registry
from src import source_identity

ROOT = Path(__file__).resolve().parents[1]


def _entry(**changes: Any) -> dict[str, Any]:
    return {"document_id": "synthetic_law", "title": "Synthetic title", "document_type": "Synthetic",
            "local_file": "data/raw/synthetic.docx", "legislation_number": "123", **changes}


def _registry(tmp_path: Path, *entries: dict[str, Any]) -> registry.SourceRegistry:
    return registry.SourceRegistry(tuple(registry.DocumentRecord.from_dict(e) for e in entries), tmp_path)


def _write_json(path: Path, value: Any) -> Path:
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def _paragraph_root(**changes: Any) -> dict[str, Any]:
    return {"document_id": "synthetic_law", "source_file": "data/raw/synthetic.docx", "paragraph_count": 1,
            "paragraphs": [{"index": 7, "text": "Madde 27- (1) Synthetic test text.", "style_name": "Normal"}],
            **changes}


def test_current_manifest_records_and_all_explicit_lookups() -> None:
    path = ROOT / "data/source_manifest.json"
    before = path.read_bytes()
    actual = registry.load_manifest(path, project_root=ROOT)
    assert {d.document_id for d in actual.documents} == {
        "5326_kabahatler_kanunu",
        "4458_gumruk_kanunu",
        "5607_kacakcilikla_mucadele_kanunu",
    }
    raw = json.loads(before)
    for expected in raw:
        record = actual.by_document_id(expected["document_id"])
        assert asdict(record) == expected
        assert actual.by_local_file(expected["local_file"]) is record
        assert actual.by_local_file(ROOT / expected["local_file"]) is record
        assert actual.unique_by_legislation_number(expected["legislation_number"]) is record
    assert path.read_bytes() == before


@pytest.mark.parametrize("method,value", [
    ("by_document_id", "absent"), ("by_local_file", "absent.docx"),
    ("unique_by_legislation_number", "5607"), ("unique_by_legislation_number", None),
])
def test_unregistered_lookup_fails_explicitly(tmp_path: Path, method: str, value: Any) -> None:
    sources = _registry(tmp_path, _entry())
    with pytest.raises(registry.SourceRegistryError):
        getattr(sources, method)(value)


@pytest.mark.parametrize("second,message", [
    (_entry(local_file="other.docx", legislation_number="456"), "duplicate document_id"),
    (_entry(document_id="other", legislation_number="456"), "duplicate local_file"),
    (_entry(document_id="other", local_file="data/raw/../raw/synthetic.docx", legislation_number="456"), "duplicate local_file"),
    (_entry(document_id="other", local_file="other.docx"), "ambiguous legislation_number"),
])
def test_duplicate_and_ambiguous_records_fail_in_either_order(tmp_path: Path, second: dict[str, Any], message: str) -> None:
    for entries in ([_entry(), second], [second, _entry()]):
        path = _write_json(tmp_path / "manifest.json", entries)
        with pytest.raises(registry.SourceRegistryError, match=message):
            registry.load_manifest(path, project_root=tmp_path)


def test_absolute_relative_path_aliases_are_one_mapping(tmp_path: Path) -> None:
    second = _entry(document_id="other", local_file=str(tmp_path / "data/raw/synthetic.docx"), legislation_number="456")
    with pytest.raises(registry.SourceRegistryError, match="duplicate local_file"):
        _registry(tmp_path, _entry(), second)


def test_document_records_and_registry_are_immutable_copies(tmp_path: Path) -> None:
    raw = _entry()
    record = registry.DocumentRecord.from_dict(raw)
    records = [record]
    sources = registry.SourceRegistry(records, tmp_path)
    records.clear()
    raw["title"] = "changed"
    assert sources.documents == (record,)
    assert record.title == "Synthetic title"
    with pytest.raises(FrozenInstanceError):
        record.document_id = "other"
    with pytest.raises(FrozenInstanceError):
        sources.documents = ()
    with pytest.raises(TypeError):
        sources._documents["other"] = record


@pytest.mark.parametrize("changes", [
    {"document_id": "UPPER"}, {"document_id": "a/b"}, {"document_id": "a__b"},
    {"document_id": None}, {"title": ""}, {"title": []}, {"document_type": " "},
    {"local_file": None}, {"local_file": ""}, {"local_file": " file.docx"}, {"local_file": "a\x00b"},
    {"legislation_number": 5326}, {"legislation_number": " "}, {"issuing_authority": []},
    {"official_source_url": False}, {"retrieved_at": 2026}, {"notes": {}}, {"invented_field": "x"},
])
def test_malformed_entry_rejected(tmp_path: Path, changes: dict[str, Any]) -> None:
    path = _write_json(tmp_path / "manifest.json", [_entry(**changes)])
    with pytest.raises(registry.SourceRegistryError):
        registry.load_manifest(path, project_root=tmp_path)


@pytest.mark.parametrize("payload", [{}, None, "text", [None], [[]], [{}]])
def test_invalid_manifest_shape_rejected(tmp_path: Path, payload: Any) -> None:
    path = _write_json(tmp_path / "manifest.json", payload)
    with pytest.raises(registry.SourceRegistryError):
        registry.load_manifest(path, project_root=tmp_path)


@pytest.mark.parametrize("missing", ["document_id", "title", "document_type", "local_file"])
def test_required_manifest_fields_are_not_guessed(missing: str) -> None:
    entry = _entry()
    del entry[missing]
    with pytest.raises(registry.SourceRegistryError):
        registry.DocumentRecord.from_dict(entry)


def test_missing_or_invalid_json_manifest_fails(tmp_path: Path) -> None:
    path = tmp_path / "manifest.json"
    with pytest.raises(registry.SourceRegistryError):
        registry.load_manifest(path, project_root=tmp_path)
    path.write_text("{broken", encoding="utf-8")
    with pytest.raises(registry.SourceRegistryError):
        registry.load_manifest(path, project_root=tmp_path)


def test_duplicate_json_identity_fields_are_not_silently_overwritten(tmp_path: Path) -> None:
    path = tmp_path / "manifest.json"
    path.write_text('[{"document_id":"law_a","document_id":"law_b"}]', encoding="utf-8")
    with pytest.raises(registry.SourceRegistryError, match="duplicate manifest object field"):
        registry.load_manifest(path, project_root=tmp_path)


def test_numberless_synthetic_documents_are_independent(tmp_path: Path) -> None:
    first = _entry(document_id="synthetic_regulation_a", legislation_number=None)
    second = _entry(document_id="synthetic_regulation_b", local_file="other.docx")
    del second["legislation_number"]
    sources = _registry(tmp_path, first, second)
    assert len(sources.documents) == 2
    assert all(d.legislation_number is None for d in sources.documents)
    for entry in (first, second):
        admitted = sources.admit_paragraph_root({"document_id": entry["document_id"], "source_file": entry["local_file"]})
        assert admitted.document_id == entry["document_id"]
    with pytest.raises(registry.SourceRegistryError):
        sources.unique_by_legislation_number("123")


@pytest.mark.parametrize("root", [
    _paragraph_root(document_id="another_document"), _paragraph_root(document_id=None),
    _paragraph_root(source_file="unregistered.docx"), _paragraph_root(source_file=None), {}, None,
])
def test_root_mismatch_or_missing_provenance_fails(tmp_path: Path, root: Any) -> None:
    with pytest.raises(registry.SourceRegistryError):
        _registry(tmp_path, _entry()).admit_paragraph_root(root)


def test_matching_root_resolves_once_and_returns_single_record(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    sources = _registry(tmp_path, _entry())
    root = _paragraph_root(legislation_number="untrusted_root_value")
    before = copy.deepcopy(root)
    calls = []
    lookup = registry.SourceRegistry.by_local_file

    def tracked(self: registry.SourceRegistry, path: str | Path) -> registry.DocumentRecord:
        calls.append(path)
        return lookup(self, path)

    monkeypatch.setattr(registry.SourceRegistry, "by_local_file", tracked)
    record = sources.admit_paragraph_root(root)
    assert record is sources.by_document_id("synthetic_law")
    assert record.legislation_number == "123"
    assert calls == [root["source_file"]]
    assert root == before


def test_parse_admission_fails_before_parser_on_mixed_document_identity(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    manifest = _write_json(tmp_path / "manifest.json", [
        _entry(), _entry(document_id="other", local_file="other.docx", legislation_number="456"),
    ])
    paragraphs = _write_json(tmp_path / "paragraphs.json", _paragraph_root(document_id="other"))
    monkeypatch.setattr(ingest, "SOURCE_MANIFEST_PATH", manifest)

    def forbidden(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("Mismatched document must not reach the parser")

    monkeypatch.setattr(chunk, "parse_articles", forbidden)
    with pytest.raises(registry.SourceRegistryError, match="does not match"):
        chunk.parse_document(paragraphs)


def test_parse_admission_uses_resolved_document_metadata_and_preserves_ids(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    manifest = _write_json(tmp_path / "manifest.json", [_entry()])
    paragraphs = _write_json(tmp_path / "paragraphs.json", _paragraph_root(legislation_number="999"))
    monkeypatch.setattr(ingest, "SOURCE_MANIFEST_PATH", manifest)
    result = chunk.build_chunks_document(paragraphs)
    stored = result["chunks"][0]
    assert stored["document_id"] == "synthetic_law"
    assert stored["legislation_number"] == "123"
    assert stored["article_id"] == "123-madde-27"
    assert stored["chunk_id"] == "123-madde-27-chunk-001"
    assert str(registry.source_key_from_metadata(stored)) == "synthetic_law/normal/27"


def test_real_5326_parse_outputs_remain_identical_to_processed_files() -> None:
    base = ROOT / "data/processed/5326-kabahatler-kanunu"
    if not all(base.with_suffix(suffix).exists() for suffix in (".paragraphs.json", ".articles.json", ".chunks.json")):
        pytest.skip("local processed 5326 artifacts unavailable")
    assert chunk.parse_document(base.with_suffix(".paragraphs.json")) == json.loads(base.with_suffix(".articles.json").read_text(encoding="utf-8"))
    assert chunk.build_chunks_document(base.with_suffix(".paragraphs.json")) == json.loads(base.with_suffix(".chunks.json").read_text(encoding="utf-8"))


def test_canonical_keys_from_actual_article_and_chunk_do_not_mutate_fields() -> None:
    paragraphs = [ingest.ExtractedParagraph(index=0, text="Madde 165/B- (1) Synthetic text.", style_name="Normal")]
    article = chunk.parse_articles(paragraphs, document_id="synthetic_regulation", legislation_number=None)[0]
    piece = chunk.build_chunks([article])[0]
    before = (asdict(article), asdict(piece))
    expected = source_identity.DocumentSourceKey("synthetic_regulation", "normal", "165/b")
    assert registry.provision_source_key(article) == expected
    assert registry.provision_source_key(piece) == expected
    assert (asdict(article), asdict(piece)) == before
    assert article.article_no == "165/B"


@pytest.mark.parametrize("document_id", [None, "", "UPPER"])
def test_missing_or_invalid_provision_document_id_does_not_fall_back(document_id: Any) -> None:
    provision = SimpleNamespace(document_id=document_id, legislation_number="5326", article_type="normal", article_no="27")
    with pytest.raises(source_identity.SourceIdentityError):
        registry.provision_source_key(provision)


@pytest.mark.parametrize("metadata", [
    {"legislation_number": "5326", "article_type": "normal", "article_no": "4"},
    {"document_id": "law_a", "article_no": "4"},
    {"document_id": "law_a", "article_type": "normal", "article_no": "4//"}, None,
])
def test_canonical_accessor_is_opt_in_and_fails_on_incomplete_retrieval_metadata(metadata: Any) -> None:
    result = retrieve.RetrievedChunk(1, "unchanged-id", "unchanged text", metadata, 0.75)
    assert result.chunk_id == "unchanged-id" and result.distance == 0.75
    before = copy.deepcopy(result)
    with pytest.raises(source_identity.SourceIdentityError):
        registry.retrieved_source_key(result)
    assert result == before


def test_retrieved_provenance_is_observational_not_a_ranking_operation(monkeypatch: pytest.MonkeyPatch) -> None:
    records = [
        retrieve.RetrievedChunk(1, "4458-madde-27-chunk-001", "first text", {
            "document_id": "4458_gumruk_kanunu", "legislation_number": "4458", "article_type": "normal",
            "article_no": "27", "paragraph_numbers": ["1", "2"]}, 0.9),
        retrieve.RetrievedChunk(2, "5326-madde-4-chunk-001", "second text", {
            "document_id": "5326_kabahatler_kanunu", "legislation_number": "5326", "article_type": "normal",
            "article_no": "4", "nested": {"example": [1, 2]}}, 0.1),
    ]
    before = copy.deepcopy(records)
    references = [id(record) for record in records]

    def forbidden(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("No retrieval, ranking or embedding function may be called")

    monkeypatch.setattr(retrieve, "retrieve", forbidden)
    monkeypatch.setattr(retrieve.embed, "embed_texts", forbidden)
    keys = [registry.retrieved_source_key(record) for record in records]
    assert keys == [source_identity.DocumentSourceKey("4458_gumruk_kanunu", "normal", "27"),
                    source_identity.DocumentSourceKey("5326_kabahatler_kanunu", "normal", "4")]
    assert records == before
    assert [id(record) for record in records] == references
    assert [record.distance for record in records] == [0.9, 0.1]  # Deliberately not sorted.


def test_existing_index_metadata_contract_needs_no_migration_or_builder_change() -> None:
    piece = chunk.Chunk(chunk_id="storage-id", article_id="article-id", document_id="synthetic_law",
        legislation_number="123", article_no="27", article_type="normal", article_title="Title",
        section_context="Section", text="Synthetic text", paragraph_numbers=["1"],
        source_paragraph_start=7, source_paragraph_end=9, footnote_references=[2])
    before = asdict(piece)
    metadata = index.build_chroma_metadata(piece)  # Pure builder; no client or collection.
    for name in ("document_id", "legislation_number", "article_type", "article_no", "article_id", "article_title",
                 "section_context", "paragraph_numbers", "source_paragraph_start", "source_paragraph_end", "footnote_references"):
        assert metadata[name] == before[name]
    assert asdict(piece) == before
    numberless = index.build_chroma_metadata(replace(piece, legislation_number=None))
    assert "legislation_number" not in numberless
    assert registry.source_key_from_metadata(numberless) == registry.provision_source_key(piece)


def test_registry_import_has_no_file_io_or_production_dependency(monkeypatch: pytest.MonkeyPatch) -> None:
    source = Path(registry.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
    imports.update(alias.name for n in ast.walk(tree) if isinstance(n, ast.Import) for alias in n.names)
    assert imports <= {"__future__", "json", "os", "re", "collections.abc", "dataclasses", "pathlib", "types", "typing", "src"}
    code = compile(source, registry.__file__, "exec")
    module = ModuleType("registry_import_probe")
    monkeypatch.setitem(sys.modules, module.__name__, module)

    def forbidden(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("Registry import must not perform filesystem I/O")

    monkeypatch.setattr(builtins, "open", forbidden)
    monkeypatch.setattr(io, "open", forbidden)
    monkeypatch.setattr(Path, "resolve", forbidden)
    exec(code, module.__dict__)
    assert callable(module.load_manifest)
