"""Offline M12E saved-evidence analysis; local accepted parser/chunker, no retrieval."""
from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from dataclasses import asdict
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports/evaluation/m12e-three-source-failure-analysis"
PRIMARY = [f"k5607-{n:03d}" for n in (2, 3, 4, 14, 25, 26, 9, 29)]
CONTROLS = [f"k5607-{n:03d}" for n in (17, 23, 28, 30, 5, 6)]
CHUNK_PATHS = {"5326": "data/processed/5326-kabahatler-kanunu.chunks.json",
               "4458": "data/processed/4458-gumruk-kanunu.chunks.json",
               "5607": "data/processed/5607-kacakcilikla-mucadele-kanunu.chunks.json"}
TERMS = ["gümrük", "eşya", "gümrük vergileri", "ithalat", "ihracat", "tasfiye", "müsadere", "gümrük işlemleri", "taşıt", "yasak eşya"]
STOP = set("ve veya ile bir bu hangi nasıl nedir için göre olarak olan halinde hâlinde sayılı kanun madde fıkra ne da de ya mı mi".split())
LOCATIONS = {2: [("normal", "2", "1", "b) Gümrüklenmiş değer")],
 3: [("normal", "3", "1", "Eşyayı, gümrük işlemlerine")],
 4: [("normal", "3", "9", "İlgili kanun hükümlerine")],
 14: [("normal", "12", "1", "Yabancı ülkelerden")],
 25: [("normal", "3", "1", "Eşyayı, gümrük işlemlerine"), ("normal", "4", "1", "bir örgütün faaliyeti"), ("normal", "4", "7", "toplum sağlığını")],
 26: [("normal", "3", "1", "Eşyayı, gümrük işlemlerine"), ("normal", "5", "2", "etkin pişmanlık"), ("normal", "5", "3", "mükerrirler")],
 9: [("normal", "6", "4", "Yolcuların")],
 29: [("normal", "3", "2", "aldatıcı işlem"), ("gecici", "10", "1", "gümrük vergilerinin")],
 17: [("normal", "16/a", "1", "teknik düzenlemelere uygun")],
 23: [("normal", "23", "1", "muhbir ve elkoyma")],
 28: [("gecici", "7", "1", "16/A maddesinin")],
 30: [("normal", "5", "2", "Kovuşturma evresinde"), ("gecici", "12", "1", "infaz aşamasında")],
 5: [("normal", "3", "11", "Ulusal marker")],
 6: [("normal", "3", "22", "teşebbüs aşamasında")],
 7: [("normal", "4", "1", "bir örgütün faaliyeti")],
 13: [("normal", "11", "1", "tutanak")],
 15: [("normal", "13", "1", "müsaderesi")],
 19: [("normal", "19", "1", "Mülkî amirler")]}


def _load(name: str) -> Any:
    return json.loads((ROOT / name).read_bytes())


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _key(row: dict[str, Any]) -> str:
    return "/".join((row["document_id"], row["article_type"], row["article_no"].lower()))


def tokens(text: str) -> list[str]:
    """Use Turkish lowercase and alphabetic tokens, without stemming."""
    text = text.replace("İ", "i").replace("I", "ı").lower()
    return re.findall(r"[^\W\d_]+", text, flags=re.UNICODE)


def _snippet(text: str, phrase: str, size: int = 450) -> str:
    at = text.lower().find(phrase.lower())
    if at < 0:
        return "[phrase not found; no excerpt asserted]"
    start = max(0, at - 35)
    return ("…" if start else "") + text[start:start + size].replace("\n", " ") + "…"


def lexical(chunks: list[dict[str, Any]]) -> dict[str, Any]:
    """Count exact normalized contiguous phrases; chunk DF is not law DF."""
    streams = [tokens(c["text"]) for c in chunks]
    total = sum(map(len, streams))
    rows = {}
    for term in TERMS:
        needle = tokens(term)
        counts = [sum(t[i:i+len(needle)] == needle for i in range(len(t)-len(needle)+1)) for t in streams]
        rows[term] = dict(occurrences=sum(counts), per_10000_tokens=sum(counts) / total * 10000,
                          chunk_document_frequency=sum(c > 0 for c in counts),
                          chunk_df_rate=sum(c > 0 for c in counts) / len(chunks))
    return dict(chunk_count=len(chunks), token_count=total, terms=rows)


def _taxonomy(qid: str, duplicate: bool) -> list[dict[str, str]]:
    n = int(qid[-3:])
    entries = []
    if n in (3, 4, 25, 26, 29):
        entries.append(dict(category="E", finding="Observed broad expected source; causal contribution unproven",
            evidence="Madde 3: 8,425 article characters, 23 numbered fıkra positions in 3 chunks. Target text is in chunk 001 (fıkra 1/2/9). The same chunk succeeds for k5607-005."))
    if n in (4, 9, 25, 26, 29):
        entries.append(dict(category="H", finding="Observed cross-reference/composite requirement, not a causal estimate",
            evidence={4:"Madde 3(9) explicitly refers to 4458 for the <=10% discrepancy exception.",
            9:"Question asks when Madde 3 applies; its gold is Madde 6(4), which explicitly refers to Madde 3.",
            25:"Query asks simultaneously for 3(1), 4(1) and 4(7); all five returned chunks belong to 4458.",
            26:"Query asks for 3(1) and 5(2)-(3); all five returned chunks belong to 4458.",
            29:"Query requires 3(2) and Geçici 10. Geçici 11 wins Top1; its wording also concerns 3(2), underpaid customs taxes and vehicles, and explicitly references 4458 Geçici 10."}[n]))
    if duplicate:
        entries.append(dict(category="F", finding="Observed slot competition; counterfactual replacement unknown",
            evidence="4458 Madde 235 occupies two Top5 slots for k5607-009 and k5607-025; only four distinct provisions remain. No 5607 Madde 3 duplicates occur in any complete miss."))
    if n == 2:
        entries.append(dict(category="D", finding="Explicit number did not enforce document discrimination; prefix weakness itself is unproven",
            evidence="Raw query explicitly includes 5607 and gümrüklenmiş değer, yet all five ranked documents are 4458. Document prefix includes 5607 Sayılı Kaçakçılıkla Mücadele Kanunu; no query enrichment or law filter exists."))
    if n in (7, 13, 15, 19):
        entries.append(dict(category="I", finding="Observed same-document, wrong-Article Top1",
            evidence={7:"Madde 3 wins over gold Madde 4 (rank 3); query asks örgüt/three-person aggravation, gold 4(1)-(2).",
                      13:"Madde 10 wins over gold Madde 11 (rank 2); query asks delivery tutanak, while Madde 10 addresses seizure/vehicle handling.",
                      15:"Madde 10 wins over gold Madde 13 (rank 2); 10(2) explicitly cites 13(1)(a), connecting the provisions.",
                      19:"Madde 24 wins over gold Madde 19 (rank 2); 24(1) repeats önlenme, izlenme ve araştırılması but addresses laboratories."}[n]))
    if n in (3, 14):
        entries.append(dict(category="I", finding="Close paraphrase still loses the expected document",
            evidence={3:"Query tabi tutulmadan ülkeye sokulması / gümrük kapıları parallels 3(1) tabi tutmaksızın ülkeye sokan / gümrük kapıları. Strong wording mismatch is not demonstrated.",
                      14:"Query yasak eşya / yükleme veya taşıma belgeleri parallels 12(1) closely. Gold is only 504 characters and one chunk, ruling out broad-Article structure as a universal explanation."}[n]))
    return entries


