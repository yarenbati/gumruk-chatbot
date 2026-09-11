"""Oracle decomposition diagnostic; saved G0 and one-shot copy-only O1/O2/O3."""
from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, median
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import run_m12d_three_source as m12d
from scripts import run_m12fb_candidate_pool as depth
from scripts.run_m12fa_explicit_law import cached_embeddings
from src import config, embed, evaluate_documents as ev, retrieve, source_registry

ROOT = m12d.ROOT
OUT = ROOT / "reports/evaluation/m12fc-oracle-decomposition"
HEAD = "55100c5d6830eb51a45c85ab167af534e6e8b5c2"
DOCUMENT = "5607_kacakcilikla_mucadele_kanunu"
G0_PATH = ROOT / "reports/evaluation/m12fb-candidate-pool-diagnostic.json"
PRIMARY = [f"k5607-{n:03d}" for n in (2,3,4,25,26,29)]
CONTROLS = [f"k5607-{n:03d}" for n in (14,17,23,28,30)]
VARIANTS = ("G0","O1","O2","O3")
CUTOFFS = (1,3,5,10,20,50)
NOTICE = "Oracle-filter performance is a decomposition diagnostic, not deployable retrieval performance."


def _load() -> dict[str, Any]:
    return json.loads(OUT.with_suffix(".json").read_bytes())


def _save(state: dict[str, Any]) -> None:
    m12d._write(OUT.with_suffix(".json"),state)


def population() -> list[ev.DocumentQuestion]:
    """Reuse M12D's reviewed adapter/projection path and check full frozen records."""
    questions = [q for q in depth._population() if q.id.startswith("k5607-")]
    assert len(questions) == len({q.question for q in questions}) == 30
    if any(q.expected_document_ids != frozenset({DOCUMENT}) for q in questions):
        raise RuntimeError("M12F-C BLOCKED — INCONSISTENT ORACLE DOCUMENT")
    saved = json.loads(G0_PATH.read_bytes())
    assert saved["status"] == "completed"
    by_id = {r["question"]["id"]:r for r in saved["results"]}
    assert all(q.to_dict() == by_id[q.id]["question"] and len(by_id[q.id]["ranks"]) == 50 for q in questions)
    return questions


def enriched_input(title: str, raw: str) -> str:
    """Add only an admitted document title and blank line, preserving raw text."""
    return title + "\n\n" + raw


def oracle_validate(question: dict[str, Any], ranks: list[dict[str, Any]], expected_ids: set[str]) -> None:
    """Require all 46 exact indexed chunks, correct provenance, and all gold keys."""
    if len(ranks) != 46 or {r["chunk_id"] for r in ranks} != expected_ids:
        raise RuntimeError("M12F-C BLOCKED — ORACLE CORPUS SOURCE MISSING")
    if any(r["document_id"] != DOCUMENT for r in ranks):
        raise RuntimeError("M12F-C BLOCKED — ORACLE FILTER ERROR")
    if not depth._keys(question) <= {r["document_source_key"] for r in ranks}:
        raise RuntimeError("M12F-C BLOCKED — ORACLE CORPUS SOURCE MISSING")


def rank_band(rank: int) -> str:
    """Band exhaustive oracle ranks without treating censoring as a numeric rank."""
    if not 1 <= rank <= 46:
        raise ValueError("Oracle rank must be within 1..46")
    for maximum,label in ((1,"1"),(3,"2-3"),(5,"4-5"),(10,"6-10"),(20,"11-20"),(30,"21-30"),(46,"31-46")):
        if rank <= maximum:
            return label
    raise AssertionError("Unreachable")


def delta_summary(deltas: list[int]) -> dict[str, Any]:
    """Summarize O3 minus O1 ranks; negative improves, positive regresses."""
    return dict(count=len(deltas),mean=mean(deltas) if deltas else None,median=median(deltas) if deltas else None,
                improved=sum(d<0 for d in deltas),unchanged=sum(d==0 for d in deltas),regressed=sum(d>0 for d in deltas))


