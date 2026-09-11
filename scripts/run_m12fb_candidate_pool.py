"""One-shot Top50 completeness diagnostic on a verified copy; no intervention."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import run_m12d_three_source as m12d
from scripts.run_m12fa_explicit_law import cached_embeddings
from src import config, evaluate_documents as ev, retrieve

ROOT = m12d.ROOT
OUT = ROOT / "reports/evaluation/m12fb-candidate-pool-diagnostic"
HEAD = "ab9969ac7f6cb05e33a25e2e04e9431133073a8f"
CUTOFFS = (1, 3, 5, 10, 20, 50)
METRICS = ("source_any", "source_all", "document_hit", "document_all", "document_intrusion")
MISSES = [f"k5607-{n:03d}" for n in (2, 3, 4, 14, 25, 26)]
PRIMARY = MISSES + ["k5607-029", "gk001"]
CONTROLS = [f"k5607-{n:03d}" for n in (17, 23, 28, 30)]
DISTANCE_ATOL = 1e-7


def _load() -> dict[str, Any]:
    return json.loads(OUT.with_suffix(".json").read_bytes())


def _save(state: dict[str, Any]) -> None:
    m12d._write(OUT.with_suffix(".json"), state)


def _population() -> list[ev.DocumentQuestion]:
    questions = m12d._questions()
    saved = json.loads(m12d.JSON_PATH.read_bytes())
    assert [q.to_dict() for q in questions] == [r["question"] for r in saved["results"]]
    assert len(questions) == len({q.question for q in questions}) == 105
    return questions


def _keys(question: dict[str, Any]) -> set[str]:
    return {str(ev.source_identity.DocumentSourceKey.from_dict(k)) for k in question["expected_sources"]}


def score_prefix(question: dict[str, Any], ranks: list[dict[str, Any]], k: int) -> dict[str, Any]:
    """Mirror reviewed set-coverage/slot-intrusion definitions at any cutoff."""
    top = ranks[:k]
    gold, expected_docs = _keys(question), set(question["expected_document_ids"])
    sources = {r["document_source_key"] for r in top}
    documents = {r["document_id"] for r in top}
    return dict(k=k, source_any=bool(gold & sources), source_all=gold <= sources,
                document_hit=bool(expected_docs & documents), document_all=expected_docs <= documents,
                document_intrusion=sum(r["document_id"] not in expected_docs for r in top)/len(top) if top else None,
                retrieved_slots=len(top))


def first_ranks(question: dict[str, Any], ranks: list[dict[str, Any]]) -> dict[str, Any]:
    """Retain null for censored gold; report each required canonical provision."""
    gold = _keys(question)
    per_source = {key:next((r["rank"] for r in ranks if r["document_source_key"] == key), None) for key in sorted(gold)}
    found = [rank for rank in per_source.values() if rank is not None]
    return dict(first_expected_document_rank=next((r["rank"] for r in ranks if r["document_id"] in question["expected_document_ids"]), None),
                first_expected_source_rank=min(found) if found else None,
                all_expected_sources_recovered_by_rank=max(found) if len(found) == len(gold) else None,
                expected_source_ranks=per_source)


def recovery_band(rank: int | None) -> str:
    """Classify a censored first/all-gold rank, retaining already-recovered cases."""
    if rank is None:
        return ">50"
    if rank <= 5:
        return "1-5"
    if rank <= 10:
        return "6-10"
    if rank <= 20:
        return "11-20"
    return "21-50"


def duplicate_slots(ranks: list[dict[str, Any]], k: int) -> dict[str, Any]:
    """Count repeated provision slots without changing ranking or global grouping."""
    counts = Counter(r["document_source_key"] for r in ranks[:k])
    repeated = {key:n-1 for key,n in counts.items() if n > 1}
    by_document: Counter[str] = Counter()
    for key,n in repeated.items():
        by_document[key.split("/")[0]] += n
    return dict(total_slots=len(ranks[:k]), distinct_sources=len(counts), repeated_slots=sum(repeated.values()),
                repeated_sources=repeated, repeated_by_document=dict(by_document))


def drift_check(row: dict[str, Any], old: dict[str, Any]) -> dict[str, Any]:
    """Compare Top5 identity, coverage and distances with explicit strict tolerance."""
    fresh = row["ranks"][:5]
    old_by_id = {r["chunk_id"]:r for r in old["ranks"]}
    common = [r for r in fresh if r["chunk_id"] in old_by_id]
    return dict(top5_chunk_ids_equal=[r["chunk_id"] for r in fresh] == [r["chunk_id"] for r in old["ranks"]],
                metrics_equal=all(row["metrics"][str(k)] == old["metrics"][str(k)] for k in (1,3,5)),
                slot_distances_equal=all(math.isclose(r["distance"],o["distance"],rel_tol=0,abs_tol=DISTANCE_ATOL) for r,o in zip(fresh,old["ranks"])),
                common_chunk_count=len(common), common_chunk_distances_equal=all(math.isclose(r["distance"],old_by_id[r["chunk_id"]]["distance"],rel_tol=0,abs_tol=DISTANCE_ATOL) for r in common),
                max_common_chunk_distance_delta=max((abs(r["distance"]-old_by_id[r["chunk_id"]]["distance"]) for r in common),default=None),
                old_top5=old["ranks"], old_metrics=old["metrics"], absolute_tolerance=DISTANCE_ATOL, relative_tolerance=0)


def prepare() -> None:
    """Verify exact population and immutable inputs, then open a byte-verified copy."""
    if OUT.with_suffix(".json").exists():
        raise RuntimeError("Existing diagnostic; no replacement preparation")
    git = lambda *args: subprocess.check_output(["git",*args],cwd=ROOT,text=True).strip()
    assert git("rev-parse","HEAD") == git("rev-parse","origin/main") == HEAD
    assert not git("diff","HEAD","--name-only"), "Tracked precondition failed"
    questions = _population()
    production = (ROOT / config.CHROMA_PATH).resolve()
    before = m12d._tree(production)
    copy = Path(tempfile.mkdtemp(prefix="m12fb-chroma-copy-")) / "chroma"
    assert production != copy.resolve() and production not in copy.resolve().parents
    shutil.copytree(production,copy)
    copied = m12d._tree(copy)
    assert before == copied == m12d._tree(production), "STOP: byte-copy mismatch"
    collection = m12d.chromadb.PersistentClient(path=str(copy)).get_collection(config.COLLECTION_NAME,embedding_function=None)
    logical = m12d._logical(collection)
    assert logical["count"] == 375 and logical["distribution"] == m12d.DISTRIBUTION
    assert logical["dimensions"] == [1536] and retrieve.distance_metric(collection) == "l2"
    assert config.EMBEDDING_MODEL == "text-embedding-3-small"
    paths = {ROOT / "data/source_manifest.json", ROOT / "app.py", ROOT / "tests/questions.json",
             ROOT / "scripts/run_m12d_three_source.py", ROOT / "scripts/run_m12fa_explicit_law.py",
             Path(__file__).resolve()}
    for directory, pattern in (("src","*.py"),("evaluation","*.json"),("reports/evaluation","m12d-*"),
                               ("reports/evaluation","m12e-*"),("reports/evaluation","m12fa-*"),
                               ("reports/evaluation","m10d-*")):
        paths.update((ROOT / directory).rglob(pattern))
    state = dict(status="prepared",verdict="M12F-B BLOCKED — DIAGNOSTIC ISSUE",head=HEAD,
                 created_utc=datetime.now(timezone.utc).isoformat(),
                 population=dict(loader="scripts.run_m12d_three_source._questions", total=105,
                                 composition={"5326":45,"4458":30,"5607":30}, full_records_equal=True, unique_raw_texts=105),
                 input_hashes={p.relative_to(ROOT).as_posix():m12d._hash(p) for p in sorted(paths) if p.is_file()},
                 configuration=dict(model=config.EMBEDDING_MODEL,dimensions=1536,query="raw original question exactly",n_results=50,
                                    cutoffs=list(CUTOFFS),filter=None,rerank=False,deduplicate=False,enrichment=False,max_retries=0,distance="l2"),
                 chroma=dict(production_path=str(production),copy_path=str(copy),production_files_before=before,
                             copy_files_before_open=copied,byte_equal_before_open=True,logical_before=logical),
                 api=dict(unique_embedding_inputs=0,requests=0,successful_embeddings=0,failures=0,prompt_tokens=0,total_tokens=0,generation_calls=0),
                 chroma_query_operations=0,results=[])
    _save(state)
    print("Prepared: 105 unique raw queries; copy byte equality PASS; 375 records, 53/276/46, 1536 dimensions, L2. API requests=0.",flush=True)


def run() -> None:
    """Attempt one embedding batch and one unfiltered K=50 query per raw vector."""
    state = _load()
    assert state["status"] == "prepared", "Already attempted; do not rerun"
    questions = _population()
    assert all(m12d._hash(ROOT/p) == h for p,h in state["input_hashes"].items())
    production,copy = (Path(state["chroma"][k]).resolve() for k in ("production_path","copy_path"))
    assert production != copy and production not in copy.parents
    assert m12d._tree(production) == state["chroma"]["production_files_before"]
    collection = m12d.chromadb.PersistentClient(path=str(copy)).get_collection(config.COLLECTION_NAME,embedding_function=None)
    assert m12d._logical(collection) == state["chroma"]["logical_before"]
    assert retrieve.distance_metric(collection) == "l2"
    state["status"] = "running"
    _save(state)
    try:
        model = state["configuration"]["model"]
        with m12d.OpenAI(api_key=config.OPENAI_API_KEY,max_retries=0,timeout=60.0) as client:
            vectors = cached_embeddings(client.embeddings,[(model,q.question) for q in questions],state["api"])
        _save(state)
        assert len(vectors) == 105
        for q in questions:
            state["chroma_query_operations"] += 1
            chunks = retrieve.retrieve_by_embedding(vectors[(model,q.question)],collection=collection,top_k=50,where=None)
            assert len(chunks) == len({c.chunk_id for c in chunks}) == 50
            ranks = []
            for c in chunks:
                r = ev.DocumentRank.from_retrieved(c).to_dict()
                r.update(distance=c.distance,text_sha256=hashlib.sha256(c.text.encode("utf-8")).hexdigest())
                ranks.append(r)
            row = dict(question=q.to_dict(),ranks=ranks,query_input_sha256=hashlib.sha256(q.question.encode("utf-8")).hexdigest())
            row["metrics"] = {str(k):score_prefix(row["question"],ranks,k) for k in CUTOFFS}
            # Independently match the accepted evaluator at its supported cutoffs.
            checked = ev.evaluate_retrieved(q,chunks).to_dict()["metrics"]
            assert all(row["metrics"][k] == checked[k] for k in ("1","3","5"))
            state["results"].append(row)
            _save(state)
            if len(state["results"]) % 15 == 0:
                print(f"Saved {len(state['results'])}/105 Top50 rankings",flush=True)
        assert state["chroma_query_operations"] == 105
        state["status"] = "completed"
    except Exception as exc:
        state["status"] = "blocked"
        state["error_type"] = type(exc).__name__
        print("STOP: " + type(exc).__name__,flush=True)
    finally:
        state["chroma"]["production_files_after"] = m12d._tree(production)
        state["chroma"]["production_unchanged"] = state["chroma"]["production_files_after"] == state["chroma"]["production_files_before"]
        state["chroma"]["logical_after"] = m12d._logical(collection)
        state["chroma"]["logical_unchanged"] = state["chroma"]["logical_after"] == state["chroma"]["logical_before"]
        state["inputs_unchanged"] = all(m12d._hash(ROOT/p) == h for p,h in state["input_hashes"].items())
        if not all((state["chroma"]["production_unchanged"],state["chroma"]["logical_unchanged"],state["inputs_unchanged"])):
            state["status"] = "blocked"
        if state["status"] == "completed":
            state["verdict"] = "M12F-B READY FOR REVIEW"
        _save(state)
        if state["status"] == "completed":
            render()
    if state["status"] != "completed":
        raise SystemExit(1)


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return dict(count=len(rows),ids=[r["question"]["id"] for r in rows],
                metrics={str(k):{m:sum(r["metrics"][str(k)][m] for r in rows)/len(rows) if rows else None for m in METRICS} for k in CUTOFFS})


def _bands(rows: list[dict[str, Any]], field: str) -> dict[str, list[str]]:
    return {band:[r["question"]["id"] for r in rows if recovery_band(r["first_ranks"][field]) == band] for band in ("1-5","6-10","11-20","21-50",">50")}


def _recovery(rows: list[dict[str, Any]], field: str) -> dict[str, Any]:
    return dict(total=len(rows),by_cutoff={str(k):sum(r["first_ranks"][field] is not None and r["first_ranks"][field] <= k for r in rows) for k in (5,10,20,50)},
                absent_or_incomplete_50=sum(r["first_ranks"][field] is None for r in rows),bands=_bands(rows,field))


def _duplicate_summary(rows: list[dict[str, Any]], k: int) -> dict[str, Any]:
    parts = [duplicate_slots(r["ranks"],k) for r in rows]
    dist: Counter[str] = Counter()
    for part in parts:
        dist.update(part["repeated_by_document"])
    return dict(total_slots=sum(p["total_slots"] for p in parts),distinct_sources_sum_per_question=sum(p["distinct_sources"] for p in parts),
                repeated_slots=sum(p["repeated_slots"] for p in parts),questions_with_repeats=sum(p["repeated_slots"] > 0 for p in parts),
                repeated_slots_by_document=dict(dist),question_ids=[r["question"]["id"] for r,p in zip(rows,parts) if p["repeated_slots"]])


def render() -> None:
    """Derive all diagnostics solely from saved rankings; no clients or queries."""
    state = _load()
    assert state["status"] == "completed"
    rows = state["results"]
    assert len(rows) == 105 and sum(len(r["ranks"]) for r in rows) == 5250
    old = {r["question"]["id"]:r for r in json.loads(m12d.JSON_PATH.read_bytes())["results"]}
    for row in rows:
        assert row["question"] == old[row["question"]["id"]]["question"]
        assert row["metrics"] == {str(k):score_prefix(row["question"],row["ranks"],k) for k in CUTOFFS}
        row["first_ranks"] = first_ranks(row["question"],row["ranks"])
        row["drift"] = drift_check(row,old[row["question"]["id"]])
        first = row["first_ranks"]["first_expected_source_rank"]
        top1 = row["ranks"][0]["distance"]
        gold_distance = row["ranks"][first-1]["distance"] if first is not None else None
        row["distance_gaps"] = dict(top1_distance=top1,first_gold_distance=gold_distance,gold_minus_top1=gold_distance-top1 if gold_distance is not None else None,
                                    cutoff_distances={str(k):row["ranks"][k-1]["distance"] for k in (5,10,20,50)})
        row["duplicates"] = {str(k):duplicate_slots(row["ranks"],k) for k in (5,10,20,50)}
        row["repeats_before_gold"] = {key:dict(gold_rank=rank,censored=rank is None,**duplicate_slots(row["ranks"],rank-1 if rank is not None else 50)) for key,rank in row["first_ranks"]["expected_source_ranks"].items()}
        doc_rank = row["first_ranks"]["first_expected_document_rank"]
        row["document_article_observation"] = (
            "Expected document absent Top50; strong observed document-discrimination failure" if doc_rank is None else
            "Expected document first appears below Top5; document competition observed, provision selection may also contribute" if doc_rank > 5 else
            "Expected document present in Top5 but gold incomplete; within-document provision selection observed" if not row["metrics"]["5"]["source_all"] else
            "Gold complete in fresh Top5; historical failure, if any, is drift, not deeper-pool recovery")
    state["summaries"] = {}
    for name,group in [(law,[r for r in rows if doc in r["question"]["expected_document_ids"]]) for law,doc in m12d.DOCS.items()] + [("combined",rows)]:
        state["summaries"][name] = {"overall":_summary(group),"single_source":_summary([r for r in group if len(_keys(r["question"])) == 1]),"multi_source":_summary([r for r in group if len(_keys(r["question"])) > 1])}
    state["drift_summary"] = {name:[r["question"]["id"] for r in rows if not r["drift"][name]] for name in ("top5_chunk_ids_equal","metrics_equal","slot_distances_equal","common_chunk_distances_equal")}
    state["first_rank_bands"] = {field:_bands(rows,field) for field in ("first_expected_document_rank","first_expected_source_rank","all_expected_sources_recovered_by_rank")}
    state["fresh_top5_failures"] = dict(
        source_all=_recovery([r for r in rows if not r["metrics"]["5"]["source_all"]],"all_expected_sources_recovered_by_rank"),
        source_any=_recovery([r for r in rows if not r["metrics"]["5"]["source_any"]],"first_expected_source_rank"),
        multi_source_all=_recovery([r for r in rows if len(_keys(r["question"])) > 1 and not r["metrics"]["5"]["source_all"]],"all_expected_sources_recovered_by_rank"))
    state["accepted_5607_failure_recovery"] = dict(
        six_complete_misses_any=_recovery([r for r in rows if r["question"]["id"] in MISSES],"first_expected_source_rank"),
        seven_all_failures=_recovery([r for r in rows if r["question"]["id"] in MISSES+["k5607-029"]],"all_expected_sources_recovered_by_rank"))
    state["duplicate_summary"] = {str(k):_duplicate_summary(rows,k) for k in (5,10,20,50)}
    breadth = []
    for row in rows:
        if m12d.DOCS["5607"] not in row["question"]["expected_document_ids"]:
            continue
        entry = dict(id=row["question"]["id"],fresh_source_all_5=row["metrics"]["5"]["source_all"],articles={})
        for no in ("3","23"):
            key = m12d.DOCS["5607"] + "/normal/" + no
            occurrences = [dict(rank=r["rank"],chunk_id=r["chunk_id"]) for r in row["ranks"] if r["document_source_key"] == key]
            entry["articles"][no] = dict(occurrences=occurrences,before_each_gold={gold:dict(ranks=[r["rank"] for r in occurrences if rank is None or r["rank"] < rank],gold_rank=rank,censored=rank is None) for gold,rank in row["first_ranks"]["expected_source_ranks"].items()})
        breadth.append(entry)
    state["madde_3_23"] = breadth
    state["breadth_association"] = {}
    for no in ("3","23"):
        state["breadth_association"][no] = {}
        for label,success in (("fresh_all5_success",True),("fresh_all5_failure",False)):
            group = [b for b in breadth if b["fresh_source_all_5"] == success]
            state["breadth_association"][no][label] = dict(count=len(group),two_or_more_before_any_required_gold_ids=[b["id"] for b in group if any(len(v["ranks"]) > 1 for v in b["articles"][no]["before_each_gold"].values())])
    historical = json.loads((ROOT / "reports/evaluation/m10d-two-law-retrieval.json").read_bytes())
    gk = next(r for r in rows if r["question"]["id"] == "gk001")
    state["gk001"] = dict(m10d=next(r for r in historical["results"] if r["id"] == "gk001"),m12d=old["gk001"],fresh_top50=gk["ranks"],first_ranks=gk["first_ranks"],
                          interpretation="Historical cause remains unresolved. Fresh-versus-old changes are not a candidate improvement; no causal attribution to 5607.")
    _save(state)
    _render_files(state)
    print(json.dumps(dict(verdict=state["verdict"],api=state["api"] ,queries=state["chroma_query_operations"],slots=5250,critical=state["accepted_5607_failure_recovery"]),ensure_ascii=True),flush=True)


def _render_files(state: dict[str, Any]) -> None:
    rows = state["results"]
    fields = ["id","question","expected_sources","rank","chunk_id","document_source_key","document_id","distance","first_expected_document_rank","first_expected_source_rank","all_expected_sources_recovered_by_rank"]
    fields += [f"{metric}@{k}" for metric in METRICS for k in CUTOFFS]
    with OUT.with_suffix(".csv").open("w",encoding="utf-8-sig",newline="") as handle:
        writer = csv.DictWriter(handle,fieldnames=fields)
        writer.writeheader()
        for row in rows:
            base = dict(id=row["question"]["id"],question=row["question"]["question"],expected_sources=" | ".join(sorted(_keys(row["question"]))))
            base.update({k:v for k,v in row["first_ranks"].items() if k in fields})
            base.update({f"{m}@{k}":row["metrics"][str(k)][m] for m in METRICS for k in CUTOFFS})
            for rank in row["ranks"]:
                writer.writerow({**base,**{k:v for k,v in rank.items() if k in fields}})
    lines = ["# M12F-B — Candidate Pool Completeness Diagnostic","",state["verdict"],"",
             "Diagnostic only: no candidate, reranking, deduplication, hybrid retrieval, enrichment, filter, routing, chunking change or corpus re-embedding. No production adoption. All cutoffs are prefixes of ONE native L2 Top50 query per question.",
             "Exact M12D loader and reviewed legacy adapter reused: 45 historical 5326, 30 historical 4458, 30 document-source-v1 5607; 105/105 full question records identical. Embeddings use raw original question bytes, text-embedding-3-small, 1536 dimensions, max_retries=0.","",
             "## Run accounting and immutability","","```json",json.dumps(state["api"],indent=2),"```",
             f"Chroma query operations: {state['chroma_query_operations']}; saved ranked slots: {sum(len(r['ranks']) for r in rows)}.",
             f"Byte-verified copy logical state: {state['chroma']['logical_before']}. Production unchanged: {state['chroma']['production_unchanged']}; copied logical state unchanged: {state['chroma']['logical_unchanged']}; frozen datasets, production code and M12D/M12E/M12F-A artifact hashes unchanged: {state['inputs_unchanged']}.",
             "Full file manifests and logical fingerprints are saved in JSON; only the temporary copy was opened.","",
             "## Fresh Top5 versus accepted M12D","",f"Distance tolerance: absolute {DISTANCE_ATOL}, relative 0. Slotwise distances and common-chunk distances are reported separately; missing common chunks are not assigned zero difference.",
             "Fresh-versus-old drift is NOT candidate improvement. The fresh Top50 prefix can differ from historical K=5 retrieval due to query-vector changes or ANN behavior; this run cannot isolate those causes.","",
             "| Comparison | Mismatch count | IDs |","|---|---:|---|"]
    for name,ids in state["drift_summary"].items():
        lines.append(f"| {name} | {len(ids)} | {', '.join(ids) or 'None'} |")
    lines += ["","## Coverage metrics","","Document ALL means all expected documents appear, not that every slot is from the correct document. Intrusion is mean wrong-document slot fraction. No ranking is deduplicated. Single/multi-source groups are shown separately; empty groups are N/A.","",
              "| Dataset | Group (n) | Metric | @1 | @3 | @5 | @10 | @20 | @50 |","|---|---|---|---:|---:|---:|---:|---:|---:|"]
    for dataset,groups in state["summaries"].items():
        for name,group in groups.items():
            for metric in METRICS:
                values = [group["metrics"][str(k)][metric] for k in CUTOFFS]
                lines.append(f"| {dataset} | {name} ({group['count']}) | {metric} | " + " | ".join(f"{v:.2%}" if v is not None else "N/A" for v in values) + " |")
    lines += ["","## Critical accepted 5607 failure cohorts","","These are fixed accepted M12D cohorts. Fresh @5 recovery, if present, is drift and is shown separately from deeper recovery.","","```json",json.dumps(state["accepted_5607_failure_recovery"],indent=2),"```","",
              "## Fresh failure recovery bands","","ALL@5 failure bands: A=6–10, B=11–20, C=21–50, D=>50/incomplete. ANY@5 complete misses use first expected source. Null is censored beyond Top50, not absent from the corpus.","","```json",json.dumps(state["fresh_top5_failures"],indent=2),"```","",
              "## First-correct-rank distribution","","```json",json.dumps(state["first_rank_bands"],indent=2),"```","",
              "## Primary failures and successful controls","","Statuses below are Source ANY / ALL. Per-source ranks are exact canonical DocumentSourceKeys; >50 means not found within saved Top50.","",
              "| ID | First expected document | Each required source: rank | ALL recovered rank | @5 ANY/ALL | @10 | @20 | @50 |","|---|---:|---|---:|---|---|---|---|"]
    for row in rows:
        if row["question"]["id"] not in PRIMARY+CONTROLS:
            continue
        f = row["first_ranks"]
        status = [f"{int(row['metrics'][str(k)]['source_any'])}/{int(row['metrics'][str(k)]['source_all'])}" for k in (5,10,20,50)]
        labels = "; ".join(key+": "+str(rank if rank is not None else ">50") for key,rank in f["expected_source_ranks"].items())
        lines.append(f"| {row['question']['id']} | {f['first_expected_document_rank'] or '>50'} | {labels} | {f['all_expected_sources_recovered_by_rank'] or '>50'} | " + " | ".join(status) + " |")
    for row in rows:
        if row["question"]["id"] in PRIMARY:
            lines += ["",f"### {row['question']['id']}","",row["question"]["question"],row["document_article_observation"],
                      "Distance gaps (within-query descriptive evidence; no global L2 correctness threshold):", "```json",json.dumps(row["distance_gaps"],indent=2),"```",
                      "Repeated slots before each required source (censored rows count through Top50):","```json",json.dumps(row["repeats_before_gold"],indent=2),"```"]
    lines += ["","## Duplicate-source capacity","","Distinct counts are summed per query, not deduplicated globally. Repeated slots = slots minus distinct canonical provisions. This measures occupied capacity, not counterfactual gold recovery.","",
              "| K | Total slots | Distinct sources summed | Repeated slots | Questions with repeats | Repeated slots by document |","|---|---:|---:|---:|---:|---|"]
    for k,d in state["duplicate_summary"].items():
        lines.append(f"| {k} | {d['total_slots']} | {d['distinct_sources_sum_per_question']} | {d['repeated_slots']} | {d['questions_with_repeats']} | {d['repeated_slots_by_document']} |")
    lines += ["","## Madde 3 / Madde 23 across all 30 5607 questions","","Accepted corpus has 3 chunks for 5607 Madde 3 and 2 for Madde 23. These are their observed Top50 ranks; missing chunks are censored. JSON records chunk IDs and ranks before EACH required gold source, including censored cases.","",
              "| ID | Madde 3 ranks | Madde 23 ranks | More than one before a required gold source (Article: source) |","|---|---|---|---|"]
    for b in state["madde_3_23"]:
        multi = [no+": "+key for no,a in b["articles"].items() for key,v in a["before_each_gold"].items() if len(v["ranks"]) > 1]
        lines.append(f"| {b['id']} | {[r['rank'] for r in b['articles']['3']['occurrences']]} | {[r['rank'] for r in b['articles']['23']['occurrences']]} | {'; '.join(multi) or 'None'} |")
    lines += ["","Association by fresh ALL@5 outcome; counts are descriptive and confounded by query topic and gold breadth. Censored gold cases count observed chunks before the Top50 boundary, not a known gold rank.","```json",json.dumps(state["breadth_association"],indent=2),"```","",
              "## gk001 historical and fresh completeness","",state["gk001"]["interpretation"],"",
              "| Snapshot | Rank | Chunk | DocumentSourceKey / historical Article | Distance |","|---|---:|---|---|---:|"]
    g = state["gk001"]
    for label,ranks in (("M10D",g["m10d"]["ranks"]),("M12D",g["m12d"]["ranks"]),("Fresh Top50",g["fresh_top50"])):
        for r in ranks:
            lines.append(f"| {label} | {r['rank']} | {r['chunk_id']} | {r.get('document_source_key',r.get('source_key',''))} | {r.get('distance')} |")
    lines += ["", "Fresh expected-source ranks: " + json.dumps(g["first_ranks"]),
              "If Madde 210 is absent Top50, larger-K through 50 did not recover it and cannot explain the historical omission. If present, the exact observed rank above establishes accessibility in this run only.","",
              "## Decision boundary","","No oracle reranker or candidate performance is calculated. Presence by a deeper cutoff establishes only access to gold for a future scorer, not its ability to select it. The review conclusion must distinguish accepted-cohort recovery, fresh failure bands and historical drift.",
              "Any future candidate informed by this diagnostic requires a NEW UNSEEN HOLDOUT before adoption. No production candidate is selected; no commit or adoption.",""]
    if state.get("review_conclusion"):
        lines += ["## Observed conclusion and next experiment","",state["review_conclusion"]["category"],state["review_conclusion"]["evidence"],state["review_conclusion"]["next_experiment"],""]
    OUT.with_suffix(".md").write_text("\n".join(line.rstrip() for line in lines).rstrip()+"\n",encoding="utf-8")


def main() -> None:
    """Separate copy preparation, one-shot real diagnostic, and offline rendering."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase",choices=("prepare","run","render"))
    args = parser.parse_args()
    {"prepare":prepare,"run":run,"render":render}[args.phase]()


if __name__ == "__main__":
    main()
