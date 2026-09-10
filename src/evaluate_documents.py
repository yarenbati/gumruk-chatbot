"""Pure document-source-v1 evaluation of supplied rankings; no retrieval or I/O.

Historical evaluators are unchanged. Cutoffs retain every chunk slot, including
repeated provisions. Summary rates are question-level arithmetic means, never a
composite score. Empty rankings have false coverage and undefined (None)
intrusion. Per-document groups include each question expecting that document;
multi-document questions therefore occur in more than one such group.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, asdict
from typing import Any, Protocol

from src import source_identity, source_registry

SOURCE_IDENTITY_SCHEMA = "document-source-v1"
CUTOFFS = (1, 3, 5)


class DocumentEvaluationError(ValueError):
    """Invalid question, rank, schema or canonical provenance; never a miss."""


def _nonempty(value: object, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise DocumentEvaluationError(f"{name} must be a nonempty string")


def _key(value: object) -> source_identity.DocumentSourceKey:
    if not isinstance(value, source_identity.DocumentSourceKey):
        raise DocumentEvaluationError("expected a DocumentSourceKey")
    return value


@dataclass(frozen=True)
class DocumentQuestion:
    """Immutable gold provision/document sets; duplicates collapse as sets."""

    id: str
    question: str
    expected_sources: frozenset[source_identity.DocumentSourceKey]
    expected_document_ids: frozenset[str]

    def __post_init__(self) -> None:
        """Validate direct construction and copy collections into frozen sets."""
        _nonempty(self.id, "id")
        _nonempty(self.question, "question")
        try:
            sources = frozenset(_key(k) for k in self.expected_sources)
            if isinstance(self.expected_document_ids, str):
                raise DocumentEvaluationError("expected_document_ids must be a collection")
            documents = frozenset(self.expected_document_ids)
        except TypeError as exc:
            raise DocumentEvaluationError("expected identities must be collections") from exc
        if not sources:
            raise DocumentEvaluationError("at least one expected source is required")
        if documents != frozenset(k.document_id for k in sources):
            raise DocumentEvaluationError("expected documents must exactly match expected sources")
        object.__setattr__(self, "expected_sources", sources)
        object.__setattr__(self, "expected_document_ids", documents)

    def to_dict(self) -> dict[str, Any]:
        """Return fresh JSON-safe fields, sorting identity sets deterministically."""
        return dict(id=self.id, question=self.question,
            expected_sources=[k.to_dict() for k in sorted(self.expected_sources)],
            expected_document_ids=sorted(self.expected_document_ids))


class RetrievedFields(Protocol):
    """Read-only shape needed from a trusted RetrievedChunk."""

    rank: int
    chunk_id: str
    metadata: Mapping[str, Any]


@dataclass(frozen=True)
class DocumentRank:
    """One unchanged retrieval slot with canonical identity and optional law metadata."""

    rank: int
    chunk_id: str
    document_source_key: source_identity.DocumentSourceKey
    document_id: str
    legislation_number: str | None = None

    def __post_init__(self) -> None:
        """Reject inconsistent direct rank construction."""
        if type(self.rank) is not int or self.rank < 1:
            raise DocumentEvaluationError("rank must be a positive integer")
        _nonempty(self.chunk_id, "chunk_id")
        key = _key(self.document_source_key)
        if self.document_id != key.document_id:
            raise DocumentEvaluationError("rank document_id contradicts canonical key")
        if self.legislation_number is not None:
            _nonempty(self.legislation_number, "legislation_number")

    @classmethod
    def from_retrieved(cls, chunk: RetrievedFields) -> DocumentRank:
        """Derive only from trusted metadata; missing identity never falls back."""
        try:
            key = source_registry.source_key_from_metadata(chunk.metadata)
            return cls(chunk.rank, chunk.chunk_id, key, key.document_id,
                       chunk.metadata.get("legislation_number"))
        except (AttributeError, source_identity.SourceIdentityError) as exc:
            raise DocumentEvaluationError(f"invalid retrieved canonical provenance: {exc}") from exc

    def to_dict(self) -> dict[str, Any]:
        """Serialize canonical identity as a string, never repr or Python hash."""
        return dict(rank=self.rank, chunk_id=self.chunk_id,
            document_source_key=str(self.document_source_key), document_id=self.document_id,
            legislation_number=self.legislation_number)


@dataclass(frozen=True)
class CutoffMetrics:
    """Coverage flags and actual-slot intrusion for one cutoff."""

    k: int
    source_any: bool
    source_all: bool
    document_hit: bool
    document_all: bool
    document_intrusion: float | None
    retrieved_slots: int


@dataclass(frozen=True)
class DocumentResult:
    """One question's immutable ranking and metrics in cutoff order."""

    question: DocumentQuestion
    ranks: tuple[DocumentRank, ...]
    metrics: tuple[CutoffMetrics, ...]

    def to_dict(self) -> dict[str, Any]:
        """Return deterministic JSON-safe result fields."""
        return dict(source_identity_schema=SOURCE_IDENTITY_SCHEMA,
            question=self.question.to_dict(), ranks=[r.to_dict() for r in self.ranks],
            metrics={str(m.k): asdict(m) for m in self.metrics})