def prepare() -> None:
    """Admit population/title and open only a fresh byte-verified Chroma copy."""
    if OUT.with_suffix(".json").exists():
        raise RuntimeError("Existing diagnostic; refusing replacement")
    git = lambda *a: subprocess.check_output(["git",*a],cwd=ROOT,text=True).strip()
    assert git("rev-parse","HEAD") == git("rev-parse","origin/main") == HEAD
    assert not git("diff","HEAD","--name-only"), "M12F-C BLOCKED — PRECONDITION FAILED"
    questions = population()
    baseline = json.loads(G0_PATH.read_bytes())
    registry = source_registry.load_manifest(ROOT / "data/source_manifest.json",project_root=ROOT)
    record = registry.by_document_id(DOCUMENT)
    assert record.legislation_number == "5607"
    title = embed.build_document_display_title(record.document_id,record.legislation_number)
    assert title == (record.title if "5607" in record.title else f"5607 Sayılı {record.title}")
    production = (ROOT / config.CHROMA_PATH).resolve()
    before = m12d._tree(production)
    copy_path = Path(tempfile.mkdtemp(prefix="m12fc-chroma-copy-")) / "chroma"
    assert production != copy_path.resolve() and production not in copy_path.resolve().parents
    shutil.copytree(production,copy_path)
    copied = m12d._tree(copy_path)
    assert before == copied == m12d._tree(production), "Byte-copy mismatch"
    collection = m12d.chromadb.PersistentClient(path=str(copy_path)).get_collection(config.COLLECTION_NAME,embedding_function=None)
    logical = m12d._logical(collection)
    assert logical["count"] == 375 and logical["distribution"] == m12d.DISTRIBUTION and logical["dimensions"] == [1536]
    assert logical == baseline["chroma"]["logical_before"], "Corpus differs from saved G0 corpus"
    assert retrieve.distance_metric(collection) == "l2" and config.EMBEDDING_MODEL == "text-embedding-3-small"
    data = collection.get(include=["metadatas"])
    catalog = {key:meta for key,meta in zip(data["ids"],data["metadatas"])}
    oracle_ids = {key for key,meta in catalog.items() if meta["document_id"] == DOCUMENT}
    assert len(oracle_ids) == 46
    oracle_keys = {str(source_registry.source_key_from_metadata(catalog[key])) for key in oracle_ids}
    if any(not {str(k) for k in q.expected_sources} <= oracle_keys for q in questions):
        raise RuntimeError("M12F-C BLOCKED — ORACLE CORPUS SOURCE MISSING")
    paths = {ROOT / "app.py",ROOT / "data/source_manifest.json",ROOT / "tests/questions.json",Path(__file__).resolve()}
    for directory,pattern in (("src","*.py"),("evaluation","*"),("reports/evaluation","m12d-*"),("reports/evaluation","m12e-*"),
                              ("reports/evaluation","m12fa-*"),("reports/evaluation","m12fb-*"),("scripts","run_m12d*"),
                              ("scripts","run_m12fa*"),("scripts","run_m12fb*")):
        paths.update(p for p in (ROOT / directory).rglob(pattern) if p.is_file())
    baseline_rows = {r["question"]["id"]:r for r in baseline["results"]}
    state = dict(status="prepared",verdict="M12F-C BLOCKED — DIAGNOSTIC ISSUE",head=HEAD,created_utc=datetime.now(timezone.utc).isoformat(),
                 population=dict(count=30,document=DOCUMENT,loader="scripts.run_m12d_three_source._questions via M12F-B _population",full_records_identical=True,frozen_file_sha256=m12d._hash(m12d.FROZEN)),
                 document_title=title,oracle_document_source="Frozen gold expected_document_ids; not a text detector or proposed router",
                 definitions={"G0":"Saved M12F-B raw original query + global corpus, Top50; NOT rerun", "O1":"Fresh raw query + oracle 5607 document, all 46 chunks", "O2":"Document-title-enriched query + global corpus, Top50", "O3":"Same enriched vector as O2 + oracle 5607 document, all 46 chunks"},
                 configuration=dict(model=config.EMBEDDING_MODEL,dimensions=1536,max_retries=0,rerank=False,deduplicate=False,corpus_reembedding=False),
                 comparison_caveat="G0 uses saved M12F-B raw vectors/rankings; O1 raw vectors are newly embedded as authorized. Possible temporal/numerical query-vector drift is not isolated. O3 versus O1 is same-run; no fresh raw/global control was run.",
                 input_hashes={p.relative_to(ROOT).as_posix():m12d._hash(p) for p in sorted(paths)},
                 chroma=dict(production_path=str(production),copy_path=str(copy_path),production_files_before=before,copy_files_before_open=copied,byte_equal_before_open=True,logical_before=logical),
                 oracle_chunk_ids=sorted(oracle_ids),metadata_catalog=catalog,
                 api=dict(unique_embedding_inputs=0,requests=0,successful_embeddings=0,failures=0,prompt_tokens=0,total_tokens=0,generation_calls=0),
                 query_operations={"G0":0,"O1":0,"O2":0,"O3":0},
                 results=[dict(question=q.to_dict(),inputs=dict(raw=q.question,enriched=enriched_input(title,q.question)),variants={"G0":dict(ranks=copy.deepcopy(baseline_rows[q.id]["ranks"]))}) for q in questions])
    assert len({(config.EMBEDDING_MODEL,text) for r in state["results"] for text in r["inputs"].values()}) == 60
    _save(state)
    print("Prepared 30 questions, 60 query inputs; saved G0 preserved. Copy: 375 records, 53/276/46, 1536 dimensions, L2. Oracle corpus = 46 exact chunk IDs. API calls=0.",flush=True)


