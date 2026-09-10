"""Offline contracts for canonical identity and the unchanged legacy bridge."""

from __future__ import annotations

import ast
import builtins
import importlib
import io
import json
from dataclasses import FrozenInstanceError, fields
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from src import evaluate, evaluate_multilaw, source_identity as identity


@pytest.mark.parametrize("document_id", [
    "5326_kabahatler_kanunu", "4458_gumruk_kanunu", "gumruk_yonetmeligi", "2009_15481_bkk", "law-a_2",
])
def test_canonical_document_construction(document_id: str) -> None:
    key = identity.DocumentSourceKey(document_id, "normal", "27")
    assert key.document_id == document_id
    assert key.article_no == "27"


@pytest.mark.parametrize("raw,expected", [
    ("42/A", "42/a"), ("42-a", "42/a"), ("42_A", "42/a"), ("42 / A", "42/a"),
    (" 42 /A ", "42/a"), ("\t42 / A\n", "42/a"), ("165/B", "165/b"),
    ("001", "001"), ("001-A-02", "001/a/02"), ("27", "27"), ("42/ç", "42/ç"),
])
def test_normalization_matches_historical_supported_aliases(raw: str, expected: str) -> None:
    key = identity.DocumentSourceKey("4458_gumruk_kanunu", "normal", raw)
    assert key.article_no == expected == evaluate.normalize_article_no(raw)


def test_immutable_hashable_value_identity() -> None:
    key = identity.DocumentSourceKey("law_a", "normal", "42/A")
    equal = identity.DocumentSourceKey("law_a", "normal", "42-a")
    with pytest.raises(FrozenInstanceError):
        key.article_no = "99"
    with pytest.raises(FrozenInstanceError):
        del key.document_id
    assert key == equal
    assert hash(key) == hash(equal)
    assert len({key, equal}) == 1
    assert {key: "value"}[equal] == "value"


def test_ordering_is_lexical_three_field_order() -> None:
    components = [("law_b", "normal", "1"), ("law_a", "normal", "2"),
                  ("law_a", "gecici", "1"), ("law_a", "normal", "10")]
    keys = [identity.DocumentSourceKey(*values) for values in components]
    assert [(k.document_id, k.article_type, k.article_no) for k in sorted(keys)] == sorted(components)
    assert sorted(reversed(keys)) == sorted(keys)


@pytest.mark.parametrize("article_no", ["27", "165/b", "001/a/02"])
def test_string_serialization_and_canonical_round_trip(article_no: str) -> None:
    key = identity.DocumentSourceKey("4458_gumruk_kanunu", "normal", article_no)
    expected = f"4458_gumruk_kanunu/normal/{article_no}"
    assert str(key) == expected
    assert identity.DocumentSourceKey.parse(expected) == key
    assert str(identity.DocumentSourceKey.parse(expected)) == expected


@pytest.mark.parametrize("serialized", [
    "4458_gumruk_kanunu/normal/165-B", "4458_gumruk_kanunu/normal/165_B",
    "4458_gumruk_kanunu/normal/165/B", "4458_gumruk_kanunu/normal/165 / b",
    "4458_gumruk_kanunu/normal/27 ", " law_a/normal/27", "law_a/normal",
    "law_a/normal/", "law_a/normal/27/", "", None, 27,
])
def test_parser_rejects_aliases_and_malformed_encodings(serialized: Any) -> None:
    with pytest.raises(identity.SourceIdentityError):
        identity.DocumentSourceKey.parse(serialized)


def test_json_round_trip_exact_fields_and_fresh_dictionary() -> None:
    key = identity.DocumentSourceKey("law_a", "gecici", "001")
    expected = {"document_id": "law_a", "article_type": "gecici", "article_no": "001"}
    assert key.to_dict() == expected
    assert identity.DocumentSourceKey.from_dict(json.loads(json.dumps(key.to_dict()))) == key
    copy = key.to_dict()
    copy["document_id"] = "law_b"
    assert key.document_id == "law_a"
    assert {f.name for f in fields(key)} == {"document_id", "article_type", "article_no"}
    assert not hasattr(key, "legislation_number")


def test_component_object_normalizes_aliases_through_constructor() -> None:
    raw = {"document_id": "law_a", "article_type": "normal", "article_no": "42_A"}
    key = identity.DocumentSourceKey.from_dict(raw)
    assert key.article_no == "42/a"
    assert raw["article_no"] == "42_A"