def evaluate_question(question: DocumentQuestion, ranks: Sequence[DocumentRank]) -> DocumentResult:
    """Evaluate supplied slots at 1/3/5 without sorting or deduplicating ranks.

    All ranks, including those beyond five, must be canonical and sequential
    starting at one. Malformed inputs raise instead of changing denominators.
    """
    if not isinstance(question, DocumentQuestion):
        raise DocumentEvaluationError("expected DocumentQuestion")
    ranks = tuple(ranks)
    for position, rank in enumerate(ranks, 1):
        if not isinstance(rank, DocumentRank) or rank.rank != position:
            raise DocumentEvaluationError("ranks must be sequential in supplied order starting at one")
    metrics = []
    for k in CUTOFFS:
        top = ranks[:k]
        sources = {r.document_source_key for r in top}
        documents = {r.document_id for r in top}
        intrusion = sum(r.document_id not in question.expected_document_ids for r in top)
        metrics.append(CutoffMetrics(k, bool(question.expected_sources & sources),
            question.expected_sources <= sources, bool(question.expected_document_ids & documents),
            question.expected_document_ids <= documents, intrusion / len(top) if top else None, len(top)))
    return DocumentResult(question, ranks, tuple(metrics))


def evaluate_retrieved(question: DocumentQuestion, chunks: Sequence[RetrievedFields]) -> DocumentResult:
    """Validate every supplied chunk and evaluate without mutating it or retrieving."""
    return evaluate_question(question, tuple(DocumentRank.from_retrieved(c) for c in chunks))


def dataset_to_dict(questions: Iterable[DocumentQuestion]) -> dict[str, Any]:
    """Serialize the new explicitly tagged schema; reject duplicate question IDs."""
    questions = tuple(questions)
    if not questions or any(not isinstance(q, DocumentQuestion) for q in questions):
        raise DocumentEvaluationError("dataset requires document questions")
    if len({q.id for q in questions}) != len(questions):
        raise DocumentEvaluationError("duplicate question ID")
    return dict(source_identity_schema=SOURCE_IDENTITY_SCHEMA,
                questions=[q.to_dict() for q in sorted(questions, key=lambda q: q.id)])