def run() -> None:
    """Attempt exactly one query-embedding batch and O1/O2/O3; never query G0."""
    state = _load()
    assert state["status"] == "prepared", "Already attempted; no rerun"
    assert [q.to_dict() for q in population()] == [r["question"] for r in state["results"]]
    assert all(m12d._hash(ROOT/p) == h for p,h in state["input_hashes"].items())
    production,copy_path = (Path(state["chroma"][k]).resolve() for k in ("production_path","copy_path"))
    assert production != copy_path and production not in copy_path.parents
    assert m12d._tree(production) == state["chroma"]["production_files_before"]
    collection = m12d.chromadb.PersistentClient(path=str(copy_path)).get_collection(config.COLLECTION_NAME,embedding_function=None)
    assert m12d._logical(collection) == state["chroma"]["logical_before"] and retrieve.distance_metric(collection) == "l2"
    state["status"] = "running"
    _save(state)
    try:
        model = state["configuration"]["model"]
        with m12d.OpenAI(api_key=config.OPENAI_API_KEY,max_retries=0,timeout=60.0) as client:
            cache = cached_embeddings(client.embeddings,[(model,text) for r in state["results"] for text in r["inputs"].values()],state["api"])
        _save(state)
        assert len(cache) == 60
        for number,row in enumerate(state["results"],1):
            for variant in ("O1","O2","O3"):
                text = row["inputs"]["raw" if variant == "O1" else "enriched"]
                where = None if variant == "O2" else {"document_id":DOCUMENT}
                size = 50 if variant == "O2" else 46
                state["query_operations"][variant] += 1
                chunks = retrieve.retrieve_by_embedding(cache[(model,text)],collection=collection,top_k=size,where=where)
                ranks = []
                for chunk in chunks:
                    rank = ev.DocumentRank.from_retrieved(chunk).to_dict()
                    rank.update(distance=chunk.distance,text_sha256=hashlib.sha256(chunk.text.encode("utf-8")).hexdigest())
                    ranks.append(rank)
                assert len(ranks) == len({r["chunk_id"] for r in ranks}) == size
                if where:
                    oracle_validate(row["question"],ranks,set(state["oracle_chunk_ids"]))
                row["variants"][variant] = dict(ranks=ranks,where=where,query_input_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest())
                _save(state)
            print(f"Saved {row['question']['id']} ({number}/30): O1/O2/O3",flush=True)
        assert state["query_operations"] == {"G0":0,"O1":30,"O2":30,"O3":30}
        state["status"] = "completed"
    except Exception as exc:
        state["status"] = "blocked"
        state["error_type"] = type(exc).__name__
        if isinstance(exc,RuntimeError) and str(exc).startswith("M12F-C BLOCKED"):
            state["verdict"] = str(exc)
        print("STOP: " + state["error_type"],flush=True)
    finally:
        state["chroma"]["production_files_after"] = m12d._tree(production)
        state["chroma"]["production_unchanged"] = state["chroma"]["production_files_after"] == state["chroma"]["production_files_before"]
        state["chroma"]["logical_after"] = m12d._logical(collection)
        state["chroma"]["logical_unchanged"] = state["chroma"]["logical_after"] == state["chroma"]["logical_before"]
        state["inputs_unchanged"] = all(m12d._hash(ROOT/p) == h for p,h in state["input_hashes"].items())
        if not all((state["chroma"]["production_unchanged"],state["chroma"]["logical_unchanged"],state["inputs_unchanged"])):
            state["status"] = "blocked"
        if state["status"] == "completed":
            state["verdict"] = "M12F-C READY FOR REVIEW"
        _save(state)
    if state["status"] != "completed":
        raise SystemExit(1)
    render()