@pytest.mark.parametrize("value", [
    {}, {"document_id": "law_a", "article_no": "27"},
    {"legislation_number": "5326", "article_type": "normal", "article_no": "27"},
    {"document_id": "law_a", "article_type": "normal", "article_no": "27", "legislation_number": "5326"},
    {"document_id": "law_a", "article_type": "normal", "article_no": "27", "source_identity_schema": "v1"},
    {"document_id": None, "article_type": "normal", "article_no": "27"},
    {"document_id": "law_a", "article_type": "normal", "article_no": 27},
    None, [], "law_a/normal/27",
])
def test_json_rejects_missing_extra_legacy_and_invalid_fields(value: Any) -> None:
    with pytest.raises(identity.SourceIdentityError):
        identity.DocumentSourceKey.from_dict(value)


@pytest.mark.parametrize("value", [
    "LAW_A", "law/a", "law a", " law_a", "law_a ", "", "_law", "law_",
    "-law", "law-", "law__a", "law--a", "law_-a", "law\x00a", "law\na",
    "gümrük", "law.a", None, 5326, True,
])
def test_invalid_document_ids_fail_on_direct_construction(value: Any) -> None:
    with pytest.raises(identity.SourceIdentityError):
        identity.DocumentSourceKey(value, "normal", "27")


@pytest.mark.parametrize("kind", ["normal", "ek", "gecici", "islenemeyen_hukum"])
def test_exact_supported_article_namespaces(kind: str) -> None:
    assert identity.DocumentSourceKey("law_a", kind, "1").article_type == kind


@pytest.mark.parametrize("kind", ["annex", "appendix", "Normal", " normal", "", None, 1, []])
def test_invalid_article_types_fail_on_direct_construction(kind: Any) -> None:
    with pytest.raises(identity.SourceIdentityError):
        identity.DocumentSourceKey("law_a", kind, "27")


@pytest.mark.parametrize("value", [
    "", " ", "42//", "42/", " /a", "42//a", "Madde 27", "27.a", "4 2/a",
    "42/a b", "42/\x00a", "42/\x1fa b", "42/%61", "42:a", "42--a", None, 27, True,
])
def test_invalid_article_numbers_fail_on_direct_construction(value: Any) -> None:
    with pytest.raises(identity.SourceIdentityError):
        identity.DocumentSourceKey("law_a", "normal", value)


def test_distinct_documents_types_and_numeric_spellings_do_not_collide() -> None:
    keys = [identity.DocumentSourceKey(*parts) for parts in (
        ("law_a", "normal", "27"), ("law_b", "normal", "27"),
        ("law_a", "gecici", "1"), ("law_a", "islenemeyen_hukum", "1"),
        ("law_a", "normal", "001"), ("law_a", "normal", "1"),
        ("law_a", "normal", "1/a/2"), ("law_a", "normal", "2/a/1"),
    )]
    assert len(set(keys)) == len(keys)
    assert identity.DocumentSourceKey("gumruk_yonetmeligi", "normal", "27").document_id == "gumruk_yonetmeligi"


def test_identity_equality_is_not_legacy_tuple_equality() -> None:
    canonical = identity.DocumentSourceKey("5326", "normal", "4")
    legacy = evaluate_multilaw.QualifiedSourceKey.build("5326", "normal", "4")
    assert canonical != legacy and legacy != canonical
    assert canonical != ("5326", "normal", "4")
    assert len({canonical, legacy}) == 2


@pytest.mark.parametrize("number,article,expected", [
    ("5326", "4", "5326_kabahatler_kanunu/normal/4"),
    ("4458", "165/a", "4458_gumruk_kanunu/normal/165/a"),
])
def test_actual_legacy_keys_resolve_through_explicit_current_registry(number: str, article: str, expected: str) -> None:
    legacy = evaluate_multilaw.QualifiedSourceKey.build(number, "normal", article)
    assert str(identity.to_document_source_key(legacy, identity.CURRENT_LEGACY_REGISTRY)) == expected


def test_registry_contents_are_reviewed_immutable_and_copied() -> None:
    assert dict(identity.CURRENT_LEGACY_REGISTRY) == {
        "5326": "5326_kabahatler_kanunu", "4458": "4458_gumruk_kanunu"}
    with pytest.raises(TypeError):
        identity.CURRENT_LEGACY_REGISTRY["5607"] = "unreviewed"
    pairs = [("5326", "law_a"), ("5326", "law_a")]
    registry = identity.build_legacy_registry(pairs)
    pairs.append(("4458", "law_b"))
    assert dict(registry) == {"5326": "law_a"}
    with pytest.raises(TypeError):
        registry["5326"] = "law_b"