def dataset_from_dict(payload: Mapping[str, Any]) -> tuple[DocumentQuestion, ...]:
    """Decode only document-source-v1 component objects; no filesystem I/O.

    Component article aliases follow DocumentSourceKey.from_dict normalization.
    Legacy strings and undeclared/unknown schemas are rejected.
    """
    if not isinstance(payload, Mapping) or set(payload) != {"source_identity_schema", "questions"}:
        raise DocumentEvaluationError("dataset requires schema and questions only")
    if payload["source_identity_schema"] != SOURCE_IDENTITY_SCHEMA:
        raise DocumentEvaluationError("unsupported or missing source identity schema")
    if not isinstance(payload["questions"], list):
        raise DocumentEvaluationError("questions must be a JSON array")
    questions = []
    for raw in payload["questions"]:
        if not isinstance(raw, Mapping) or set(raw) != {"id", "question", "expected_sources", "expected_document_ids"}:
            raise DocumentEvaluationError("invalid document question fields")
        if not isinstance(raw["expected_sources"], list) or not isinstance(raw["expected_document_ids"], list):
            raise DocumentEvaluationError("expected identities must be JSON arrays")
        try:
            sources = [source_identity.DocumentSourceKey.from_dict(k) for k in raw["expected_sources"]]
            questions.append(DocumentQuestion(raw["id"], raw["question"], sources, raw["expected_document_ids"]))
        except source_identity.SourceIdentityError as exc:
            raise DocumentEvaluationError(str(exc)) from exc
    dataset_to_dict(questions)
    return tuple(sorted(questions, key=lambda q: q.id))


class LegacyQuestion(Protocol):
    """Historical qualified question shape, without importing its evaluator."""

    id: str
    question: str
    expected_sources: Iterable[source_identity.LegacySourceKey]


def adapt_legacy_question(question: LegacyQuestion) -> DocumentQuestion:
    """Explicitly adapt only the reviewed 5326/4458 registry; never mutate input."""
    try:
        keys = frozenset(source_identity.to_document_source_key(k, source_identity.CURRENT_LEGACY_REGISTRY)
                         for k in question.expected_sources)
        return DocumentQuestion(question.id, question.question, keys, frozenset(k.document_id for k in keys))
    except (AttributeError, TypeError, source_identity.SourceIdentityError) as exc:
        raise DocumentEvaluationError(f"legacy adaptation failed: {exc}") from exc


def summarize(results: Iterable[DocumentResult]) -> dict[str, Any]:
    """Aggregate question means by gold document and source/document cardinality.

    Empty groups have count zero and None rates. Intrusion averages only defined
    per-question proportions, reporting defined/undefined denominator counts.
    Per-document groups retain each question's full multi-document gold set.
    """
    results = tuple(sorted(results, key=lambda r: r.question.id))
    if len({r.question.id for r in results}) != len(results):
        raise DocumentEvaluationError("duplicate result question ID")

    def group(items: Sequence[DocumentResult]) -> dict[str, Any]:
        metrics = {}
        for index, k in enumerate(CUTOFFS):
            values = [r.metrics[index] for r in items]
            rates = {name: sum(getattr(m, name) for m in values) / len(values) if values else None
                     for name in ("source_any", "source_all", "document_hit", "document_all")}
            defined = [m.document_intrusion for m in values if m.document_intrusion is not None]
            rates.update(document_intrusion=sum(defined) / len(defined) if defined else None,
                         intrusion_defined_questions=len(defined), intrusion_undefined_questions=len(values)-len(defined))
            metrics[str(k)] = rates
        return dict(count=len(items), question_ids=[r.question.id for r in items], metrics=metrics)

    documents = sorted({d for r in results for d in r.question.expected_document_ids})
    return dict(source_identity_schema=SOURCE_IDENTITY_SCHEMA, overall=group(results),
        per_document={d: group([r for r in results if d in r.question.expected_document_ids]) for d in documents},
        single_source=group([r for r in results if len(r.question.expected_sources) == 1]),
        multi_source=group([r for r in results if len(r.question.expected_sources) > 1]),
        single_document=group([r for r in results if len(r.question.expected_document_ids) == 1]),
        multi_document=group([r for r in results if len(r.question.expected_document_ids) > 1]))