def _paired(rows: list[dict[str, Any]], left: str, right: str) -> dict[str, Any]:
    result = {}
    for metric in ("document_hit","document_all","source_any","source_all"):
        result[metric] = {}
        for k in CUTOFFS:
            groups: dict[str,list[str]] = {name:[] for name in ("improved","unchanged","regressed")}
            for row in rows:
                change = int(row["variants"][right]["metrics"][str(k)][metric])-int(row["variants"][left]["metrics"][str(k)][metric])
                groups["improved" if change>0 else "regressed" if change<0 else "unchanged"].append(row["question"]["id"])
            result[metric][str(k)] = {name:dict(count=len(ids),ids=ids) for name,ids in groups.items()}
    return result


def _classify(row: dict[str, Any]) -> list[dict[str, str]]:
    evidence = []
    for key in depth._keys(row["question"]):
        ranks = {v:row["variants"][v]["first_ranks"]["expected_source_ranks"][key] for v in VARIANTS}
        labels = []
        if ranks["G0"] is None and ranks["O1"] <= 10:
            labels.append("document competition supported: G0 censored, O1 <=10")
        if ranks["O1"] > 10:
            labels.append("within-document provision difficulty: O1 >10")
        if ranks["O2"] is not None and (ranks["G0"] is None or ranks["O2"] < ranks["G0"]):
            labels.append("enriched global source rank improves (historical G0 comparator)")
        if ranks["O3"] < ranks["O1"]:
            labels.append("enrichment improves within-document source rank")
        if ranks["O3"] > ranks["O1"]:
            labels.append("enrichment worsens within-document source rank")
        if ranks["O1"] > 20 and ranks["O3"] > 20:
            labels.append("persistent poor rank under both representations; chunk causality unproven")
        evidence.append(dict(source=key,ranks=str(ranks),observations="; ".join(labels) or "No rule triggered; inspect exact ranks"))
    return evidence