def test_registry_rejects_conflict_in_either_record_order() -> None:
    pairs = [("5326", "law_a"), ("5326", "law_b")]
    for records in (pairs, list(reversed(pairs))):
        with pytest.raises(identity.SourceIdentityError, match="ambiguous"):
            identity.build_legacy_registry(records)


@pytest.mark.parametrize("number", ["5607", "2009/15481", " 5326 "])
def test_unreviewed_or_nonmatching_legacy_number_fails(number: str) -> None:
    legacy = evaluate_multilaw.QualifiedSourceKey.build(number, "normal", "27")
    with pytest.raises(identity.SourceIdentityError, match="unresolved"):
        identity.to_document_source_key(legacy, identity.CURRENT_LEGACY_REGISTRY)


def test_adapter_uses_injected_registry_and_preserves_namespace() -> None:
    legacy = evaluate_multilaw.QualifiedSourceKey("4458", "islenemeyen_hukum", "001_A")
    registry = identity.build_legacy_registry([("4458", "synthetic_doc")])
    converted = identity.to_document_source_key(legacy, registry)
    assert str(converted) == "synthetic_doc/islenemeyen_hukum/001/a"
    assert legacy.article_no == "001_A"


@pytest.mark.parametrize("registry", [
    {"5326": ["law_a", "law_b"]}, {"5326": "LAW_A"}, {"": "law_a"},
    {5326: "law_a"}, {"5326": None}, None,
])
def test_adapter_rejects_ambiguous_or_invalid_supplied_mapping(registry: Any) -> None:
    legacy = evaluate_multilaw.QualifiedSourceKey.build("5326", "normal", "4")
    with pytest.raises(identity.SourceIdentityError):
        identity.to_document_source_key(legacy, registry)


@pytest.mark.parametrize("legacy", [
    object(), {"legislation_number": "5326", "article_type": "normal", "article_no": "4"},
    SimpleNamespace(legislation_number=None, article_type="normal", article_no="4"),
    SimpleNamespace(legislation_number="5326", article_type="annex", article_no="4"),
    SimpleNamespace(legislation_number="5326", article_type="normal", article_no="4//"),
])
def test_malformed_structural_legacy_key_fails_closed(legacy: Any) -> None:
    with pytest.raises(identity.SourceIdentityError):
        identity.to_document_source_key(legacy, identity.CURRENT_LEGACY_REGISTRY)


def test_historical_factory_and_constructor_behavior_are_unchanged() -> None:
    legacy = evaluate_multilaw.QualifiedSourceKey.build(" 5326 ", "normal", "42_A")
    assert legacy.legislation_number == " 5326 "
    assert legacy.article_no == "42/a"
    direct = evaluate_multilaw.QualifiedSourceKey("5326", "normal", "42_A")
    assert direct.article_no == "42_A"  # Legacy direct constructor remains permissive.
    assert str(direct) == "5326/normal/42_A"
    assert direct != evaluate_multilaw.QualifiedSourceKey.build("5326", "normal", "42_A")
    assert evaluate.normalize_article_no("27.a") == "27.a"  # New strict validation is not backported.
    with pytest.raises(evaluate_multilaw.MultiLawEvaluationError):
        evaluate_multilaw.QualifiedSourceKey.build(None, "normal", "4")


def test_dependency_boundary_and_import_perform_no_application_io(monkeypatch: pytest.MonkeyPatch) -> None:
    tree = ast.parse(Path(identity.__file__).read_text(encoding="utf-8"))
    imports = {node.module.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
    imports.update(alias.name.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names)
    assert imports <= {"__future__", "re", "collections", "dataclasses", "types", "typing"}

    def forbidden(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("Identity import must not read files or discover a registry")

    monkeypatch.setattr(builtins, "open", forbidden)
    monkeypatch.setattr(io, "open", forbidden)
    reloaded = importlib.reload(identity)
    assert str(reloaded.DocumentSourceKey("law_a", "normal", "42_A")) == "law_a/normal/42/a"
    assert set(reloaded.CURRENT_LEGACY_REGISTRY) == {"5326", "4458"}
