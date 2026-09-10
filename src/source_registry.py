"""Explicit manifest admission and observational canonical provenance views.

No I/O occurs on import. Loading is explicit; lookups never discover documents
through titles, gold datasets or a first-match legislation-number fallback.
Strict admission belongs here, not in the generic index metadata builder:
index.build_chroma_metadata already preserves existing provenance and omits an
absent legislation_number. This module neither opens storage nor renames IDs.
"""

from __future__ import annotations

import json
import os
import re
from collections.abc import Mapping
from dataclasses import dataclass, field, fields
from pathlib import Path
from types import MappingProxyType
from typing import Protocol

from src import source_identity


class SourceRegistryError(ValueError):
    """Malformed manifest, ambiguous lookup or inconsistent admission metadata."""


def _nonempty_string(value: object, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise SourceRegistryError(f"{name} must be a nonempty string")


@dataclass(frozen=True)
class DocumentRecord:
    """Immutable document metadata using only fields in the current manifest.

    Legislation number and descriptive provenance are optional for generic
    records; any supplied value must be a nonempty string. Source-file presence
    is not checked: validation does not open a legal document or fetch a URL.
    """

    document_id: str
    title: str
    document_type: str
    local_file: str
    legislation_number: str | None = None
    issuing_authority: str | None = None
    official_source_url: str | None = None
    retrieved_at: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        """Validate direct construction without normalizing document identities."""
        # The frozen core exposes no document-only validator; keep its exact
        # documented grammar here rather than changing/importing private core APIs.
        if not isinstance(self.document_id, str) or not re.fullmatch(
            r"[a-z0-9]+(?:[_-][a-z0-9]+)*", self.document_id
        ):
            raise SourceRegistryError("document_id is not canonical")
        for name in ("title", "document_type", "local_file"):
            _nonempty_string(getattr(self, name), name)
        if self.local_file != self.local_file.strip() or any(ord(c) < 32 for c in self.local_file):
            raise SourceRegistryError("local_file must not contain edge whitespace or control characters")
        for name in ("legislation_number", "issuing_authority", "official_source_url", "retrieved_at", "notes"):
            value = getattr(self, name)
            if value is not None:
                _nonempty_string(value, name)

    @classmethod
    def from_dict(cls, value: Mapping[str, object]) -> DocumentRecord:
        """Reject unknown/missing fields; preserve current manifest values exactly."""
        required = {"document_id", "title", "document_type", "local_file"}
        allowed = {f.name for f in fields(cls)}
        if not isinstance(value, Mapping) or not required <= value.keys() or not value.keys() <= allowed:
            raise SourceRegistryError("manifest entry has missing or unknown fields")
        return cls(**value)


@dataclass(frozen=True)
class SourceRegistry:
    """Validated immutable manifest snapshot with explicit project-relative paths.

    Every non-null legislation number must resolve uniquely in this snapshot.
    This restriction protects the legacy bridge; number is not canonical identity.
    Multiple numberless records are permitted. Path aliases resolve against the
    supplied root and follow host filesystem case semantics, never the working dir.
    """

    documents: tuple[DocumentRecord, ...]
    project_root: Path
    _documents: Mapping[str, DocumentRecord] = field(init=False, repr=False, compare=False)
    _files: Mapping[str, DocumentRecord] = field(init=False, repr=False, compare=False)
    _numbers: Mapping[str, DocumentRecord] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        """Copy records and reject duplicate identities, paths and legacy mappings."""
        object.__setattr__(self, "documents", tuple(self.documents))
        object.__setattr__(self, "project_root", Path(self.project_root).resolve())
        by_id: dict[str, DocumentRecord] = {}
        by_file: dict[str, DocumentRecord] = {}
        by_number: dict[str, DocumentRecord] = {}
        for record in self.documents:
            if not isinstance(record, DocumentRecord):
                raise SourceRegistryError("registry entries must be DocumentRecord values")
            if record.document_id in by_id:
                raise SourceRegistryError(f"duplicate document_id: {record.document_id!r}")
            file_key = self._file_key(record.local_file)
            if file_key in by_file:
                raise SourceRegistryError(f"duplicate local_file mapping: {record.local_file!r}")
            if record.legislation_number is not None:
                if record.legislation_number in by_number:
                    raise SourceRegistryError(f"ambiguous legislation_number: {record.legislation_number!r}")
                by_number[record.legislation_number] = record
            by_id[record.document_id] = record
            by_file[file_key] = record
        object.__setattr__(self, "_documents", MappingProxyType(by_id))
        object.__setattr__(self, "_files", MappingProxyType(by_file))
        object.__setattr__(self, "_numbers", MappingProxyType(by_number))

    def _file_key(self, value: str | Path) -> str:
        if not isinstance(value, (str, Path)):
            raise SourceRegistryError("local file lookup requires a path")
        _nonempty_string(str(value), "local_file")
        return os.path.normcase(str((self.project_root / value).resolve()))

    def by_document_id(self, document_id: str) -> DocumentRecord:
        """Return exactly the registered document; unknown IDs fail explicitly."""
        _nonempty_string(document_id, "document_id")
        try:
            return self._documents[document_id]
        except KeyError as exc:
            raise SourceRegistryError(f"unregistered document_id: {document_id!r}") from exc

    def by_local_file(self, local_file: str | Path) -> DocumentRecord:
        """Resolve a source-file path uniquely without reading its contents."""
        key = self._file_key(local_file)
        try:
            return self._files[key]
        except KeyError as exc:
            raise SourceRegistryError(f"unregistered local_file: {str(local_file)!r}") from exc

    def unique_by_legislation_number(self, legislation_number: str) -> DocumentRecord:
        """Legacy-only exact lookup; ambiguity is rejected when building the registry."""
        _nonempty_string(legislation_number, "legislation_number")
        try:
            return self._numbers[legislation_number]
        except KeyError as exc:
            raise SourceRegistryError(f"unregistered legislation_number: {legislation_number!r}") from exc

    def admit_paragraph_root(self, root: Mapping[str, object]) -> DocumentRecord:
        """Resolve once by source_file and require an exactly matching persisted ID.

        Missing IDs or unknown paths fail closed; never combine root identity
        with independently looked-up law metadata or overwrite a mismatched ID.
        """
        if not isinstance(root, Mapping):
            raise SourceRegistryError("paragraph root must be an object")
        source_file = root.get("source_file")
        document_id = root.get("document_id")
        _nonempty_string(source_file, "paragraph source_file")
        _nonempty_string(document_id, "paragraph document_id")
        record = self.by_local_file(source_file)
        if document_id != record.document_id:
            raise SourceRegistryError("paragraph document_id does not match the source_file manifest record")
        return record


def _unique_json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise SourceRegistryError(f"duplicate manifest object field: {key!r}")
        result[key] = value
    return result


def load_manifest(path: str | Path, *, project_root: str | Path) -> SourceRegistry:
    """Explicitly read and validate one manifest; no implicit default file or cache."""
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=_unique_json_object)
    except SourceRegistryError:
        raise
    except (OSError, ValueError) as exc:
        raise SourceRegistryError(f"could not load manifest: {path}") from exc
    if not isinstance(payload, list):
        raise SourceRegistryError("manifest must be a list of document objects")
    return SourceRegistry(tuple(DocumentRecord.from_dict(value) for value in payload), Path(project_root))