def render() -> None:
    """Analyze saved rankings only; no embedding, Chroma opening, or retrieval."""
    state = _load()
    assert state["status"] == "completed"
    rows = state["results"]
    assert len(rows) == 30
    baseline = {r["question"]["id"]:r for r in json.loads(G0_PATH.read_bytes())["results"]}
    for row in rows:
        assert row["variants"]["G0"]["ranks"] == baseline[row["question"]["id"]]["ranks"]
        for variant,result in row["variants"].items():
            if variant in ("O1","O3"):
                oracle_validate(row["question"],result["ranks"],set(state["oracle_chunk_ids"]))
            result["metrics"] = {str(k):depth.score_prefix(row["question"],result["ranks"],k) for k in CUTOFFS}
            result["first_ranks"] = depth.first_ranks(row["question"],result["ranks"])
            result["gold_distances"] = {}
            for key,rank in result["first_ranks"]["expected_source_ranks"].items():
                top = result["ranks"][0]["distance"]
                distance = result["ranks"][rank-1]["distance"] if rank is not None else None
                result["gold_distances"][key] = dict(rank=rank,top1_distance=top,gold_distance=distance,gold_minus_top1=distance-top if distance is not None else None)
        o1 = row["variants"]["O1"]["first_ranks"]["expected_source_ranks"]
        o3 = row["variants"]["O3"]["first_ranks"]["expected_source_ranks"]
        row["O3_minus_O1"] = {key:o3[key]-o1[key] for key in o1}
        row["decomposition"] = _classify(row)
        if row["question"]["id"] in ("k5607-003","k5607-004"):
            key = DOCUMENT+"/normal/3"
            row["provisions_above_madde_3"] = {}
            for v in ("O1","O3"):
                rank = row["variants"][v]["first_ranks"]["expected_source_ranks"][key]
                row["provisions_above_madde_3"][v] = [dict(**r,article_title=state["metadata_catalog"][r["chunk_id"]].get("article_title")) for r in row["variants"][v]["ranks"][:rank-1]]
    state["saved_rank_counts"] = {v:sum(len(r["variants"][v]["ranks"]) for r in rows) for v in VARIANTS}
    assert state["saved_rank_counts"] == {"G0":1500,"O1":1380,"O2":1500,"O3":1380}
    state["oracle_validation"] = dict(exhaustive_rankings=60,expected_chunks_each=46,missing_gold_sources=0,wrong_document_slots=0)
    state["summaries"] = {v:depth._summary([dict(question=r["question"],metrics=r["variants"][v]["metrics"]) for r in rows]) for v in VARIANTS}
    state["O2_vs_G0"] = _paired(rows,"G0","O2")
    state["O3_vs_O1"] = _paired(rows,"O1","O3")
    deltas = [d for r in rows for d in r["O3_minus_O1"].values()]
    state["rank_delta_summary"] = dict(unit="question-required-source pair (repeated sources across questions remain separate)",per_required_source=delta_summary(deltas),
        first_gold=delta_summary([r["variants"]["O3"]["first_ranks"]["first_expected_source_rank"]-r["variants"]["O1"]["first_ranks"]["first_expected_source_rank"] for r in rows]),
        all_gold=delta_summary([r["variants"]["O3"]["first_ranks"]["all_expected_sources_recovered_by_rank"]-r["variants"]["O1"]["first_ranks"]["all_expected_sources_recovered_by_rank"] for r in rows]))
    state["oracle_rank_distributions"] = {}
    for v in ("O1","O3"):
        state["oracle_rank_distributions"][v] = {}
        for group,items in (("all",rows),("single_source",[r for r in rows if len(depth._keys(r["question"]))==1]),("multi_source",[r for r in rows if len(depth._keys(r["question"]))>1])):
            state["oracle_rank_distributions"][v][group] = {}
            for field in ("first_expected_source_rank","all_expected_sources_recovered_by_rank"):
                state["oracle_rank_distributions"][v][group][field] = {band:[r["question"]["id"] for r in items if rank_band(r["variants"][v]["first_ranks"][field])==band] for band in ("1","2-3","4-5","6-10","11-20","21-30","31-46")}
    state["primary_recovery"] = {v:{str(k):{m:[r["question"]["id"] for r in rows if r["question"]["id"] in PRIMARY and r["variants"][v]["metrics"][str(k)][m]] for m in ("source_any","source_all")} for k in (5,10,20,50)} for v in VARIANTS}
    _save(state)
    _render_files(state)
    print(json.dumps(dict(verdict=state["verdict"],api=state["api"],queries=state["query_operations"],slots=state["saved_rank_counts"],rank_deltas=state["rank_delta_summary"]),ensure_ascii=True),flush=True)


