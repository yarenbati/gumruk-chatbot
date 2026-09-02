"""
Legal article parsing for ingested legal .docx sources.

Scope (Milestone M3A): convert the ordered paragraphs produced by
src/ingest.py (data/processed/*.paragraphs.json) into Article structures
per docs/data-model.md — detecting "Madde N-", lettered "Madde N/A-", "Ek
Madde N-", and "Geçici Madde N-" headings, and Kısım/Bölüm section context.
This module does NOT build Chunks, does NOT call embeddings/Chroma/an LLM,
and does NOT alter legal wording.

Chunking (M3B) is kept as a clearly separate function group below the parser
(see `build_chunks`) so the parser and chunker can evolve (and be split into
separate modules later) independently.

Footnote references: `Article.footnote_references` is derived from the
`footnote_reference_ids` that src/ingest.py already attaches to each
ExtractedParagraph (read from the paragraph's own OOXML — see
src/ingest.py's docstring and docs/source-analysis-5326.md §4). This module
only aggregates those paragraph-level IDs onto the Article that consumes
each paragraph; it does not open or parse the .docx itself, and does not
resolve footnote *text* or build the amendment-history model — only
traceable reference IDs are preserved (see `_extract_amendment_note` for the
separate, unrelated "(Değişik: ...)"-style annotations).

Chunking strategy (M3B, see docs/data-model.md Chunk and
docs/source-analysis-5326.md §10): legal-structure-aware, not fixed-size.
A short/normal Article is one Chunk. A long Article is split only at
numbered fıkra ("(1)", "(2)"...) boundaries, grouping whole fıkra units
below a soft `max_chars` target (src.config.MAX_CHUNK_CHARS); a fıkra (with
any lettered a)/b)/c) sub-items it contains) is never split, even if that
leaves one oversized Chunk. Chunk-level `source_paragraph_start`/`_end` and
`footnote_references` are inherited verbatim from the parent Article on
every resulting Chunk (documented as Article-level provenance) — the
Article representation this module consumes has no finer-grained
paragraph-to-fıkra mapping to derive exact per-Chunk values from, and this
module does not redesign Article/ingestion to obtain one.

CLI usage:
    python -m src.chunk data/processed/5326-kabahatler-kanunu.paragraphs.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from src import config, ingest
from src.ingest import ExtractedParagraph

if __name__ == "__main__":  # pragma: no cover - exercised via CLI, not tests
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


@dataclass(frozen=True)
class Article:
    """One legal article, per docs/data-model.md."""

    article_id: str
    document_id: str | None
    legislation_number: str | None
    article_no: str
    article_type: str  # "normal" | "ek" | "gecici"
    article_title: str | None
    section_context: str | None
    text: str
    source_paragraph_start: int
    source_paragraph_end: int
    amendment_note: str | None = None
    footnote_references: list[int] | None = None


# ============================================================================
# Recognition patterns
# ============================================================================

# Tolerant of hyphen variants: ASCII hyphen, en dash, em dash.
_HYPHEN = "[-–—]"

NORMAL_ARTICLE_RE = re.compile(rf"^Madde\s+(\d+(?:/[A-Z])?)\s*{_HYPHEN}\s*(.*)$")
EK_MADDE_RE = re.compile(rf"^Ek\s+Madde\s+(\d+)\s*{_HYPHEN}\s*(.*)$")
GECICI_MADDE_RE = re.compile(rf"^Geçici\s+Madde\s+(\d+)\s*{_HYPHEN}\s*(.*)$")

NUMBERED_PARAGRAPH_RE = re.compile(r"^\(\d+\)\s")
LETTERED_SUBITEM_RE = re.compile(r"^[a-zçğıöşü]\)\s")

_ORDINALS = (
    "BİRİNCİ",
    "İKİNCİ",
    "ÜÇÜNCÜ",
    "DÖRDÜNCÜ",
    "BEŞİNCİ",
    "ALTINCI",
    "YEDİNCİ",
    "SEKİZİNCİ",
    "DOKUZUNCU",
    "ONUNCU",
)
SECTION_HEADING_RE = re.compile(rf"^({'|'.join(_ORDINALS)})\s+(KISIM|BÖLÜM)$")

# Turkish title-casing for a small closed vocabulary of ordinal/unit words —
# not a general-purpose casing routine, and not applied to legal text.
_ORDINAL_TITLE_CASE = {
    "BİRİNCİ": "Birinci",
    "İKİNCİ": "İkinci",
    "ÜÇÜNCÜ": "Üçüncü",
    "DÖRDÜNCÜ": "Dördüncü",
    "BEŞİNCİ": "Beşinci",
    "ALTINCI": "Altıncı",
    "YEDİNCİ": "Yedinci",
    "SEKİZİNCİ": "Sekizinci",
    "DOKUZUNCU": "Dokuzuncu",
    "ONUNCU": "Onuncu",
}
_UNIT_TITLE_CASE = {"KISIM": "Kısım", "BÖLÜM": "Bölüm"}

# Marks the start of the end-of-document amendment-history section (a
# preamble line followed by a real Word table that src/ingest.py never sees,
# since it only reads Document.paragraphs — see docs/source-analysis-5326.md
# §5). Everything from this marker onward is excluded from the Article
# corpus for V1.
AMENDMENT_HISTORY_MARKER_RE = re.compile(r"^\d+\s+SAYILI\s+KANUNA\s+EK\s+VE\s+DEĞİŞİKLİK", re.IGNORECASE)

_MAX_TITLE_LENGTH = 80


def _match_article_heading(text: str) -> tuple[str, str, str] | None:
    """Return (article_type, article_no, rest_text) if `text` is an article
    heading line, else None. Checks Ek/Geçici before the generic "Madde"
    pattern (though the anchors make them mutually exclusive already)."""
    m = EK_MADDE_RE.match(text)
    if m:
        return "ek", m.group(1), m.group(2)
    m = GECICI_MADDE_RE.match(text)
    if m:
        return "gecici", m.group(1), m.group(2)
    m = NORMAL_ARTICLE_RE.match(text)
    if m:
        return "normal", m.group(1), m.group(2)
    return None


def _match_section_heading(text: str) -> tuple[str, str] | None:
    """Return (ordinal, unit) if `text` is exactly a Kısım/Bölüm heading."""
    m = SECTION_HEADING_RE.fullmatch(text.strip())
    if m:
        return m.group(1), m.group(2)
    return None


def _looks_like_title(candidate: str) -> bool:
    """Heuristic for "is this paragraph a genuine article-title line".

    Real article titles in this corpus (e.g. "Tanım", "Sorumluluk",
    "Yürürlük") are short heading-like phrases that never end with a
    sentence-ending punctuation mark and are not themselves an article
    heading, a section heading, a numbered fıkra, a lettered sub-item, or
    the amendment-history marker. When any of these signals apply, this
    returns False so the caller falls back to `article_title = None`
    ("use null rather than guessing").
    """
    if not candidate:
        return False
    if len(candidate) > _MAX_TITLE_LENGTH:
        return False
    if candidate.rstrip().endswith((".", ":", ";")):
        return False
    if _match_article_heading(candidate) is not None:
        return False
    if _match_section_heading(candidate) is not None:
        return False
    if NUMBERED_PARAGRAPH_RE.match(candidate):
        return False
    if LETTERED_SUBITEM_RE.match(candidate):
        return False
    if AMENDMENT_HISTORY_MARKER_RE.match(candidate):
        return False
    return True


def _extract_amendment_note(rest_text: str) -> str | None:
    """Extract a leading parenthetical amendment annotation from the text
    following an article heading's "Madde N-" prefix, e.g. "(Değişik:
    6/12/2006-5560/31 md.)". A single leading group that is purely a bare
    number, e.g. "(1)", is a fıkra number, not an amendment note, and is
    left alone (returns None) — it stays in Article.text either way, this
    only controls what is *additionally* copied into amendment_note.
    """
    remaining = rest_text
    groups: list[str] = []
    while True:
        m = re.match(r"^\(([^)]*)\)\s*", remaining)
        if not m:
            break
        groups.append(m.group(0).strip())
        remaining = remaining[m.end():]
    if not groups:
        return None
    if len(groups) == 1 and re.fullmatch(r"\(\d+\)", groups[0]):
        return None
    return " ".join(groups)


def _combine_section_context(kisim: str | None, bolum: str | None) -> str | None:
    parts = [p for p in (kisim, bolum) if p]
    return " > ".join(parts) if parts else None


def _canonical_article_id(
    legislation_number: str | None, article_type: str, article_no: str
) -> str:
    """Deterministic, collision-free ID: no "/" characters, distinct
    namespaces per article_type so e.g. Madde 1 / Ek Madde 1 / Geçici Madde 1
    never collide. Examples: 5326-madde-1, 5326-madde-42-a, 5326-ek-madde-1,
    5326-gecici-madde-1."""
    prefix = legislation_number or "unknown"
    normalized_no = article_no.lower().replace("/", "-")
    if article_type == "ek":
        return f"{prefix}-ek-madde-{normalized_no}"
    if article_type == "gecici":
        return f"{prefix}-gecici-madde-{normalized_no}"
    return f"{prefix}-madde-{normalized_no}"


# ============================================================================
# Parsing (M3A)
# ============================================================================


def parse_articles(
    paragraphs: list[ExtractedParagraph],
    *,
    document_id: str | None,
    legislation_number: str | None,
) -> list[Article]:
    """Convert an ordered list of ExtractedParagraph into Article structures.

    Deterministic: the same paragraph list always produces the same Article
    list, in source order. Does not renumber articles, does not rewrite
    legal wording, and stops at the end-of-document amendment-history
    marker rather than parsing the table that follows it (see module
    docstring and docs/source-analysis-5326.md §5).
    """
    articles: list[Article] = []

    current_kisim: str | None = None
    current_bolum: str | None = None
    prev_paragraph: ExtractedParagraph | None = None

    open_article: dict[str, Any] | None = None
    paragraph_count = len(paragraphs)

    def close_open_article() -> None:
        nonlocal open_article
        if open_article is None:
            return
        text = "\n".join(open_article["body_texts"])
        footnote_refs = sorted(set(open_article["footnote_ids"])) or None
        articles.append(
            Article(
                article_id=_canonical_article_id(
                    legislation_number, open_article["article_type"], open_article["article_no"]
                ),
                document_id=document_id,
                legislation_number=legislation_number,
                article_no=open_article["article_no"],
                article_type=open_article["article_type"],
                article_title=open_article["title"],
                section_context=open_article["section_context"],
                text=text,
                source_paragraph_start=open_article["start"],
                source_paragraph_end=open_article["end"],
                amendment_note=open_article["amendment_note"],
                footnote_references=footnote_refs,
            )
        )
        open_article = None

    for i, para in enumerate(paragraphs):
        text = para.text

        if AMENDMENT_HISTORY_MARKER_RE.match(text):
            close_open_article()
            break

        section = _match_section_heading(text)
        if section is not None:
            close_open_article()
            ordinal, unit = section
            formatted = f"{_ORDINAL_TITLE_CASE[ordinal]} {_UNIT_TITLE_CASE[unit]}"
            if unit == "KISIM":
                current_kisim = formatted
                current_bolum = None
            else:
                current_bolum = formatted
            prev_paragraph = para
            continue

        heading = _match_article_heading(text)
        if heading is not None:
            close_open_article()
            article_type, article_no, rest_text = heading

            title: str | None = None
            title_footnote_ids: list[int] = []
            if prev_paragraph is not None and _looks_like_title(prev_paragraph.text):
                title = prev_paragraph.text
                title_footnote_ids = list(prev_paragraph.footnote_reference_ids or [])

            open_article = {
                "article_no": article_no,
                "article_type": article_type,
                "amendment_note": _extract_amendment_note(rest_text),
                "title": title,
                "section_context": _combine_section_context(current_kisim, current_bolum),
                "start": para.index,
                "end": para.index,
                "body_texts": [text],
                # The heading paragraph's own refs, plus any refs carried by
                # its accepted title paragraph (titles are excluded from
                # Article.text but a footnote attached to one still
                # traceably belongs to the article it titles).
                "footnote_ids": list(para.footnote_reference_ids or []) + title_footnote_ids,
            }
            prev_paragraph = para
            continue

        # A free (non-heading) paragraph immediately followed by an article
        # heading is that article's title candidate (see _looks_like_title)
        # and must NOT also be swallowed as trailing body text of whatever
        # article is currently open — titles precede their own "Madde N-"
        # line, they are never part of the previous article's body.
        next_para = paragraphs[i + 1] if i + 1 < paragraph_count else None
        reserved_as_next_title = (
            next_para is not None
            and _match_article_heading(next_para.text) is not None
            and _looks_like_title(text)
        )

        if open_article is not None and not reserved_as_next_title:
            open_article["body_texts"].append(text)
            open_article["end"] = para.index
            open_article["footnote_ids"].extend(para.footnote_reference_ids or [])

        prev_paragraph = para

    close_open_article()
    return articles


def load_paragraphs_json(path: Path) -> dict[str, Any]:
    """Load a data/processed/*.paragraphs.json file produced by src.ingest."""
    return json.loads(path.read_text(encoding="utf-8"))


def paragraphs_from_json(data: dict[str, Any]) -> list[ExtractedParagraph]:
    return [
        ExtractedParagraph(
            index=p["index"],
            text=p["text"],
            style_name=p["style_name"],
            footnote_reference_ids=p.get("footnote_reference_ids"),
        )
        for p in data["paragraphs"]
    ]


def _load_and_parse_articles(paragraphs_json_path: Path) -> tuple[str | None, list[Article]]:
    """Shared load+parse step for both parse_document() and
    build_chunks_document(): read a *.paragraphs.json, look up
    legislation_number from data/source_manifest.json (via the paragraphs
    JSON's `source_file` — reuses src.ingest's existing manifest lookup
    rather than duplicating it or hard-coding legal metadata here), and
    return (document_id, articles).
    """
    data = load_paragraphs_json(paragraphs_json_path)
    paragraphs = paragraphs_from_json(data)
    document_id = data.get("document_id")
    source_file = data.get("source_file")

    legislation_number = None
    if source_file:
        metadata = ingest._load_source_metadata(PROJECT_ROOT / source_file)
        legislation_number = metadata.get("legislation_number")

    articles = parse_articles(
        paragraphs, document_id=document_id, legislation_number=legislation_number
    )
    return document_id, articles


def parse_document(paragraphs_json_path: Path) -> dict[str, Any]:
    """Parse a *.paragraphs.json file into a JSON-serializable articles result:
    document_id, article_count, articles.
    """
    document_id, articles = _load_and_parse_articles(paragraphs_json_path)
    return {
        "document_id": document_id,
        "article_count": len(articles),
        "articles": [asdict(a) for a in articles],
    }


def write_articles_json(result: dict[str, Any], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return output_path


def default_articles_output_path(paragraphs_json_path: Path) -> Path:
    """data/processed/<stem>.articles.json for a given *.paragraphs.json path."""
    name = paragraphs_json_path.name
    suffix = ".paragraphs.json"
    base = name[: -len(suffix)] if name.endswith(suffix) else paragraphs_json_path.stem
    return PROCESSED_DIR / f"{base}.articles.json"


# ============================================================================
# Chunking (M3B)
# ============================================================================


@dataclass(frozen=True)
class Chunk:
    """One retrieval chunk, per docs/data-model.md.

    `source_paragraph_start`/`_end` and `footnote_references` are always the
    parent Article's own values, copied onto every Chunk produced from that
    Article (see module docstring): for a single-Chunk Article these are
    exactly the Article's values; for a multi-Chunk Article they are
    Article-level provenance, not a guaranteed exact per-Chunk range/set.
    """

    chunk_id: str
    article_id: str
    document_id: str | None
    legislation_number: str | None
    article_no: str
    article_type: str
    article_title: str | None
    section_context: str | None
    text: str
    paragraph_numbers: list[str] | None
    source_paragraph_start: int
    source_paragraph_end: int
    footnote_references: list[int] | None = None
    metadata: dict[str, Any] | None = None


# A fıkra "unit" is (fıkra_number_or_None, unit_text): unit_text is one or
# more original paragraph lines ("\n"-joined, mirroring how Article.text
# itself was built) that must never be split apart — a fıkra together with
# any lettered a)/b)/c) sub-items and continuation lines that follow it,
# until the next numbered fıkra starts.
_FikraUnit = tuple[str | None, str]

_LEADING_PAREN_GROUP_RE = re.compile(r"^\(([^)]*)\)\s*")


def _detect_line0_embedded_fikra(line0: str) -> str | None:
    """Return the fıkra number if `line0` (the article's own heading
    paragraph) directly embeds its first numbered fıkra on the same line,
    e.g. "Madde 2- (1) Kabahat deyiminden..." -> "1". Leading amendment-note
    parenthetical groups are skipped first, e.g. "Madde 3- (Değişik: ...)
    (1) ..." -> "1"; a bare "(Değişik: ...)" note with no following "(N)" on
    the same line (the fıkra instead starts on its own next paragraph/line,
    the common case in the real 5326 source) returns None.
    """
    heading = _match_article_heading(line0)
    if heading is None:
        return None
    _, _, remaining = heading
    while True:
        m = _LEADING_PAREN_GROUP_RE.match(remaining)
        if not m:
            return None
        content = m.group(1)
        if re.fullmatch(r"\d+", content):
            return content
        remaining = remaining[m.end():]


def _split_article_text_into_fikra_units(text: str) -> list[_FikraUnit]:
    """Split an Article's text into ordered fıkra units (see `_FikraUnit`).

    Each line of `text` (one original source paragraph, see how
    parse_articles() builds Article.text) is assigned to exactly one unit,
    in order, so "\\n".join(unit_text for _, unit_text in units) always
    losslessly reconstructs `text` — no line is dropped or duplicated.

    Text before the first numbered fıkra (the heading line, any amendment
    note, and — rare in practice — further non-fıkra lines before the first
    "(N)" line) is merged into that first fıkra's unit rather than kept as
    its own standalone unit, so it always ends up in chunk-001 together with
    fıkra 1. If the Article has no numbered fıkra at all, the whole text is
    a single unit with a None fıkra number.
    """
    lines = text.split("\n")

    units: list[tuple[str | None, list[str]]] = []
    current_number = _detect_line0_embedded_fikra(lines[0])
    current_lines: list[str] = [lines[0]]

    for line in lines[1:]:
        m = NUMBERED_PARAGRAPH_RE.match(line)
        if m:
            units.append((current_number, current_lines))
            current_number = re.match(r"^\((\d+)\)", line).group(1)
            current_lines = [line]
        else:
            current_lines.append(line)
    units.append((current_number, current_lines))

    if len(units) > 1 and units[0][0] is None:
        preamble_lines = units[0][1]
        next_number, next_lines = units[1]
        units = [(next_number, preamble_lines + next_lines), *units[2:]]

    return [(number, "\n".join(unit_lines)) for number, unit_lines in units]


def _group_units_into_chunks(
    units: list[_FikraUnit], max_chars: int | None
) -> list[list[_FikraUnit]]:
    """Group ordered fıkra units into ordered Chunk-sized groups.

    `max_chars` is a soft target: units are only ever grouped whole, never
    split, so a single fıkra unit larger than `max_chars` still becomes its
    own (oversized) group rather than being cut. `max_chars=None` disables
    size-based splitting entirely (single group, i.e. one Chunk).
    """
    if max_chars is None or len(units) <= 1:
        return [list(units)]

    groups: list[list[_FikraUnit]] = []
    current: list[_FikraUnit] = []
    for unit in units:
        if current and len("\n".join(t for _, t in current + [unit])) > max_chars:
            groups.append(current)
            current = [unit]
        else:
            current.append(unit)
    if current:
        groups.append(current)
    return groups


def build_chunks(
    articles: list[Article], max_chars: int | None = config.MAX_CHUNK_CHARS
) -> list[Chunk]:
    """Build Chunk records from parsed Articles (see docs/data-model.md).

    Legal-structure-aware chunking: an Article whose text fits within the
    soft `max_chars` target (or when `max_chars` is None) becomes exactly
    one Chunk; a longer Article is split only at numbered-fıkra boundaries,
    grouping whole fıkra units near/below the target and never splitting a
    fıkra (including its lettered a)/b)/c) sub-items) even if that leaves
    one oversized Chunk. Source order is preserved throughout: Article
    order, fıkra order within an Article, and chunk-001/002/... numbering
    all follow source order.

    `max_chars` defaults to `src.config.MAX_CHUNK_CHARS` (env
    `MAX_CHUNK_CHARS`, default 4000) — a provisional soft default for
    legal-semantic chunking, not tuned to any embedding model's token limit
    (no tokenizer dependency is used here); revisit in M4.
    """
    chunks: list[Chunk] = []
    for article in articles:
        units = _split_article_text_into_fikra_units(article.text)
        groups = _group_units_into_chunks(units, max_chars)
        for position, group in enumerate(groups, start=1):
            paragraph_numbers = [number for number, _ in group if number is not None] or None
            chunks.append(
                Chunk(
                    chunk_id=f"{article.article_id}-chunk-{position:03d}",
                    article_id=article.article_id,
                    document_id=article.document_id,
                    legislation_number=article.legislation_number,
                    article_no=article.article_no,
                    article_type=article.article_type,
                    article_title=article.article_title,
                    section_context=article.section_context,
                    text="\n".join(unit_text for _, unit_text in group),
                    paragraph_numbers=paragraph_numbers,
                    source_paragraph_start=article.source_paragraph_start,
                    source_paragraph_end=article.source_paragraph_end,
                    footnote_references=article.footnote_references,
                )
            )
    return chunks


def build_chunks_document(
    paragraphs_json_path: Path, *, max_chars: int | None = config.MAX_CHUNK_CHARS
) -> dict[str, Any]:
    """Parse a *.paragraphs.json file straight through to a JSON-serializable
    chunks result: document_id, chunk_count, chunks. Reuses
    `_load_and_parse_articles` (the same load+parse step parse_document()
    uses) rather than duplicating ingestion/parsing logic.
    """
    document_id, articles = _load_and_parse_articles(paragraphs_json_path)
    chunks = build_chunks(articles, max_chars=max_chars)
    return {
        "document_id": document_id,
        "chunk_count": len(chunks),
        "chunks": [asdict(c) for c in chunks],
    }


def write_chunks_json(result: dict[str, Any], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return output_path


def default_chunks_output_path(paragraphs_json_path: Path) -> Path:
    """data/processed/<stem>.chunks.json for a given *.paragraphs.json path."""
    name = paragraphs_json_path.name
    suffix = ".paragraphs.json"
    base = name[: -len(suffix)] if name.endswith(suffix) else paragraphs_json_path.stem
    return PROCESSED_DIR / f"{base}.chunks.json"


# ============================================================================
# CLI
# ============================================================================


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Parse legal articles and build Chunks from an ingested paragraphs JSON."
    )
    parser.add_argument(
        "paragraphs_json", type=Path, help="Path to a *.paragraphs.json produced by src.ingest"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Articles output JSON path (default: data/processed/<stem>.articles.json)",
    )
    parser.add_argument(
        "--chunks-output",
        type=Path,
        default=None,
        help="Chunks output JSON path (default: data/processed/<stem>.chunks.json)",
    )
    parser.add_argument(
        "--max-chars",
        type=int,
        default=config.MAX_CHUNK_CHARS,
        help=(
            "Soft chunk-size target in characters, or a negative value to pass "
            "through as None (disables size-based splitting). "
            f"Default: src.config.MAX_CHUNK_CHARS ({config.MAX_CHUNK_CHARS})."
        ),
    )
    args = parser.parse_args(argv)
    max_chars = None if args.max_chars is not None and args.max_chars < 0 else args.max_chars

    document_id, articles = _load_and_parse_articles(args.paragraphs_json)
    articles_result = {
        "document_id": document_id,
        "article_count": len(articles),
        "articles": [asdict(a) for a in articles],
    }
    articles_output_path = args.output or default_articles_output_path(args.paragraphs_json)
    write_articles_json(articles_result, articles_output_path)

    chunks = build_chunks(articles, max_chars=max_chars)
    chunks_result = {
        "document_id": document_id,
        "chunk_count": len(chunks),
        "chunks": [asdict(c) for c in chunks],
    }
    chunks_output_path = args.chunks_output or default_chunks_output_path(args.paragraphs_json)
    write_chunks_json(chunks_result, chunks_output_path)

    breakdown = Counter(a.article_type for a in articles)
    multi_chunk_articles = sum(
        1 for article in articles if sum(1 for c in chunks if c.article_id == article.article_id) > 1
    )
    print(f"Input file: {args.paragraphs_json}")
    print(f"Detected articles: {len(articles)}")
    print(
        f"  normal: {breakdown.get('normal', 0)}, "
        f"ek: {breakdown.get('ek', 0)}, "
        f"gecici: {breakdown.get('gecici', 0)}"
    )
    print(f"Articles output path: {articles_output_path}")
    print(f"Built chunks: {len(chunks)} (max_chars={max_chars})")
    print(f"Articles that produced more than one chunk: {multi_chunk_articles}")
    print(f"Chunks output path: {chunks_output_path}")


if __name__ == "__main__":
    main()
