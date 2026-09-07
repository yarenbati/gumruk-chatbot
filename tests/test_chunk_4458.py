"""Focused M10B parser/chunker regressions for structures observed in 4458."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import pytest

from src import chunk
from src.ingest import ExtractedParagraph

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PARAGRAPHS_4458 = PROJECT_ROOT / "data/processed/4458-gumruk-kanunu.paragraphs.json"


def _p(index: int, text: str, style: str = "Normal") -> ExtractedParagraph:
    return ExtractedParagraph(index=index, text=text, style_name=style)


def _parse(paragraphs: list[ExtractedParagraph], number: str = "4458") -> list[chunk.Article]:
    return chunk.parse_articles(paragraphs, document_id=f"doc_{number}", legislation_number=number)


@pytest.mark.parametrize("heading", ["Madde 5/A- X", "Madde 5 /A- X", "Madde 5/ A- X", "Madde 5 / A- X"])
def test_suffix_whitespace_is_canonicalized(heading: str) -> None:
    article = _parse([_p(0, heading)])[0]
    assert article.article_no == "5/A"
    assert article.article_id == "4458-madde-5-a"


def test_existing_5326_suffix_id_is_unchanged() -> None:
    article = _parse([_p(0, "Madde 42/A- (1) Hüküm.")], number="5326")[0]
    assert (article.article_no, article.article_id) == ("42/A", "5326-madde-42-a")


def _article(text: str, article_id: str = "4458-madde-1") -> chunk.Article:
    return chunk.Article(
        article_id=article_id, document_id="doc", legislation_number="4458",
        article_no="1", article_type="normal", article_title=None,
        section_context=None, text=text, source_paragraph_start=0,
        source_paragraph_end=text.count("\n"),
    )


def test_parenthesized_and_numbered_dot_fikra_are_supported() -> None:
    paren = chunk.build_chunks([_article("Madde 1- (1) Bir.\n(2) İki.")], max_chars=20)
    dotted = chunk.build_chunks([_article("Madde 1- 1. Bir.\n2. İki.\n3. Üç.")], max_chars=20)
    assert [n for c in paren for n in c.paragraph_numbers or []] == ["1", "2"]
    assert [n for c in dotted for n in c.paragraph_numbers or []] == ["1", "2", "3"]


def test_dotted_list_inside_fikra_is_not_promoted_without_sequence_context() -> None:
    text = "Madde 1- Hüküm.\n2. Bu bir liste kalemidir.\n3. Bu da liste kalemidir."
    chunks = chunk.build_chunks([_article(text)], max_chars=20)
    assert len(chunks) == 1
    assert chunks[0].paragraph_numbers is None


def test_lettered_bent_stays_with_owning_numbered_dot_fikra() -> None:
    text = "Madde 1- 1. " + "x" * 30 + "\na) A bendi.\nb) B bendi.\n2. " + "y" * 30
    chunks = chunk.build_chunks([_article(text)], max_chars=45)
    assert len(chunks) == 2
    assert "a) A bendi." in chunks[0].text and "b) B bendi." in chunks[0].text
    assert chunks[1].text.startswith("2. ")
    assert "\n".join(c.text for c in chunks) == text


def test_single_oversized_dotted_fikra_remains_intact() -> None:
    huge = "1. " + "uzun " * 1000
    chunks = chunk.build_chunks([_article("Madde 1-\n" + huge)], max_chars=40)
    assert any(huge in c.text for c in chunks)
    assert "\n".join(c.text for c in chunks) == "Madde 1-\n" + huge


@pytest.mark.parametrize(
    ("ordinal", "expected"),
    [("ONBİRİNCİ", "Onbirinci"), ("ONİKİNCİ", "Onikinci"), ("ONÜÇÜNCÜ", "Onüçüncü")],
)
def test_late_kisim_ordinals_are_recognized(ordinal: str, expected: str) -> None:
    article = _parse([_p(0, f"{ordinal} KISIM"), _p(1, "Madde 1- Hüküm.")])[0]
    assert article.section_context == f"{expected} Kısım"


def test_ayirim_is_preserved_in_hierarchical_context() -> None:
    article = _parse([
        _p(0, "BİRİNCİ KISIM"), _p(1, "İKİNCİ BÖLÜM"),
        _p(2, "ÜÇÜNCÜ AYIRIM"), _p(3, "Madde 1- Hüküm."),
    ])[0]
    assert article.section_context == "Birinci Kısım > İkinci Bölüm > Üçüncü Ayırım"


def test_special_temporary_article_has_neutral_unique_namespace() -> None:
    articles = _parse([
        _p(0, "Geçici Madde 1- Ana geçici hüküm."),
        _p(1, "Madde 248- Yürütme hükmü."),
        _p(2, "4458 SAYILI KANUNA İŞLENEMEYEN HÜKÜMLER"),
        _p(3, "1) 5911 sayılı Kanunun Geçici Maddesi:"),
        _p(4, "Geçici Madde 1- Özel hüküm."),
    ])
    main, madde248, special = articles
    assert main.article_id == "4458-gecici-madde-1"
    assert special.article_type == "islenemeyen_hukum"
    assert special.article_id == "4458-islenemeyen-hukum-gecici-madde-1"
    assert special.article_title == "1) 5911 sayılı Kanunun Geçici Maddesi:"
    assert special.section_context == "4458 SAYILI KANUNA İŞLENEMEYEN HÜKÜMLER"
    assert "İŞLENEMEYEN" not in madde248.text and "5911" not in madde248.text
    assert len({a.article_id for a in articles}) == 3


def test_mulga_body_is_not_stolen_as_next_article_title() -> None:
    articles = _parse([
        _p(0, "Madde 188- 1. Birinci fıkra."),
        _p(1, "3. (Mülga: 18/6/2009-5911/68 md.)"),
        _p(2, "Madde 189- 1. Sonraki madde."),
    ])
    assert "Mülga" in articles[0].text
    assert articles[1].article_title is None


def test_legitimate_title_still_remains_a_title() -> None:
    articles = _parse([_p(0, "Sorumluluk"), _p(1, "Madde 1- Hüküm.")])
    assert articles[0].article_title == "Sorumluluk"
    assert "Sorumluluk" not in articles[0].text


@pytest.mark.skipif(not PARAGRAPHS_4458.exists(), reason="local ignored 4458 paragraph artifact absent")
def test_local_4458_inventory_and_reconstruction() -> None:
    data = chunk.load_paragraphs_json(PARAGRAPHS_4458)
    articles = chunk.parse_articles(
        chunk.paragraphs_from_json(data), document_id=data["document_id"], legislation_number="4458"
    )
    assert len(articles) == 271
    assert Counter(a.article_type for a in articles) == {
        "normal": 259, "gecici": 11, "islenemeyen_hukum": 1,
    }
    expected_suffixes = {"5/A", "10/A", "35/A", "35/B", "35/C", "165/A", "165/B", "165/C", "165/D", "191/A", "218/A"}
    assert {a.article_no for a in articles if "/" in a.article_no} == expected_suffixes
    assert len({a.article_id for a in articles}) == len(articles)
    chunks_a = chunk.build_chunks(articles)
    chunks_b = chunk.build_chunks(articles)
    assert [c.chunk_id for c in chunks_a] == [c.chunk_id for c in chunks_b]
    assert all(c.text for c in chunks_a)
    for article in articles:
        assert "\n".join(c.text for c in chunks_a if c.article_id == article.article_id) == article.text