def _render_files(state: dict[str, Any]) -> None:
    rows = state["results"]
    fields = ["id","question","variant","rank","chunk_id","document_source_key","document_id","distance","article_title","expected_sources","first_expected_source_rank","all_expected_sources_recovered_by_rank"]
    with OUT.with_suffix(".csv").open("w",encoding="utf-8-sig",newline="") as handle:
        writer = csv.DictWriter(handle,fieldnames=fields)
        writer.writeheader()
        for row in rows:
            for v,result in row["variants"].items():
                for rank in result["ranks"]:
                    writer.writerow(dict(id=row["question"]["id"],question=row["question"]["question"],variant=v,
                                         **{k:rank[k] for k in ("rank","chunk_id","document_source_key","document_id","distance")},
                                         article_title=state["metadata_catalog"][rank["chunk_id"]].get("article_title"),
                                         expected_sources=" | ".join(sorted(depth._keys(row["question"]))),
                                         first_expected_source_rank=result["first_ranks"]["first_expected_source_rank"],
                                         all_expected_sources_recovered_by_rank=result["first_ranks"]["all_expected_sources_recovered_by_rank"]))
    lines = ["# M12F-C — Oracle Retrieval Decomposition Diagnostic","",state["verdict"],"",NOTICE,
             "The correct document is supplied from frozen gold solely to diagnose failure. It is not information available to the real chatbot and is not a proposed router. No production candidate is selected.",
             "Any future adopted candidate requires a NEW UNSEEN HOLDOUT. No production code, index, corpus embeddings, chunking or frozen datasets changed.","",
             "## Population, variants and accounting","","30 frozen 5607 document-source-v1 records, loaded through the exact reviewed M12D path. Full records match M12D/M12F-B; frozen bytes are fingerprinted. No Article information, answer text or expected-source text is added to queries.",
             "Official manifest display title: " + state["document_title"],state["comparison_caveat"],""]
    lines += [f"- {v}: {definition}" for v,definition in state["definitions"].items()]
    lines += ["","```json",json.dumps(dict(api=state["api"],query_operations=state["query_operations"],saved_rank_counts=state["saved_rank_counts"],oracle_validation=state["oracle_validation"]),indent=2),"```",
              f"Copy byte equality verified before opening; logical corpus {state['chroma']['logical_before']}. Production bytes unchanged: {state['chroma']['production_unchanged']}; copy logical state unchanged: {state['chroma']['logical_unchanged']}; protected inputs unchanged: {state['inputs_unchanged']}.","",
              "## Diagnostic coverage (not production accuracy)","","O1/O3 @50 means all 46 available chunks. Complete coverage there is an exhaustive-corpus sanity check. Rankings are not deduplicated.","",
              "| Variant | Metric | @1 | @3 | @5 | @10 | @20 | @50 |","|---|---|---:|---:|---:|---:|---:|---:|"]
    for v,summary in state["summaries"].items():
        for m in depth.METRICS:
            lines.append(f"| {v} | {m} | " + " | ".join(f"{summary['metrics'][str(k)][m]:.2%}" for k in CUTOFFS) + " |")
    lines += ["","## Every required source: exact ranks and within-document deltas","","Global >50 is censored and never converted into a numeric rank delta. O1/O3 ranks are out of 46. Negative O3-O1 means improvement.","",
              "| ID | Required source | G0 | O1 /46 | O2 | O3 /46 | O3-O1 |","|---|---|---:|---:|---:|---:|---:|"]
    for row in rows:
        for key in sorted(depth._keys(row["question"])):
            values = [row["variants"][v]["first_ranks"]["expected_source_ranks"][key] for v in VARIANTS]
            lines.append(f"| {row['question']['id']} | {key} | " + " | ".join(str(n) if n is not None else ">50" for n in values) + f" | {row['O3_minus_O1'][key]} |")
    lines += ["","## Primary decomposition and distance evidence","","Rules describe overlapping observations: O1 <=10 indicates accessible gold; O1 >10 indicates provision-selection difficulty; both O1/O3 >20 flag persistent poor ranks. These are descriptive thresholds, not causal diagnoses of chunks. Exact ranks and cutoff crossings take precedence over labels.",""]
    for row in rows:
        if row["question"]["id"] not in PRIMARY+CONTROLS:
            continue
        lines += [f"### {row['question']['id']}","",row["question"]["question"],
                  "ALL recovered ranks (G0/O1/O2/O3): " + " / ".join(str(row["variants"][v]["first_ranks"]["all_expected_sources_recovered_by_rank"] or ">50") for v in VARIANTS),
                  "First expected document ranks (G0/O2): " + " / ".join(str(row["variants"][v]["first_ranks"]["first_expected_document_rank"] or ">50") for v in ("G0","O2")),""]
        for finding in row["decomposition"]:
            lines += [finding["source"] + ": " + finding["observations"]]
        if row["question"]["id"] in PRIMARY:
            lines += ["","Within-query distance evidence only; absolute L2 thresholds are not transferable across questions.","```json",json.dumps({v:row["variants"][v]["gold_distances"] for v in ("O1","O3")},indent=2),"```",""]
        if row.get("provisions_above_madde_3"):
            lines += ["| Variant | Rank | Provision above Madde 3 | Article title (if present) | L2 |","|---|---:|---|---|---:|"]
            for v,ranks in row["provisions_above_madde_3"].items():
                if not ranks:
                    lines += [f"| {v} | — | None: Madde 3 is first | — | — |"]
                for r in ranks:
                    lines.append(f"| {v} | {r['rank']} | {r['document_source_key']} | {r['article_title'] or 'not supplied'} | {r['distance']:.9f} |")
            lines += [""]
    lines += ["## O2 versus saved G0: paired coverage changes","","Counts are improved / unchanged / regressed for each question's boolean coverage flag. Full IDs are in JSON. This is a historical-comparator diagnostic, not a same-run production trial.","",
              "| Metric | K | Improved | Unchanged | Regressed |","|---|---:|---:|---:|---:|"]
    for m,cutoffs in state["O2_vs_G0"].items():
        for k,counts in cutoffs.items():
            lines.append(f"| {m} | {k} | {counts['improved']['count']} | {counts['unchanged']['count']} | {counts['regressed']['count']} |")
    lines += ["","## Exhaustive within-document rank distributions","","First gold and ALL gold are separate for multi-source questions; count denominators appear through the ID lists in JSON.","",
              "| Variant | Group | Measure | 1 | 2–3 | 4–5 | 6–10 | 11–20 | 21–30 | 31–46 |","|---|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    for v,groups in state["oracle_rank_distributions"].items():
        for group,measures in groups.items():
            for measure,bands in measures.items():
                lines.append(f"| {v} | {group} | {measure} | " + " | ".join(str(len(ids)) for ids in bands.values()) + " |")
    lines += ["","## O3 minus O1 rank deltas","","Each required source is counted once per question. Repeated sources across different questions are distinct diagnostic instances. No censored global rank enters these calculations.","```json",json.dumps(state["rank_delta_summary"],indent=2),"```","",
              "## Persistent six-question cohort recovery","","Includes 002/003/004/025/026/029; excludes historical-drift 014. Lists show observed cutoff coverage, not deployable performance.","```json",json.dumps(state["primary_recovery"],indent=2),"```",""]
    if state.get("decision_answers"):
        lines += ["## Ten decision questions and single next experiment",""]
        for answer in state["decision_answers"]:
            lines += [answer,""]
    lines += [NOTICE,"A NEW UNSEEN HOLDOUT is mandatory before any future adoption. No oracle filtering, routing, reranking or other candidate is adopted."]
    OUT.with_suffix(".md").write_text("\n".join(line.rstrip() for line in lines).rstrip()+"\n",encoding="utf-8")


def main() -> None:
    """Separate preparation, authorized one-shot run and offline-only rendering."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase",choices=("prepare","run","render"))
    args = parser.parse_args()
    {"prepare":prepare,"run":run,"render":render}[args.phase]()


if __name__ == "__main__":
    main()
