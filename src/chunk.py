"""
Legal article parsing for ingested legal .docx sources.

Scope (Milestone M3A): convert the ordered paragraphs produced by
src/ingest.py (data/processed/*.paragraphs.json) into Article structures
per docs/data-model.md — detecting "Madde N-", lettered "Madde N/A-", "Ek
Madde N-", and "Geçici Madde N-" headings, and Kısım/Bölüm section context.
This module does NOT build Chunks, does NOT call embeddings/Chroma/an LLM,
and does NOT alter legal wording.

Chunking (M3B) is intentionally kept as a clearly separate function group
below the parser (see `build_chunks`, not yet implemented) so the parser can
be lifted into its own module later without disturbing chunking, and vice
versa.

Footnote references: `Article.footnote_references` is derived from the
`footnote_reference_ids` that src/ingest.py already attaches to each
ExtractedParagraph (read from the paragraph's own OOXML — see
src/ingest.py's docstring and docs/source-analysis-5326.md §4). This module
only aggregates those paragraph-level IDs onto the Article that consumes
each paragraph; it does not open or parse the .docx itself, and does not
resolve footnote *text* or build the amendment-history model — only
traceable reference IDs are preserved (see `_extract_amendment_note` for the
separate, unrelated "(Değişik: ...)"-style annotations).

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

from src import ingest
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


def parse_document(paragraphs_json_path: Path) -> dict[str, Any]:
    """Parse a *.paragraphs.json file into a JSON-serializable articles result:
    document_id, article_count, articles. Looks up legislation_number from
    data/source_manifest.json (via the paragraphs JSON's `source_file`) —
    reuses src.ingest's existing manifest lookup rather than duplicating it
    or hard-coding legal metadata here.
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
# Chunking (M3B) — intentionally not implemented yet
# ============================================================================


def build_chunks(articles: list[Article]) -> list[dict[str, Any]]:
    """Build Chunk records from parsed Articles (see docs/data-model.md).

    Out of scope for M3A. Kept as a clearly separate function group from
    parse_articles() above so the parser and chunker can evolve (and be
    split into separate modules) independently.
    """
    raise NotImplementedError("Chunking is implemented in Milestone M3B, not M3A.")


# ============================================================================
# CLI
# ============================================================================


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Parse legal articles from an ingested paragraphs JSON."
    )
    parser.add_argument(
        "paragraphs_json", type=Path, help="Path to a *.paragraphs.json produced by src.ingest"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output JSON path (default: data/processed/<stem>.articles.json)",
    )
    args = parser.parse_args(argv)

    result = parse_document(args.paragraphs_json)
    output_path = args.output or default_articles_output_path(args.paragraphs_json)
    write_articles_json(result, output_path)

    breakdown = Counter(a["article_type"] for a in result["articles"])
    print(f"Input file: {args.paragraphs_json}")
    print(f"Detected articles: {result['article_count']}")
    print(
        f"  normal: {breakdown.get('normal', 0)}, "
        f"ek: {breakdown.get('ek', 0)}, "
        f"gecici: {breakdown.get('gecici', 0)}"
    )
    print(f"Output path: {output_path}")


if __name__ == "__main__":
    main()