class ProvisionFields(Protocol):
    """Read-only Article/Chunk-shaped canonical provenance fields."""

    @property
    def document_id(self) -> str | None:
        """Return the supplied document ID, never a legacy fallback."""
        ...

    @property
    def article_type(self) -> str:
        """Return the supplied structural namespace."""
        ...

    @property
    def article_no(self) -> str:
        """Return the source article number without mutating it."""
        ...


class RetrievedProvenance(Protocol):
    """RetrievedChunk-shaped metadata carrier, independent of ranking code."""

    @property
    def metadata(self) -> Mapping[str, object]:
        """Return trusted retrieved metadata."""
        ...


def source_key_from_metadata(metadata: Mapping[str, object]) -> source_identity.DocumentSourceKey:
    """Validate an observational canonical view; never mutate or use law fallback."""
    if not isinstance(metadata, Mapping):
        raise source_identity.SourceIdentityError("canonical provenance requires metadata")
    return source_identity.DocumentSourceKey(metadata.get("document_id"), metadata.get("article_type"), metadata.get("article_no"))


def provision_source_key(provision: ProvisionFields) -> source_identity.DocumentSourceKey:
    """Derive a key from trusted Article/Chunk fields, leaving storage IDs intact."""
    try:
        return source_identity.DocumentSourceKey(provision.document_id, provision.article_type, provision.article_no)
    except AttributeError as exc:
        raise source_identity.SourceIdentityError("provision lacks canonical provenance fields") from exc


def retrieved_source_key(chunk: RetrievedProvenance) -> source_identity.DocumentSourceKey:
    """Opt-in RetrievedChunk provenance view with no retrieval/ranking dependency.

    Existing callers can keep using metadata without requesting this strict view.
    A key validates supplied components; it does not independently certify that
    a record passed manifest admission or establish legal relevance.
    """
    try:
        metadata = chunk.metadata
    except AttributeError as exc:
        raise source_identity.SourceIdentityError("retrieved object lacks metadata") from exc
    return source_key_from_metadata(metadata)
