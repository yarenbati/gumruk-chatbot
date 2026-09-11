"""Pure document-centered provision identity and explicit legacy conversion.

Historical QualifiedSourceKey semantics remain owned by the evaluation module.
This module neither imports that module nor discovers registry data through I/O.
Existing article/chunk IDs, metadata, citations and ranking behavior are untouched.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Protocol

_DOCUMENT_ID_PATTERN = re.compile(r"[a-z0-9]+(?:[_-][a-z0-9]+)*")
_ARTICLE_TYPES = frozenset({"normal", "ek", "gecici", "islenemeyen_hukum"})
_IDENTITY_FIELDS = frozenset({"document_id", "article_type", "article_no"})
_TURKISH_UPPERCASE_LETTERS = frozenset("ÇĞİÖŞÜ")


class SourceIdentityError(ValueError):
    """Invalid canonical identity, serialized key or legacy resolution."""


def _validate_document_id(document_id: str) -> None:
    if not isinstance(document_id, str) or not _DOCUMENT_ID_PATTERN.fullmatch(document_id):
        raise SourceIdentityError("document_id must match [a-z0-9]+(?:[_-][a-z0-9]+)*")


def _normalize_article_no(article_no: str) -> str:
    if not isinstance(article_no, str):
        raise SourceIdentityError("article_no must be a string")
    # Deliberately duplicate the tiny historical algorithm to avoid importing
    # evaluation/retrieval dependencies. Tests pin parity for supported aliases.
    normalized = article_no.strip()
    normalized = re.sub(r"[-_]", "/", normalized)
    normalized = re.sub(r"\s*/\s*", "/", normalized)
    normalized = normalized.strip()
    # Keep the historical lower-case form for ASCII aliases. For non-ASCII
    # suffixes, upper-case the segment instead of using str.lower(): Turkish
    # capital İ lower-cases to ``i`` plus a combining dot, which is not a
    # stable alphanumeric component and can collide with ASCII I in storage.
    normalized = "/".join(
        segment.upper() if any(character in _TURKISH_UPPERCASE_LETTERS for character in segment)
        else segment.lower()
        for segment in normalized.split("/")
    )
    if not all(segment.isalnum() for segment in normalized.split("/")):
        raise SourceIdentityError("article_no must have nonempty alphanumeric slash-separated segments")
    return normalized


@dataclass(frozen=True, order=True)
class DocumentSourceKey:
    """Immutable provision identity with normalized article-number components.

    Construction accepts supported article aliases; document_id and article_type
    must already be canonical. Equality is type-specific; ordering is lexical
    tuple order, not legal or source order. Hashes are for Python sets/dicts,
    not persistent cross-process identifiers. Use str(key) for stable encoding.
    """

    document_id: str
    article_type: str
    article_no: str

    def __post_init__(self) -> None:
        """Enforce validation and normalization even on direct construction."""
        _validate_document_id(self.document_id)
        if not isinstance(self.article_type, str) or self.article_type not in _ARTICLE_TYPES:
            raise SourceIdentityError("article_type must be normal, ek, gecici or islenemeyen_hukum")
        object.__setattr__(self, "article_no", _normalize_article_no(self.article_no))

    def __str__(self) -> str:
        """Return document_id/article_type/article_no; article_no may contain /."""
        return f"{self.document_id}/{self.article_type}/{self.article_no}"

    @classmethod
    def parse(cls, value: str) -> DocumentSourceKey:
        """Parse only canonical encodings; aliases belong in component construction."""
        if not isinstance(value, str):
            raise SourceIdentityError("serialized source key must be a string")
        parts = value.split("/", 2)
        if len(parts) != 3:
            raise SourceIdentityError("serialized source key must contain three components")
        key = cls(*parts)
        if str(key) != value:
            raise SourceIdentityError("serialized source key is not canonical")
        return key

    def to_dict(self) -> dict[str, str]:
        """Return a fresh canonical component object without an enclosing schema tag."""
        return {"document_id": self.document_id, "article_type": self.article_type, "article_no": self.article_no}

    @classmethod
    def from_dict(cls, value: Mapping[str, str]) -> DocumentSourceKey:
        """Validate exactly three identity fields; component article aliases normalize.

        Unlike parse(), this constructs from components. Extra legacy fields or
        schema tags are rejected; legislation_number never substitutes for an ID.
        """
        if not isinstance(value, Mapping) or set(value) != _IDENTITY_FIELDS:
            raise SourceIdentityError("identity object requires exactly document_id, article_type and article_no")
        return cls(value["document_id"], value["article_type"], value["article_no"])


class LegacySourceKey(Protocol):
    """Read-only structural interface implemented by the existing legacy key."""

    @property
    def legislation_number(self) -> str:
        """Return the legacy number without implicit trimming or rewriting."""
        ...

    @property
    def article_type(self) -> str:
        """Return the legacy provision namespace."""
        ...

    @property
    def article_no(self) -> str:
        """Return the legacy article number, possibly a supported alias."""
        ...


def build_legacy_registry(pairs: Iterable[tuple[str, str]]) -> Mapping[str, str]:
    """Copy explicit number/ID pairs into an immutable, validated registry.

    Conflicting repeated numbers fail; identical repeated mappings are harmless.
    Pass the original pairs, not a dict that has already discarded duplicates.
    Numbers are exact nonblank strings, with no numeric parsing or fallback.
    """
    resolved: dict[str, str] = {}
    for number, document_id in pairs:
        if not isinstance(number, str) or not number.strip():
            raise SourceIdentityError("legacy legislation_number must be a nonempty string")
        _validate_document_id(document_id)
        if number in resolved and resolved[number] != document_id:
            raise SourceIdentityError(f"ambiguous legacy mapping for {number!r}")
        resolved[number] = document_id
    return MappingProxyType(resolved)


# Explicit audited mapping, never extended from a manifest or a gold dataset.
# A constant is appropriate for this historical two-law bridge; callers must
# still pass it explicitly, making the resolution provenance visible at use.
CURRENT_LEGACY_REGISTRY: Mapping[str, str] = build_legacy_registry((
    ("5326", "5326_kabahatler_kanunu"),
    ("4458", "4458_gumruk_kanunu"),
))


def to_document_source_key(legacy_key: LegacySourceKey, registry: Mapping[str, str]) -> DocumentSourceKey:
    """Convert through an explicitly supplied registry; never inspect external data.

    Validate even caller-supplied mappings; non-scalar/invalid targets fail closed.
    Conflicting duplicate input records must be caught by build_legacy_registry
    before constructing a mapping. There is deliberately no reverse adapter.
    """
    if not isinstance(registry, Mapping):
        raise SourceIdentityError("legacy registry must be an explicit mapping")
    checked = build_legacy_registry(registry.items())
    try:
        number = legacy_key.legislation_number
        article_type = legacy_key.article_type
        article_no = legacy_key.article_no
    except AttributeError as exc:
        raise SourceIdentityError("legacy key requires legislation_number, article_type and article_no") from exc
    if not isinstance(number, str) or not number.strip():
        raise SourceIdentityError("legacy legislation_number must be a nonempty string")
    if number not in checked:
        raise SourceIdentityError(f"unresolved legacy legislation_number: {number!r}")
    return DocumentSourceKey(checked[number], article_type, article_no)
