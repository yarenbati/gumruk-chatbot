"""Tests for src/chunk.py (M3A legal article parsing, parser only).

All core tests are self-contained: paragraph fixtures are built
programmatically as ExtractedParagraph instances (matching the
data/processed/*.paragraphs.json contract produced by src/ingest.py), with
deliberately non-contiguous `index` values to prove source_paragraph_start/
end use real ingestion indices, not parser-invented sequential ones. None of
this requires data/raw/.

A separate, clearly-named integration test at the bottom exercises the real
5326 Kabahatler Kanunu source end-to-end (ingest -> parse) and SKIPs when
that file isn't present locally.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src import chunk, ingest
from src.chunk import parse_articles
from src.ingest import ExtractedParagraph

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REAL_SOURCE_PATH = PROJECT_ROOT / "data" / "raw" / "5326-kabahatler-kanunu.docx"


def _p(
    index: int, text: str, footnote_reference_ids: list[int] | None = None
) -> ExtractedParagraph:
    return ExtractedParagraph(
        index=index, text=text, style_name="Normal", footnote_reference_ids=footnote_reference_ids
    )


# A single rich fixture exercising: Kısım/Bölüm context (with a KISIM reset),
# a normal single-fıkra article, a multi-paragraph article with a lettered
# sub-item, a lettered article id (42/A) with a hyphen variant (en dash), a
# hyphen variant (em dash) on another normal article, an amendment_note
# annotation + a paragraph-level footnote_reference_ids marker (mirroring
# how src/ingest.py attaches real Word footnote-reference IDs — never as
# literal "[N]" text, see src/ingest.py's docstring), Ek Madde, two Geçici
# Madde (both with no title, adjacent to numbered-fıkra/heading
# predecessors), a titled trailing article (Yürürlük), and an
# amendment-history marker followed by decoy content that must NOT be
# parsed as an article.
MAIN_FIXTURE: list[ExtractedParagraph] = [
    _p(0, "KABAHATLER KANUNU"),
    _p(2, "BİRİNCİ KISIM"),
    _p(3, "Genel Hükümler"),
    _p(5, "BİRİNCİ BÖLÜM"),
    _p(6, "Amaç ve Kapsam, Tanım ve Uygulama Alanı Hakkında Ayrıntılı Açıklama"),
    _p(7, "Amaç ve kapsam"),
    _p(8, "Madde 1- (1) Bu Kanunda test hükmü birinci fıkra."),
    _p(9, "a) test alt bent birinci"),
    _p(10, "b) test alt bent ikinci"),
    _p(12, "(2) ikinci fıkra metni."),
    _p(14, "Tanım"),
    _p(15, "Madde 2– (1) İkinci madde test hükmü ile ilgili fıkra."),
    _p(17, "İKİNCİ BÖLÜM"),
    _p(18, "Ceza sorumluluğu istisnası"),
    _p(19, "Madde 42/A— (1) Lettered madde test hükmü."),
    _p(21, "Madde 3- (Değişik: 6/12/2006-5560/31 md.)"),
    _p(22, "(1) Değişiklik sonrası hüküm metni referans.", footnote_reference_ids=[1]),
    _p(24, "İKİNCİ KISIM"),
    _p(26, "Ek Madde 1- (Ek: 11/5/2005-5348/5 md.)"),
    _p(27, "(1) Ek madde hükmü metni."),
    _p(29, "Geçici Madde 1- (1) Geçici hüküm birinci."),
    _p(31, "Geçici Madde 2- (1) Geçici hüküm ikinci."),
    _p(33, "Yürürlük"),
    _p(34, "Madde 44- (1) Bu Kanun test tarihinde yürürlüğe girer."),
    _p(36, "5326 SAYILI KANUNA EK VE DEĞİŞİKLİK GETİREN MEVZUATIN VEYA"),
    _p(38, "ANAYASA MAHKEMESİ TARAFINDAN İPTAL EDİLEN HÜKÜMLERİN"),
    _p(40, "Madde 99- (1) Bu asla bir madde olarak görünmemeli."),
]


def _parse_main() -> list[chunk.Article]:
    return parse_articles(MAIN_FIXTURE, document_id="doc_test", legislation_number="5326")


def _by_no(articles: list[chunk.Article], article_type: str, article_no: str) -> chunk.Article:
    for a in articles:
        if a.article_type == article_type and a.article_no == article_no:
            return a
    raise AssertionError(f"article not found: {article_type} {article_no}")


# --- Core detection -----------------------------------------------------


def test_normal_madde_detection() -> None:
    paragraphs = [_p(0, "Madde 1- (1) Basit bir hüküm.")]
    articles = parse_articles(paragraphs, document_id="d", legislation_number="5326")
    assert len(articles) == 1
    assert articles[0].article_no == "1"
    assert articles[0].article_type == "normal"
    assert "Madde 1-" in articles[0].text
    assert "Basit bir hüküm." in articles[0].text


def test_multiple_articles_detected() -> None:
    articles = _parse_main()
    assert len(articles) == 8


def test_lettered_article_identifier() -> None:
    articles = _parse_main()
    a = _by_no(articles, "normal", "42/A")
    assert a.article_type == "normal"
    assert a.article_id == "5326-madde-42-a"


def test_ek_madde_detected() -> None:
    articles = _parse_main()
    a = _by_no(articles, "ek", "1")
    assert a.article_type == "ek"
    assert a.article_id == "5326-ek-madde-1"
    assert "Ek madde hükmü metni." in a.text


def test_gecici_madde_detected() -> None:
    articles = _parse_main()
    g1 = _by_no(articles, "gecici", "1")
    g2 = _by_no(articles, "gecici", "2")
    assert g1.article_id == "5326-gecici-madde-1"
    assert g2.article_id == "5326-gecici-madde-2"


def test_hyphen_variants_are_tolerated() -> None:
    paragraphs = [
        _p(0, "Madde 1- (1) ASCII tire."),
        _p(2, "Madde 2– (1) En dash tire."),
        _p(4, "Madde 3— (1) Em dash tire."),
    ]
    articles = parse_articles(paragraphs, document_id="d", legislation_number="5326")
    assert [a.article_no for a in articles] == ["1", "2", "3"]
    assert all(a.article_type == "normal" for a in articles)


# --- Canonical IDs --------------------------------------------------------


def test_unique_canonical_ids() -> None:
    articles = _parse_main()
    ids = [a.article_id for a in articles]
    assert len(ids) == len(set(ids))


def test_no_collision_between_madde_ek_gecici_same_number() -> None:
    paragraphs = [
        _p(0, "Madde 1- (1) Normal madde."),
        _p(2, "Ek Madde 1- (1) Ek madde."),
        _p(4, "Geçici Madde 1- (1) Geçici madde."),
    ]
    articles = parse_articles(paragraphs, document_id="d", legislation_number="5326")
    ids = {a.article_id for a in articles}
    assert ids == {"5326-madde-1", "5326-ek-madde-1", "5326-gecici-madde-1"}


# --- Section context -------------------------------------------------------


def test_kisim_bolum_section_context() -> None:
    articles = _parse_main()
    madde1 = _by_no(articles, "normal", "1")
    madde42a = _by_no(articles, "normal", "42/A")
    ek1 = _by_no(articles, "ek", "1")
    assert madde1.section_context == "Birinci Kısım > Birinci Bölüm"
    assert madde42a.section_context == "Birinci Kısım > İkinci Bölüm"
    # a new KISIM resets the previously active BÖLÜM
    assert ek1.section_context == "İkinci Kısım"


# --- Non-article content must not become an Article -----------------------


def test_non_heading_prose_does_not_become_an_article() -> None:
    paragraphs = [
        _p(0, "Genel Hükümler"),
        _p(1, "Bu bir başlık altı açıklama metnidir."),
    ]
    articles = parse_articles(paragraphs, document_id="d", legislation_number="5326")
    assert articles == []


def test_amendment_history_marker_stops_parsing() -> None:
    articles = _parse_main()
    article_nos = [(a.article_type, a.article_no) for a in articles]
    assert ("normal", "99") not in article_nos
    assert len(articles) == 8  # decoy after the marker must not be counted


# --- Determinism and ordering ----------------------------------------------


def test_parse_articles_is_deterministic() -> None:
    a1 = parse_articles(MAIN_FIXTURE, document_id="doc_test", legislation_number="5326")
    a2 = parse_articles(MAIN_FIXTURE, document_id="doc_test", legislation_number="5326")
    assert a1 == a2


def test_article_ordering_matches_source() -> None:
    articles = _parse_main()
    starts = [a.source_paragraph_start for a in articles]
    assert starts == sorted(starts)


def test_source_paragraph_indices_are_original_not_renumbered() -> None:
    articles = _parse_main()
    madde1 = _by_no(articles, "normal", "1")
    # Madde 1 heading is at original index 8, its last body paragraph
    # ("(2) ikinci fıkra metni.") is at original index 12 - NOT sequential
    # positions 0..N invented by the parser.
    assert madde1.source_paragraph_start == 8
    assert madde1.source_paragraph_end == 12


# --- Title handling ---------------------------------------------------------


def test_article_title_captured_when_reliable() -> None:
    articles = _parse_main()
    assert _by_no(articles, "normal", "1").article_title == "Amaç ve kapsam"
    assert _by_no(articles, "normal", "2").article_title == "Tanım"
    assert _by_no(articles, "normal", "44").article_title == "Yürürlük"


def test_article_title_is_null_when_not_reliably_identifiable() -> None:
    articles = _parse_main()
    # Madde 3 directly follows Madde 42/A's heading paragraph -> no title line
    assert _by_no(articles, "normal", "3").article_title is None
    # Ek Madde 1 directly follows the "İKİNCİ KISIM" section heading
    assert _by_no(articles, "ek", "1").article_title is None
    # Geçici Madde 1/2 both directly follow numbered-fıkra/heading paragraphs
    assert _by_no(articles, "gecici", "1").article_title is None
    assert _by_no(articles, "gecici", "2").article_title is None


def test_article_text_excludes_title_and_section_headings() -> None:
    articles = _parse_main()
    madde1 = _by_no(articles, "normal", "1")
    assert "Amaç ve kapsam" not in madde1.text
    assert all("BÖLÜM" not in a.text and "KISIM" not in a.text for a in articles)


# --- Amendment notes and footnote references --------------------------------


def test_amendment_note_extraction() -> None:
    articles = _parse_main()
    madde3 = _by_no(articles, "normal", "3")
    ek1 = _by_no(articles, "ek", "1")
    madde1 = _by_no(articles, "normal", "1")
    assert madde3.amendment_note == "(Değişik: 6/12/2006-5560/31 md.)"
    assert ek1.amendment_note == "(Ek: 11/5/2005-5348/5 md.)"
    assert madde1.amendment_note is None  # "(1)" is a fıkra number, not a note


def test_footnote_reference_ids_propagate_from_paragraphs() -> None:
    """footnote_reference_ids on an ExtractedParagraph (as produced by
    src/ingest.py from real <w:footnoteReference> elements) must propagate
    to Article.footnote_references for whichever article consumes that
    paragraph as body text."""
    articles = _parse_main()
    madde3 = _by_no(articles, "normal", "3")
    madde1 = _by_no(articles, "normal", "1")
    assert madde3.footnote_references == [1]
    assert madde1.footnote_references is None


def test_multiple_footnote_ids_on_one_paragraph_are_all_kept() -> None:
    paragraphs = [_p(0, "Madde 1- (1) Hüküm.", footnote_reference_ids=[2, 3])]
    articles = parse_articles(paragraphs, document_id="d", legislation_number="5326")
    assert articles[0].footnote_references == [2, 3]


def test_footnote_id_on_title_paragraph_is_attributed_to_its_article() -> None:
    """Real-world edge case found in the 5326 source: a short article-title
    paragraph (e.g. "Tüzel kişilerin sorumluluğu") can itself carry a
    footnote reference. The title paragraph is excluded from Article.text,
    but its footnote id must still be traceably attributed to the article
    it titles — not silently dropped, and not attributed to the previous
    article (whose body it is never part of)."""
    paragraphs = [
        _p(0, "Madde 1- (1) İlk madde hükmü."),
        _p(2, "Sorumluluk", footnote_reference_ids=[9]),
        _p(3, "Madde 2- (1) İkinci madde hükmü."),
    ]
    articles = parse_articles(paragraphs, document_id="d", legislation_number="5326")
    madde1 = _by_no(articles, "normal", "1")
    madde2 = _by_no(articles, "normal", "2")
    assert madde1.footnote_references is None
    assert madde2.article_title == "Sorumluluk"
    assert madde2.footnote_references == [9]
    assert "Sorumluluk" not in madde2.text


# --- JSON output -------------------------------------------------------------


def test_parse_document_and_write_articles_json(tmp_path: Path) -> None:
    paragraphs_payload = {
        "document_id": "doc_test",
        "source_file": "data/raw/does-not-exist.docx",
        "paragraph_count": 1,
        "paragraphs": [{"index": 0, "text": "Madde 1- (1) Basit hüküm.", "style_name": "Normal"}],
    }
    import json

    paragraphs_path = tmp_path / "sample.paragraphs.json"
    paragraphs_path.write_text(json.dumps(paragraphs_payload), encoding="utf-8")

    result = chunk.parse_document(paragraphs_path)
    assert result["document_id"] == "doc_test"
    assert result["article_count"] == 1
    assert {"document_id", "article_count", "articles"} <= result.keys()

    output_path = chunk.write_articles_json(result, tmp_path / "sample.articles.json")
    loaded = json.loads(output_path.read_text(encoding="utf-8"))
    assert loaded["article_count"] == 1


# --- Optional integration test: real 5326 source ----------------------------


@pytest.mark.skipif(
    not REAL_SOURCE_PATH.exists(),
    reason=f"integration test: real source not present locally: {REAL_SOURCE_PATH}",
)
def test_integration_real_kabahatler_kanunu_article_count() -> None:
    """Source-validation integration test: the real 5326 source must yield
    exactly 53 article-like units (45 normal numeric + 4 lettered + 1 Ek +
    3 Geçici). Optional/local-only — see docs/source-analysis-5326.md."""
    ingest_result = ingest.ingest_document(REAL_SOURCE_PATH)
    paragraphs = chunk.paragraphs_from_json(ingest_result)
    articles = parse_articles(
        paragraphs,
        document_id=ingest_result["document_id"],
        legislation_number="5326",
    )

    assert len(articles) == 53

    lettered = sorted(a.article_no for a in articles if a.article_type == "normal" and "/" in a.article_no)
    assert lettered == ["42/A", "43/A", "43/B", "43/C"]

    ek = [a for a in articles if a.article_type == "ek"]
    gecici = [a for a in articles if a.article_type == "gecici"]
    assert len(ek) == 1
    assert sorted(a.article_no for a in gecici) == ["1", "2", "3"]

    with_footnotes = [a for a in articles if a.footnote_references]
    assert len(with_footnotes) > 0, "expected at least one real article to carry a footnote reference"
    all_ref_ids = sorted({ref for a in with_footnotes for ref in a.footnote_references})
    assert all_ref_ids == list(range(1, 14))  # footnotes 1..13, see docs/source-analysis-5326.md §4