def _reconstruct_4458(saved: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Fail closed before diagnostics unless admitted source and saved hashes match."""
    sys.path.insert(0, str(ROOT))
    from src.chunk import _load_and_parse_articles, build_chunks

    source = ROOT / "data/processed/4458-gumruk-kanunu.paragraphs.json"
    if not source.exists():
        raise RuntimeError("M12E BLOCKED — 4458 RECONSTRUCTION MISMATCH: accepted paragraphs absent")
    document_id, articles = _load_and_parse_articles(source)
    chunks = build_chunks(articles)
    def require(condition: bool, message: str) -> None:
        if not condition:
            raise RuntimeError("M12E BLOCKED — 4458 RECONSTRUCTION MISMATCH: " + message)
    require(document_id == "4458_gumruk_kanunu", "document identity")
    require(len(articles) == 271 and len(chunks) == 276, "271/276 inventory")
    require(len({a.article_id for a in articles}) == 271, "unique Article IDs")
    require(len({c.chunk_id for c in chunks}) == 276, "unique Chunk IDs")
    require(Counter(a.article_type for a in articles) == {"normal":259,"gecici":11,"islenemeyen_hukum":1}, "Article types")
    require(all(x.document_id == document_id and x.legislation_number == "4458" for x in [*articles,*chunks]), "provenance")
    multi = []
    for a in articles:
        parts = [c for c in chunks if c.article_id == a.article_id]
        require(a.text == "\n".join(c.text for c in parts), "lossless ordered Article reconstruction")
        for i, c in enumerate(parts, 1):
            require(c.chunk_id == f"{a.article_id}-chunk-{i:03d}", "ordered chunk identity")
            require(all(getattr(c, field) == getattr(a, field) for field in ("article_no","article_type","article_title","section_context","source_paragraph_start","source_paragraph_end","footnote_references")), "source metadata preservation")
        if len(parts) > 1:
            multi.append(a.article_id)
    require(set(multi) == {"4458-madde-3", "4458-madde-241", "4458-madde-235", "4458-madde-167", "4458-gecici-madde-6"}, "five accepted multi-chunk provisions")
    article_path = source.with_name("4458-gumruk-kanunu.articles.json")
    if article_path.exists():
        require(_load(str(article_path.relative_to(ROOT)))["articles"] == [asdict(a) for a in articles], "persisted Article equality")
    require(chunks == build_chunks(articles), "deterministic repeat construction")
    by_id = {c.chunk_id:c for c in chunks}
    ranks = [r for q in saved["results"] for r in q["ranks"] if r["document_id"] == document_id]
    require(len(ranks) == 207, "207 ranked slots")
    checks = [dict(chunk_id=r["chunk_id"], saved_sha256=r["text_sha256"], reconstructed_sha256=hashlib.sha256(by_id[r["chunk_id"]].text.encode("utf-8")).hexdigest() if r["chunk_id"] in by_id else None) for r in ranks]
    require(all(c["saved_sha256"] == c["reconstructed_sha256"] for c in checks), "missing ranked ID or text hash mismatch")
    return [asdict(c) for c in chunks], dict(label="deterministically reconstructed 4458 chunk corpus", source=str(source.relative_to(ROOT)), original_persisted_chunks_absent=not (ROOT / CHUNK_PATHS["4458"]).exists(), persisted_articles_present=article_path.exists(), method="Regenerated in memory from accepted processed source using current accepted src/chunk.py implementation; manifest admission; no historical snapshot identity asserted", article_count=271, chunk_count=276, article_types=dict(Counter(a.article_type for a in articles)), multi_chunk_articles=multi, lossless_article_reconstructions=271, source_metadata_preserved=True, unique_article_ids=271, unique_chunk_ids=276, document_id=document_id, legislation_number="4458", ranked_text_hashes_passed=207, missing_ranked_chunk_ids=0, hash_mismatches=0, ranked_slot_checks=checks)


def main() -> None:
    """Generate descriptive reports from immutable local files; never open Chroma."""
    required = ["reports/evaluation/m12d-three-source-retrieval.json", "reports/evaluation/m12d-three-source-retrieval.csv",
                "reports/evaluation/m12d-offline-audit.md", "evaluation/questions_5607.json",
                "reports/evaluation/m10d-two-law-retrieval.json", "src/embed.py", "src/retrieve.py",
                "data/source_manifest.json", "data/processed/5607-kacakcilikla-mucadele-kanunu.articles.json"]
    required += [p for law, p in CHUNK_PATHS.items() if law != "4458"]
    required += ["data/processed/4458-gumruk-kanunu.paragraphs.json", "docs/source-analysis-4458.md", "src/chunk.py", "src/config.py"]
    if (ROOT / "data/processed/4458-gumruk-kanunu.articles.json").exists():
        required.append("data/processed/4458-gumruk-kanunu.articles.json")
    hashes = {p: _hash(ROOT / p) for p in required if (ROOT / p).exists()}
    missing = [p for p in required if not (ROOT / p).exists()]
    saved = _load(required[0])
    old = _load("reports/evaluation/m10d-two-law-retrieval.json")
    gold = {q["id"]: q for q in _load("evaluation/questions_5607.json")["questions"]}
    assert hashes["evaluation/questions_5607.json"] == "30de79d0c7564bf67e7ef01c88e27077d530b50f4a47d3ce9f6df6d1d7b117a2"
    corpus = {law: _load(p)["chunks"] for law, p in CHUNK_PATHS.items() if p in hashes}
    corpus["4458"], reconstruction = _reconstruct_4458(saved)
    chunks = {c["chunk_id"]: c for group in corpus.values() for c in group}
    sources: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for c in chunks.values():
        sources[_key(c)].append(c)
    articles = {_key(a): a for a in _load("data/processed/5607-kacakcilikla-mucadele-kanunu.articles.json")["articles"]}
    verified = 0
    for row in saved["results"]:
        for r in row["ranks"]:
            if r["chunk_id"] in chunks:
                c = chunks[r["chunk_id"]]
                assert hashlib.sha256(c["text"].encode()).hexdigest() == r["text_sha256"]
                assert _key(c) == r["document_source_key"]
                verified += 1
    with (ROOT / required[1]).open(encoding="utf-8-sig", newline="") as handle:
        csv_rows = list(csv.DictReader(handle))
    assert len(csv_rows) == 525 and len(saved["results"]) == 105
    expected_rows = [(q["question"]["id"], r["chunk_id"], r["distance"]) for q in saved["results"] for r in q["ranks"]]
    assert [(r["id"], r["chunk_id"], float(r["distance"])) for r in csv_rows] == expected_rows
    slot_rows = []
    for q in saved["results"]:
        counts = Counter(r["document_source_key"] for r in q["ranks"])
        repeats = {k: v for k, v in counts.items() if v > 1}
        if repeats:
            slot_rows.append(dict(id=q["question"]["id"], repeats=repeats, distinct_provisions=len(counts),
                                  redundant_slots=sum(v-1 for v in repeats.values())))
    repeated_ids = {r["id"] for r in slot_rows}
    data = []
    for row in saved["results"]:
        q = row["question"]
        if q["id"] not in gold:
            continue
        ranks, expected = row["ranks"], {_key(k) for k in q["expected_sources"]}
        best_doc = next((r for r in ranks if r["document_id"] in q["expected_document_ids"]), None)
        best_source = next((r for r in ranks if r["document_source_key"] in expected), None)
        structures = []
        for key in sorted(expected):
            article, parts = articles[key], sources[key]
            assert article["text"] == "\n".join(c["text"] for c in parts)
            structures.append(dict(source=key, article_characters=len(article["text"]), source_chunk_count=len(parts),
                multi_chunk=len(parts)>1, chunks=[dict(chunk_id=c["chunk_id"], characters=len(c["text"]),
                paragraph_numbers=c["paragraph_numbers"], source_paragraph_start=c["source_paragraph_start"], source_paragraph_end=c["source_paragraph_end"]) for c in parts]))
        excerpts = []
        for kind, number, paragraph, phrase in LOCATIONS.get(int(q["id"][-3:]), []):
            key = q["expected_document_ids"][0] + "/" + kind + "/" + number
            matches = [c for c in sources[key] if paragraph in c["paragraph_numbers"]]
            for c in matches:
                excerpts.append(dict(source=key, chunk_id=c["chunk_id"], fikra=paragraph,
                    snippet=_snippet(c["text"], phrase), concentrated_target=True,
                    surrounding_context="Other offence families and exceptions share this chunk" if number == "3" and kind == "normal" else "See chunk paragraph range; no semantic isolation experiment performed"))
        qwords = set(tokens(q["question"])) - STOP
        correct_words = set(tokens(" ".join(articles[k]["text"] for k in expected))) - STOP
        wrong = [r for r in ranks if r["document_id"].startswith("4458")]
        failure = not row["metrics"]["1"]["source_any"] or not row["metrics"]["5"]["source_all"]
        data.append(dict(id=q["id"], query=q["question"], expected_sources=sorted(expected),
            ranks=ranks, best_rank_by_law={law: next((r["rank"] for r in ranks if r["document_id"].startswith(law)), None) for law in CHUNK_PATHS},
            top1_distance=ranks[0]["distance"],
            top1_to_best_correct_document_margin=best_doc["distance"]-ranks[0]["distance"] if best_doc else None,
            top1_to_best_correct_source_margin=best_source["distance"]-ranks[0]["distance"] if best_source else None,
            correct_document_absent_from_saved_top5=best_doc is None,
            expected_source_exists_in_local_corpus={k: bool(sources[k]) for k in expected},
            correct_document_margin_lower_bound=ranks[-1]["distance"]-ranks[0]["distance"] if not best_doc else None,
            margin_lower_bound_caveat="Only conditional on exact global distance ordering; ANN may omit closer items. Not a measured correct-source distance.",
            explicit_5607="5607" in q["question"], query_embedding_includes_5607="5607" in q["question"],
            query_token_count=len(tokens(q["question"])), query_character_count=len(q["question"]),
            source_count=len(expected), provision_types=sorted({s["article_type"] for s in q["expected_sources"]}),
            category=gold[q["id"]]["category"], query_style="Explicit Article/fıkra reference" if re.search(r"madde|fıkra", q["question"], re.I) else "Natural-language topical lookup/paraphrase; manual snippets determine closeness",
            metrics=row["metrics"], structures=structures, expected_excerpts=excerpts,
            query_correct_exact_overlap=sorted(qwords & correct_words), query_correct_overlap_rate=len(qwords & correct_words)/len(qwords),
            competing_4458_sources=[dict(chunk_id=r["chunk_id"], source=r["document_source_key"], rank=r["rank"], distance=r["distance"]) for r in wrong],
            competing_4458_text_comparison={"status":"pending verified text comparison", "top_wrong_chunk":wrong[0]["chunk_id"] if wrong else None,
                "overlapping_terms":None,"correct_source_unique_terms":None,"terms_favoring_wrong_source":None},
            taxonomy=_taxonomy(q["id"], q["id"] in repeated_ids) if failure else [],
            is_primary=q["id"] in PRIMARY, is_control=q["id"] in CONTROLS))
    competitor_counts = Counter(r["document_source_key"] for q in data for r in q["ranks"] if r["document_id"].startswith("4458"))
    competitor_top1 = Counter(q["ranks"][0]["document_source_key"] for q in data if q["ranks"][0]["document_id"].startswith("4458"))
    prior = {r["id"]: r for r in old["results"]}
    comparisons = []
    for q in saved["results"]:
        if not q["question"]["id"].startswith("gk"):
            continue
        p = prior[q["question"]["id"]]
        assert p["question"] == q["question"]["question"]
        changes = [dict(k=k, metric=m, old=p[f"{field}_{k}"], current=q["metrics"][str(k)][m]) for k in (1,3,5) for m,field in (("source_any","any_source_hit_at"),("source_all","all_sources_match_at")) if p[f"{field}_{k}"] != q["metrics"][str(k)][m]]
        comparisons.append(dict(id=p["id"], changes=changes, old_ranks=p["ranks"], current_ranks=q["ranks"], new_5607_slots=sum(r["document_id"].startswith("5607") for r in q["ranks"]),
            removed_old_chunk_ids=sorted({r["chunk_id"] for r in p["ranks"]}-{r["chunk_id"] for r in q["ranks"]})))
    groups = {}
    for name, group in (("complete_misses",[q for q in data if q["correct_document_absent_from_saved_top5"]]),
                        ("all_source_top5_successes",[q for q in data if q["metrics"]["5"]["source_all"]]),
                        ("requested_controls",[q for q in data if q["id"] in CONTROLS[:4]])):
        groups[name] = dict(count=len(group), ids=[q["id"] for q in group], explicit_5607_count=sum(q["explicit_5607"] for q in group),
            multi_source_count=sum(q["source_count"]>1 for q in group),
            mean_query_tokens=mean(q["query_token_count"] for q in group),
            mean_exact_query_gold_overlap=mean(q["query_correct_overlap_rate"] for q in group),
            mean_top1_distance=mean(q["top1_distance"] for q in group),
            mean_document_intrusion_at5=mean(q["metrics"]["5"]["document_intrusion"] for q in group),
            mean_expected_article_chars=mean(mean(s["article_characters"] for s in q["structures"]) for q in group),
            mean_expected_source_chunks=mean(mean(s["source_chunk_count"] for s in q["structures"]) for q in group))
    manifest = _load("data/source_manifest.json")
    prefixes = {m["legislation_number"]: f"{m['legislation_number']} Sayılı {m['title']}" for m in manifest}
    header_examples = {}
    for law in CHUNK_PATHS:
        c = corpus[law][0] if law in corpus else next(r["metadata"] for q in saved["results"] for r in q["ranks"] if r["document_id"].startswith(law))
        label = {"normal":"Madde", "gecici":"Geçici Madde", "ek":"Ek Madde", "islenemeyen_hukum":"Geçici Madde"}[c["article_type"]]
        header_examples[law] = "\n".join([prefixes[law], label + " " + c["article_no"]] + ([c["article_title"]] if c.get("article_title") else [])) + "\n\n"
    report = dict(reconstruction_4458=reconstruction, verdict="M12E BLOCKED — 4458 RECONSTRUCTION MISMATCH" if missing else "M12E READY FOR REVIEW",
        missing_inputs=missing, input_sha256=hashes, saved_questions=105, saved_rank_slots=525,
        local_rank_text_hashes_verified=verified, other_rank_text_hashes_unverifiable=525-verified,
        calls=dict(network=0,openai=0,retrieval=0,chroma_open=0,embedding=0),
        limits=["Top5 is censored: absent means not in saved five, not absent from the whole corpus or known rank 6.",
                "No saved vectors/global distances or ANN trace; no causal embedding explanation or removal counterfactual is possible.",
                "4458 is a deterministically reconstructed 4458 chunk corpus, not the original historical snapshot. All 207 ranked-text hashes match; unranked historical text identity is not independently proven.",
                "Current code and manifest document the embedding template; original embedding input bytes are not exported for every record."],
        embedding=dict(document_prefixes=prefixes, exact_header_examples=header_examples,
            template="document display title + newline + Article label + optional newline Article title + blank line + unchanged chunk text",
            query="embed_texts([query], client=client, model=model, batch_size=1): raw natural language, no enrichment or explicit-law normalization",
            model=saved["retrieval_configuration"], source_refs=["src/embed.py:build_document_display_title/build_article_label/build_embedding_text", "src/retrieve.py:embed_query/retrieve"]),
        questions_5607=data, competitor_slot_counts=dict(competitor_counts.most_common()), competitor_top1_counts=dict(competitor_top1.most_common()),
        lexical=dict(method="Turkish I/İ-aware lowercase; Unicode alphabetic tokens; exact contiguous phrase frequency / 10,000 body tokens and chunk DF. No stemming: gümrük does not count gümrüğe; phrases do not count inflected variants. Descriptive only, not embedding causality.",
            by_law={law:lexical(group) for law,group in corpus.items()}, comparison_4458_vs_5607="blocked" if "4458" not in corpus else "available"),
        slot_competition=dict(question_count=len(slot_rows), reduced_distinct_coverage_question_count=len(slot_rows), rows=slot_rows,
            redundant_slots=sum(r["redundant_slots"] for r in slot_rows),
            by_repeated_source_document=dict(Counter(key.split('/')[0] for r in slot_rows for key in r["repeats"])),
            caveat="Repeated-source slots reduce distinct provision count from 5 to 4 in these cases. Actual gold recovery from diversification is unobserved; ranks 6+ are unavailable."),
        control_comparison=groups,
        historical_4458=dict(delta_percentage_points={m:{str(k):-100/30 for k in (1,3,5)} for m in ("source_any","source_all")},
            changed_ids=[q["id"] for q in comparisons if q["changes"]], comparisons=comparisons,
            total_new_5607_slots=sum(q["new_5607_slots"] for q in comparisons),
            finding="gk001 alone accounts for all six -3.33 percentage-point changes. No 5607 chunk in any of the 150 current 4458 slots. Old Madde 210 at 0.727341 disappears; old ranks 2-5 retain exactly their distances and move to 1-4. Direct 5607 displacement is not supported; ANN candidate omission or another unobserved retrieval-state difference remains unresolved, not diagnosed."))
    _complete_text_analysis(report, corpus)
    _render(report)
    assert hashes == {p:_hash(ROOT / p) for p in hashes}, "An input changed during analysis"
    print(json.dumps(dict(verdict=report["verdict"], missing=missing, questions=len(data), duplicate_questions=len(slot_rows), regression_ids=report["historical_4458"]["changed_ids"]),ensure_ascii=True))


CASE_FINDINGS = {
    "002": "Valuation language connects 4458/25 (alternative customs valuation, sale price, calculated value) to the requested definition. The 5607 definition and import/export components remain the correct target; the explicit law number did not enforce scope.",
    "003": "4458/236 concerns goods removed from warehouses before customs procedures finish and administrative fines. This is a concrete procedural/penalty parallel, but 5607 specifies entry into the country, customs gates, imprisonment and judicial fines. Close correct wording still loses; lexical mismatch is not established.",
    "004": "4458/141 shares export, quantity, declaration and value/difference vocabulary, but calculates outward-processing import taxes. It does not supply the requested fictitious-export offence. 5607/3(9) closely answers the query and itself refers to 4458 for the ten-percent exception; these connections plausibly support topical competition but do not explain the ranking causally.",
    "009": "4458/235(3) closely parallels the passenger, belongings/vehicle and contrary-declaration situation, then imposes doubled customs taxes. 5607/6(4) instead supplies the two conditions for applying Article 3. This is unusually concrete overlap across distinct legal consequences.",
    "014": "4458/56 concerns goods barred from import and permission for transit, warehousing or re-export, whereas 5607/12 addresses prohibited goods shown in loading/transport documents and secure return/transit. Shared prohibited-goods handling plausibly connects them; the 5607 source is short and directly worded.",
    "025": "4458/57 repeatedly describes customs procedures being stopped, goods detained, court decisions and disposal, offering general procedure/enforcement overlap. It concerns intellectual-property rights, not organized crime or public-health aggravation. The composite gold request is wholly absent from Top5; query composition and broad Article 3 dilution remain unproven causal hypotheses.",
    "026": "4458/57 supplies customs-procedure, goods, application and court vocabulary, but concerns intellectual-property detention, not effective remorse, payment reductions or investigation/prosecution stages. Shared procedural wording is plausible but weaker than a matching offence; why it wins remains unproven. No correct source is in Top5.",
    "029": "4458 transitional Article 9 also addresses seized land vehicles, application deadlines, payment, return and completed liquidation exclusions. Its Article 235/confiscated-public-property and special-consumption-tax scheme differs from the requested 5607 transitional Article 10. The actual Top1 is 5607 transitional Article 11; this 4458 competitor is rank 2.",
}
TOPICS = {
    "235": "Administrative penalties for prohibited/restricted imports/exports, declaration discrepancies and passenger goods",
    "57": "Intellectual-property goods: detention, suspension of customs procedures and disposal",
    "236": "Warehouse irregularities, unauthorized removal and administrative fines",
    "25": "Alternative customs valuation methods",
    "24": "Customs transaction value and sale-price conditions",
    "167": "Customs tax exemptions, including personal and passenger goods",
}


def _complete_text_analysis(report: dict[str, Any], corpus: dict[str, list[dict[str, Any]]]) -> None:
    """Attach exact excerpts and descriptive comparisons only after reconstruction gates."""
    chunks = {c["chunk_id"]:c for group in corpus.values() for c in group}
    for q in report["questions_5607"]:
        wrong = q["competing_4458_sources"]
        if not wrong:
            q["competing_4458_text_comparison"] = dict(status="no saved 4458 competitor")
            continue
        c = chunks[wrong[0]["chunk_id"]]
        qw = set(tokens(q["query"])) - STOP
        gold_text = " ".join(e["snippet"] for e in q["expected_excerpts"])
        gw, ww = set(tokens(gold_text)) - STOP, set(tokens(c["text"])) - STOP
        # Select an actual source line by exact query-token overlap; never synthesize text.
        line = max(c["text"].splitlines(), key=lambda line: len(qw & set(tokens(line))))
        comparison = dict(status="complete", evidence_corpus=report["reconstruction_4458"]["label"], top_wrong_chunk=c["chunk_id"], rank=wrong[0]["rank"], snippet=line,
            overlapping_terms=sorted(qw & gw & ww), correct_source_unique_terms=sorted((qw & gw)-ww), terms_favoring_wrong_source=sorted(qw & ww), wrong_source_distinct_query_terms=sorted((qw & ww)-gw),
            term_scope="Exact normalized tokens; correct terms use displayed target excerpts, wrong terms use the ranked chunk. Unique means absent from this competitor, not legally unique. Inflections are not stemmed.",
            finding=CASE_FINDINGS.get(q["id"][-3:], "Descriptive token comparison; no causal attribution."), evidence_level="SUPPORTED INTERPRETATION; token sets and excerpts OBSERVED; embedding causality UNPROVEN HYPOTHESIS")
        q["competing_4458_text_comparison"] = comparison
    competitors = []
    for no, topic in TOPICS.items():
        key = "4458_gumruk_kanunu/normal/" + no
        parts = [c for c in corpus["4458"] if _key(c) == key]
        ids = [q["id"] for q in report["questions_5607"] if any(r["document_source_key"] == key for r in q["ranks"])]
        overlaps = sorted(set(w for q in report["questions_5607"] if q["id"] in ids for w in set(tokens(q["query"])) & set(tokens(" ".join(c["text"] for c in parts))) if w not in STOP))
        competitors.append(dict(article_no=no, article_title=parts[0]["article_title"], descriptive_topic=topic, question_count=len(ids), question_ids=ids, top1_wins=report["competitor_top1_counts"].get(key,0), slots=report["competitor_slot_counts"].get(key,0), relevant_query_overlap_terms=overlaps, opening_excerpt=parts[0]["text"][:500]))
    report["strongest_4458_competitors"] = competitors
    report["root_cause_evidence"] = dict(observed="Seven of 12 wrong Top1 results are wrong-document (58.33%); five are same-document wrong Article (41.67%). Six of seven ALL@5 failures exclude 5607 (85.71%); one is partial. All 525 saved rank-text hashes match local/reconstructed texts. No demonstrated source omission/provenance defect.", supported_interpretation="Document discrimination dominates observed Top5 failures. Actual 4458 procedure, valuation, passenger and vehicle provisions supply plausible cross-law competition. Broad Madde 3 mixes offence families in a shared vector input; this is a plausible contributor, not a demonstrated material effect.", unproven_hypothesis="Embedding causality, dilution effect size, effects of reranking/diversification, and the cause of gk001 omission remain unproven. No 5607 displacement of gk001 is observed.")
    assert all(q["competing_4458_text_comparison"]["status"] == "complete" for q in report["questions_5607"] if q["is_primary"])
    assert set(("4458","5607")) <= report["lexical"]["by_law"].keys()


def _render(s: dict[str, Any]) -> None:
    cases = {q["id"]: q for q in s["questions_5607"]}
    margin009 = cases["k5607-009"]["top1_to_best_correct_source_margin"]
    margin029 = cases["k5607-029"]["top1_to_best_correct_source_margin"]
    distance017 = cases["k5607-017"]["top1_distance"]
    OUT.with_suffix(".json").write_text(json.dumps(s, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    lines = ["# M12E — Three-source retrieval failure analysis", "", s["verdict"], "",
        "Analysis only. No retrieval optimization was performed. No OpenAI/network, retrieval, embedding or Chroma operation was performed. M12D metrics and frozen datasets are unchanged.", "",
        "## Evidence boundary", "", "Missing required inputs: " + (", ".join(s["missing_inputs"]) or "none; original 4458 persisted chunks artifact remains absent"), "",
        "The original persisted 4458 chunks.json was absent. The deterministically reconstructed 4458 chunk corpus was regenerated in memory from the accepted processed source using the current accepted chunking implementation. All 207 4458 M12D ranked-text hashes match exactly; structural invariants match the accepted 271 Articles / 276 chunks historical result. This supports text diagnostics, not a claim that this is the original historical snapshot.", "",
        "Supplemental read-only inputs: M10D two-law JSON for regression; source manifest for exact titles; existing 5607 Article JSON for exact character counts (each Article verified equal to newline-joined accepted chunks). Full input hashes are in JSON.", "",
        f"Verified {s['saved_questions']} saved questions / {s['saved_rank_slots']} ranked slots; {s['local_rank_text_hashes_verified']} available chunk-text rank hashes match. CSV IDs/distances agree with JSON. All 207 reconstructed 4458 ranked texts are verified.", ""]
    lines += ["- " + limit for limit in s["limits"]]
    lines += ["", "## Required conclusions", "",
        "1. **Indexing/provenance:** no evidence of a missing 5607 gold provision or source-identity defect. All expected sources exist in the accepted local corpus; saved M12D checks report 375 records (53/276/46) and gold-key existence. This does not independently prove every vector correct or exclude an ANN issue.",
        "2. **Document discrimination:** all six complete misses have five 4458 slots and no 5607 slot: k5607-002/003/004/014/025/026. This is the dominant observed Top5 failure pattern, not yet a proven semantic root cause.",
        "3. **4458 competitors:** Madde 235 occupies 9 slots across 7 of the 30 questions; 236 and 57 occupy 3 each. Among wrong-document Top1 cases, 57 wins twice; 25, 236, 141, 56 and 235 once each.",
        "4. **003/004:** target fıkra 1 and 9 are both in Madde 3 chunk 001. Both questions closely track the gold text, so missing content or strong paraphrase mismatch is not established. Their five winners are 4458. Fıkra 9 itself explicitly cross-refers to 4458 for the <=10% exception. Semantic dilution in a broad chunk is plausible, unproven.",
        "5. **025/026:** combine 3(1) with 4(1)/(7) or 5(2)/(3), respectively, without naming 5607. Both return 4458 Madde 57 at Top1 and no gold source by Top5. Multi-clause topical competition is a hypothesis; the reconstructed 57 text shares customs-procedure and enforcement language but does not answer organized-crime, public-health or effective-remorse conditions. This is a supported topical interpretation, not a causal estimate.",
        "6. **Madde 3 structure:** 8,425 characters, chunks of 3,742 / 3,692 / 989 characters, covering fıkra 1–11 / 12–19 / 20–23. Its seven gold questions have four complete misses, one partial miss, and two Top1 successes (005/006). This association is confounded by topic and query composition. No Madde 3 chunk occupies any slot in the six complete misses; duplicate Madde 3 slots therefore do not directly cause those misses. Material causal contribution is unproven.",
        "7. **Wrong document versus wrong Article:** seven Top1 wrong documents (six complete misses plus 009), five additional same-document wrong-Article Top1 cases (007/013/015/019/029). At Top5, six of seven ALL failures exclude 5607 entirely; 029 is the sole partial failure, with gold Geçici 10 at rank 4 and Madde 3 absent. No same-document complete miss occurs. Three of its five slots are 4458, while same-document Geçici 11 also competes.",
        "8. **4458 regression:** -3.33 percentage points at every ANY/ALL cutoff, one question (gk001), not evidence of direct 5607 displacement. No 5607 chunks occur in any current 4458 Top5. Madde 210 drops from historical rank 1 despite its old distance being lower than every current slot; cause unresolved from saved evidence.",
        "9. **Next experiments:** prioritize explicit-law normalization/title enrichment (and a separately measured explicit-law filter), source-aware provision/fıkra candidate scoring for broad/composite queries, and a pre-adoption retrieval-candidate completeness diagnostic for gk001. These are development-informed proposals, not production choices. Reconstruction gates now pass; interventions still require new evaluation.", "",
        "## Document versus query embedding signal", "", "Source: `src/embed.py` build_document_display_title/build_article_label/build_embedding_text; `src/retrieve.py` embed_query/retrieve. Manifest was inspected read-only.", "",
        "Exact first-line prefixes:", ""]
    for law, prefix in s["embedding"]["document_prefixes"].items():
        lines += [f"- {law}: `{prefix}`"]
    lines += ["", "The next line is Madde N / Ek Madde N / Geçici Madde N; an Article title follows only when present, then a blank line and unchanged chunk text. For example, 5607 Madde 16/A includes `Kaçak akaryakıtın tasfiyesi`. Document IDs themselves are not an extra embedding prefix. Exact representative complete headers are stored in JSON.", "",
        "Queries are embedded exactly as raw natural language: `embed_texts([query], ..., batch_size=1)`. A query saying ‘5607 sayılı Kanunda’ receives no law-aware normalization or title enrichment. The number reaches the query embedding only when already in the question. Document title enrichment exists only on the document side. The saved configuration is text-embedding-3-small, 1536 dimensions, L2, K=5, no filter/rerank/expansion or deduplication. No claim about numerical prefix strength can be established without an intervention.", "",
        "## Rank and distance inventory: all 30 questions", "", "Each JSON question records all five full chunk/document/source IDs and raw distances. Margin means best gold-source distance minus Top1 distance; a separate document margin is stored. Null means censored beyond saved Top5, not zero or a measured rank 6. Conditional Top5-distance gaps in JSON are not global ANN lower bounds.", "",
        "| ID | Best ranks 5607/4458/5326 | Top1 L2 | Gold-source margin | Expected document absent @5 |", "|---|---|---:|---:|---|"]
    for q in s["questions_5607"]:
        margin = q["top1_to_best_correct_source_margin"]
        lines += [f"| {q['id']} | {' / '.join(str(q['best_rank_by_law'][law]) for law in ('5607','4458','5326'))} | {q['top1_distance']:.6f} | {margin:.6f} | {q['correct_document_absent_from_saved_top5']} |" if margin is not None else f"| {q['id']} | {' / '.join(str(q['best_rank_by_law'][law]) for law in ('5607','4458','5326'))} | {q['top1_distance']:.6f} | unavailable | {q['correct_document_absent_from_saved_top5']} |"]
    lines += ["", f"009: correct document/source rank 3, distance margin {margin009:.9f}. 029: correct document at rank 1 but wrong Article; first gold source rank 4, margin {margin029:.9f}. Controls 017/023/028/030 have a gold source at Top1 (margin zero); 030 obtains all gold sources by Top3. Successful 017 has Top1 distance {distance017:.9f}, greater than the wrong Top1 distance of several failures: raw L2 is not a universal correctness threshold.", "",
        "## Primary cases and controls: exact gold snippets and ranked competitors", ""]
    for q in s["questions_5607"]:
        if not (q["is_primary"] or q["is_control"]):
            continue
        lines += [f"### {q['id']}", "", q["query"], "", f"Explicit 5607/query-input number: {q['explicit_5607']}. Expected: {', '.join(q['expected_sources'])}.", ""]
        for e in q["expected_excerpts"]:
            lines += [f"- `{e['chunk_id']}`, fıkra {e['fikra']}: {e['snippet']}"]
        lines += ["", "Exact normalized query/gold token overlap (no stemming, not discriminative against 4458): " + ", ".join(q["query_correct_exact_overlap"]), "",
                  "Exact saved competitors (text comparison follows):", ""]
        for r in q["competing_4458_sources"]:
            lines += [f"- Rank {r['rank']}: `{r['chunk_id']}` / `{r['source']}`, L2={r['distance']:.9f}."]
        cmp = q["competing_4458_text_comparison"]
        if cmp["status"] == "complete":
            lines += ["", f"Top-ranked wrong 4458 excerpt (rank {cmp['rank']}): {cmp['snippet']}", "", "Shared query/target/competitor tokens: " + ", ".join(cmp["overlapping_terms"]), "Target query terms absent from competitor: " + ", ".join(cmp["correct_source_unique_terms"]), "Query terms present in wrong competitor: " + ", ".join(cmp["terms_favoring_wrong_source"]), cmp["term_scope"], "", cmp["evidence_level"] + ": " + cmp["finding"], ""]
        if not q["competing_4458_sources"]:
            lines += ["- No 4458 competitor in the saved five."]
        lines += [""]
    lines += ["## Evidence-backed taxonomy", "", "Classification describes observed properties, not measured causal attribution. A (cross-document terminology), B (generic legal wording as a cause), C (more like 4458), and G (strong paraphrase mismatch) are not assigned: causal attribution is not established; descriptive cross-document overlap is supplied above. D is limited to observed failure of an explicit number to enforce document choice, not a demonstrated weak vector prefix. E/F/H/I evidence follows.", ""]
    for q in s["questions_5607"]:
        for t in q["taxonomy"]:
            lines += [f"- **{q['id']} / {t['category']} — {t['finding']}:** {t['evidence']}"]
    lines += ["", "## Article length and chunk structure", "", "Exact lengths come from accepted local Article text checked against concatenated chunks. All failed expected provisions exist in the local corpus. Fıkra locations and individual chunk IDs/ranges are in JSON and case snippets above.", "",
        "| ID | Expected source | Article characters | Chunks | Multi-chunk |", "|---|---|---:|---:|---|"]
    for q in s["questions_5607"]:
        if not q["taxonomy"] and not q["is_control"]:
            continue
        for st in q["structures"]:
            lines += [f"| {q['id']} | {st['source']} | {st['article_characters']} | {st['source_chunk_count']} | {st['multi_chunk']} |"]
    lines += ["", "Madde 3 chunk 001 surrounds the targeted import and export offences with transit, temporary import, prohibited goods, fuel and marker offences. The target is present and concentrated within its fıkra, but the vector covers all 11 fıkras. Madde 23 is also broad: 7,509 characters split 3,766/3,742 (fıkra 1–4 / 5–9); k5607-023 succeeds on chunk 001 and no saved Top5 repeats this source. Multi-chunk structure alone is therefore not sufficient to predict failure.", "",
        "## Slot competition: all 105 saved rankings", "", f"{s['slot_competition']['question_count']} questions have repeated DocumentSourceKeys through different chunk IDs; each has 4 distinct provisions in 5 slots ({s['slot_competition']['redundant_slots']} redundant slots total). Different Articles are not duplicates.", ""]
    for r in s["slot_competition"]["rows"]:
        lines += [f"- {r['id']}: {r['repeats']}"]
    lines += ["", "By repeated provision document: 4458=4 question cases, 5607=2, 5326=0. Of the six complete 5607 misses, only 025 has duplicates (4458/235); 009 also repeats 4458/235 but finds gold rank 3. No duplicate-source competition in 029. Diversification would increase distinct-source count but its effect on gold coverage cannot be recovered from Top5 alone. No deduplication was performed.", "",
        "## Failure versus successful controls", "", "Groups are descriptive and small. Question-length tokenizer excludes numeric strings; explicit 5607 is measured separately. Exact token overlap ignores Turkish inflections and says nothing about vector similarity. Direct/paraphrase style is not inferred as a binary psychological category; explicit references and frozen case categories are stored per question.", "", "```json", json.dumps(s["control_comparison"],ensure_ascii=False,indent=2), "```", "",
        "Complete misses include one explicitly numbered query (002), whereas all four requested successful controls omit 5607. Thus lack of a number is neither necessary nor sufficient for failure. Short one-chunk 2 and 12 also fail. Geçici 7 succeeds; composite Geçici 12 + Madde 5 succeeds; Geçici 10 + Madde 3 partially fails. A blanket transitional-provision explanation is unsupported.", "",
        "## Offline lexical statistics", "", s["lexical"]["method"], "", "Descriptive lexical evidence, not embedding-causality evidence. 4458 uses the deterministically reconstructed corpus; 5607 uses accepted chunks.", "",
        "| Law | Term | Occurrences | Per 10k tokens | Chunk DF | Chunk DF rate |", "|---|---|---:|---:|---:|---:|"]
    for law in ("4458", "5607"):
        for term, v in s["lexical"]["by_law"][law]["terms"].items():
            lines += [f"| {law} | {term} | {v['occurrences']} | {v['per_10000_tokens']:.2f} | {v['chunk_document_frequency']} / {s['lexical']['by_law'][law]['chunk_count']} | {v['chunk_df_rate']:.4%} |"]
    lines += ["", "## Strongest 4458 competitors", "", "Topics below summarize actual text; they are not invented Article titles. Question counts deduplicate multiple slots from the same provision.", "", "| Article | Topic | Questions | Top1 wins | Relevant exact query terms |", "|---|---|---:|---:|---|"]
    for c in s["strongest_4458_competitors"]:
        lines += [f"| {c['article_no']} | {c['descriptive_topic']} | {c['question_count']} | {c['top1_wins']} | {', '.join(c['relevant_query_overlap_terms'])} |"]
    lines += ["", "235 is plausible for valuation, import/export penalties and passenger questions; 57 for customs-procedure suspension/enforcement wording; 236 for goods moved before procedures finish; 24/25 for valuation; 167 for personal/passenger tax exemptions. Their legal consequences differ from the 5607 targets. Exact opening excerpts and affected question IDs are retained in JSON.", "", "## Evidence levels", ""]
    for level, finding in s["root_cause_evidence"].items():
        lines += [f"- **{level.upper().replace('_', ' ')}:** {finding}"]
    lines += ["", "5326 normalized statistics are also provided in JSON. Counts use body text only, excluding enrichment prefixes and avoiding artificial title repetitions.", "",
        "## Historical 4458 regression", "", "| Metric | M10D @1/3/5 | M12D @1/3/5 | Delta (percentage points) |", "|---|---|---|---|",
        "| ANY | 56.67 / 73.33 / 80.00 | 53.33 / 70.00 / 76.67 | -3.33 / -3.33 / -3.33 |",
        "| ALL | 46.67 / 66.67 / 76.67 | 43.33 / 63.33 / 73.33 | -3.33 / -3.33 / -3.33 |", "",
        s["historical_4458"]["finding"], "", "All 30 paired old/current rankings and changes are stored in JSON. We cannot infer that adding 5607 caused the gk001 omission merely because it occurred later. A future authorized candidate-completeness investigation should precede attributing this regression to semantic competition.", "",
        "## Future experiments — analysis only", "", "No production winner is selected. M10E B2 was NOT validated and is not a production candidate by default. Every newly designed candidate informed by M12D/M12E is development-informed; **future adoption requires a new unseen holdout**, in addition to these diagnostic development questions.", "",
        "| Direction | Target / likely benefit | Risk | Production semantics change if adopted? | Re-embedding required? | New unseen holdout? |",
        "|---|---|---|---|---|---|",
        "| Explicit-law query normalization/title enrichment; separately test an explicit-law filter | Document discrimination, especially explicit 002; make named scope usable | Wrong user number, cross-law questions, query drift; only a minority of failures name 5607 | Yes, query input or candidate scope | No corpus re-embedding; query embeddings change for normalization | Yes |",
        "| Source-aware reranking / fıkra-focused candidate scoring; separately test broad-Article chunking | Madde 3 topical breadth and composite 025/026/029, same-law Article mistakes | Gold cannot be recovered if absent from candidate pool; overfitting, lost context | Yes, ranking or index representation | Reranking alone: no; changed chunks/document embedding text: yes | Yes |",
        "| Larger candidate K plus completeness diagnostic before downstream selection | Censored complete misses and unexplained gk001 omission | Cost/noise; saved evidence cannot estimate recovery | Yes if adopted for retrieval; offline diagnostic alone no | No corpus re-embedding | Yes for adoption |",
        "| Distinct-source diversification | Six repeated-slot cases, especially 009/025 | May remove complementary fıkra evidence; most complete misses have no duplicates | Yes | No | Yes |",
        "| Hybrid lexical+dense | Close gold phrasing in 003/004/014; hypothesis supported by descriptive text comparison, not tested | Shared terms may strengthen wrong law; M10E B2 not validated | Yes | No dense re-embedding; lexical index required | Yes |",
        "| Document routing | Six complete wrong-document misses | Routing errors hide correct law; cross-document questions; must route on evidence, not gold labels | Yes | Depends on route implementation; not inherently | Yes |", "",
        "No interventions were implemented or benchmarked. The top three investigation directions are the first three rows; ordering is informed by the verified competitor texts, with benefits still untested.", "",
        "## Review boundary", "", "Only this analysis Markdown/JSON, the human-auditable CSV matrix and the offline analysis script using the accepted parser/chunker are created. No production module, frozen dataset or M12D report is modified. No commit. Test-gate outcome is reported at delivery."]
    OUT.with_suffix(".md").write_text("\n".join(line.rstrip() for line in lines).rstrip()+"\n",encoding="utf-8")
    path = ROOT / "reports/evaluation/m12e-failure-matrix.csv"
    fields = ["id","query","expected_sources","rank","chunk_id","document_id","source","distance","best_5607_rank","best_4458_rank","best_5326_rank","source_margin","document_margin","correct_document_absent_top5","gold_exists_in_local_corpus","explicit_5607","query_tokens","taxonomy","competitor_text_status","top_wrong_4458_snippet","text_finding"]
    with path.open("w",encoding="utf-8-sig",newline="") as handle:
        writer = csv.DictWriter(handle,fieldnames=fields)
        writer.writeheader()
        for q in s["questions_5607"]:
            for r in q["ranks"]:
                writer.writerow(dict(id=q["id"],query=q["query"],expected_sources=" | ".join(q["expected_sources"]),rank=r["rank"],chunk_id=r["chunk_id"],document_id=r["document_id"],source=r["document_source_key"],distance=r["distance"],
                    best_5607_rank=q["best_rank_by_law"]["5607"],best_4458_rank=q["best_rank_by_law"]["4458"],best_5326_rank=q["best_rank_by_law"]["5326"],source_margin=q["top1_to_best_correct_source_margin"],document_margin=q["top1_to_best_correct_document_margin"],correct_document_absent_top5=q["correct_document_absent_from_saved_top5"],gold_exists_in_local_corpus=all(q["expected_source_exists_in_local_corpus"].values()),explicit_5607=q["explicit_5607"],query_tokens=q["query_token_count"],taxonomy=" | ".join(t["category"] for t in q["taxonomy"]), competitor_text_status=q["competing_4458_text_comparison"]["status"], top_wrong_4458_snippet=q["competing_4458_text_comparison"].get("snippet", ""), text_finding=q["competing_4458_text_comparison"].get("finding", "")))


if __name__ == "__main__":
    main()
