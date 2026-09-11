"""Development-only explicit-law experiment; copy-only, one-shot query embeddings."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
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
from src import config, embed, evaluate_documents as ev, retrieve, source_registry

ROOT = m12d.ROOT
OUT = ROOT / "reports/evaluation/m12fa-explicit-law-experiment"
HEAD = "96a352b10eb049c9d8d6351df54c78786de69fc1"
LAW_PATTERN = re.compile(r"(?<!\w)(5326|4458|5607)(?!\w)")
VARIANTS = ("B0", "A1", "A2", "A3")
METRICS = ("source_any", "source_all", "document_hit", "document_all", "document_intrusion")
MISSES = [f"k5607-{n:03d}" for n in (2, 3, 4, 14, 25, 26)]
WRONG_TOP1 = ["q028", "gk020", "gk028"] + [f"k5607-{n:03d}" for n in (2, 3, 4, 9, 14, 25, 26)]
NOTICE = "The intervention was designed after inspecting M12D/M12E development failures. Its scores are development evidence only."


def detect_laws(question: str) -> tuple[str, ...]:
    """Read literal standalone supported numbers only; repeated mentions count once."""
    return tuple(sorted(set(LAW_PATTERN.findall(question))))


def document_filter(law: str) -> dict[str, str]:
    """Map an explicit supported law to an exact Chroma equality filter."""
    return {"document_id": m12d.DOCS[law]}


def _load() -> dict[str, Any]:
    return json.loads(OUT.with_suffix(".json").read_bytes())


def _save(state: dict[str, Any]) -> None:
    m12d._write(OUT.with_suffix(".json"), state)


def detector_audit() -> tuple[list[ev.DocumentQuestion], dict[str, Any]]:
    """Reuse M12D's exact adapter path; gold is checked only after text detection."""
    questions = m12d._questions()
    saved = json.loads(m12d.JSON_PATH.read_bytes())
    if [q.to_dict() for q in questions] != [r["question"] for r in saved["results"]]:
        raise RuntimeError("M12F-A BLOCKED — DATASET / DETECTOR INCONSISTENCY")
    rows = []
    for q in questions:
        laws = detect_laws(q.question)
        rows.append(dict(id=q.id, question=q.question, detected_laws=list(laws),
                         classification="A" if len(laws) == 1 else "B" if laws else "C"))
        if any(m12d.DOCS[law] not in q.expected_document_ids for law in laws):
            raise RuntimeError("M12F-A BLOCKED — DATASET / DETECTOR INCONSISTENCY")
    eligible = [q for q in questions if len(detect_laws(q.question)) == 1]
    ids = {q.id for q in eligible}
    counts = Counter(detect_laws(q.question)[0] for q in eligible)
    audit = dict(total=105, composition={"5326":45,"4458":30,"5607":30},
                 loader="scripts.run_m12d_three_source._questions (unchanged)",
                 population_records_identical=True, eligible_count=len(eligible),
                 breakdown={law:counts[law] for law in m12d.DOCS},
                 ambiguous_count=sum(r["classification"] == "B" for r in rows),
                 no_explicit_count=sum(r["classification"] == "C" for r in rows),
                 eligible_ids=[q.id for q in eligible], eligible_fraction=len(eligible)/105,
                 gold_contradictions=0, false_activations=0,
                 false_activation_basis="All matched spans are standalone law numbers in literal questions; frozen gold agrees. No gold used to activate detector.",
                 complete_miss_eligible=[i for i in MISSES if i in ids],
                 wrong_top1_eligible=[i for i in WRONG_TOP1 if i in ids],
                 untouched_complete_misses=[i for i in MISSES if i not in ids],
                 untouched_wrong_top1=[i for i in WRONG_TOP1 if i not in ids],
                 scope_ceiling="Eligibility only; not a claim that eligible failures will be fixed.", rows=rows)
    assert set(saved["wrong_document_top1_ids"]) == set(WRONG_TOP1)
    print(json.dumps({k:v for k,v in audit.items() if k != "rows"}, ensure_ascii=True), flush=True)
    return eligible, audit


def prepare() -> None:
    """Audit offline, hash production bytes, verify a fresh copy, then open only it."""
    if OUT.with_suffix(".json").exists():
        raise RuntimeError("Existing experiment; refusing replacement")
    git = lambda *args: subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()
    if git("rev-parse", "HEAD") != HEAD or git("rev-parse", "origin/main") != HEAD or git("diff", "HEAD", "--name-only"):
        raise RuntimeError("M12F-A BLOCKED — M12E PRECONDITION FAILED")
    eligible, audit = detector_audit()
    registry = source_registry.load_manifest(ROOT / "data/source_manifest.json", project_root=ROOT)
    titles = {}
    for law, doc in m12d.DOCS.items():
        record = registry.by_document_id(doc)
        assert record.legislation_number == law
        titles[law] = embed.build_document_display_title(record.document_id, record.legislation_number)
        assert titles[law] == (record.title if law in record.title else f"{law} Sayılı {record.title}")
    production = (ROOT / config.CHROMA_PATH).resolve()
    before = m12d._tree(production)
    copy = Path(tempfile.mkdtemp(prefix="m12fa-chroma-copy-")) / "chroma"
    assert production != copy.resolve() and production not in copy.resolve().parents
    shutil.copytree(production, copy)
    copied = m12d._tree(copy)
    assert before == copied == m12d._tree(production), "Copy byte mismatch"
    collection = m12d.chromadb.PersistentClient(path=str(copy)).get_collection(config.COLLECTION_NAME, embedding_function=None)
    logical = m12d._logical(collection)
    assert logical["count"] == 375 and logical["distribution"] == m12d.DISTRIBUTION
    assert logical["dimensions"] == [1536] and retrieve.distance_metric(collection) == "l2"
    assert config.TOP_K == 5 and config.EMBEDDING_MODEL == "text-embedding-3-small"
    paths = [*m12d.HISTORICAL, str(m12d.FROZEN.relative_to(ROOT)), "data/source_manifest.json",
             "reports/evaluation/m12d-three-source-retrieval.json", "scripts/run_m12d_three_source.py",
             "scripts/run_m12fa_explicit_law.py", "app.py"]
    paths += [p.relative_to(ROOT).as_posix() for p in (ROOT / "src").rglob("*.py")]
    state = dict(status="prepared", verdict="M12F-A BLOCKED — EXPERIMENT ISSUE", head=HEAD,
                 created_utc=datetime.now(timezone.utc).isoformat(), detector=audit, titles=titles,
                 input_hashes={p:m12d._hash(ROOT / p) for p in paths},
                 baseline_m12d_105=json.loads(m12d.JSON_PATH.read_bytes())["summary"],
                 configuration=dict(model=config.EMBEDDING_MODEL, dimensions=1536, top_k=5, distance="l2", max_retries=0,
                                    candidates={"B0":"raw, no filter", "A1":"title + blank line + raw, no filter", "A2":"B0 vector, detected document filter", "A3":"A1 vector, detected document filter"}),
                 chroma=dict(production_path=str(production), copy_path=str(copy), production_files_before=before,
                             copy_files_before_open=copied, byte_equal_before_open=True, logical_before=logical),
                 api=dict(eligible_questions=len(eligible), unique_embedding_inputs=0, requests=0, successful_embeddings=0,
                          failures=0, prompt_tokens=0, total_tokens=0, generation_calls=0), results=[])
    _save(state)
    print("Verified copy: 375 records; 53/276/46; 1536 dimensions; L2. No API calls yet.")


def cached_embeddings(endpoint: Any, pairs: list[tuple[str, str]], accounting: dict[str, Any]) -> dict[tuple[str, str], list[float]]:
    """Embed each exact (model, input) once per run; one batch per model, no retries."""
    unique = list(dict.fromkeys(pairs))
    accounting["unique_embedding_inputs"] = len(unique)
    cache = {}
    for model in dict.fromkeys(model for model, _ in unique):
        keys = [key for key in unique if key[0] == model]
        accounting["requests"] += 1
        try:
            response = endpoint.create(model=model, input=[text for _, text in keys], dimensions=1536, encoding_format="float")
            accounting["prompt_tokens"] += response.usage.prompt_tokens
            accounting["total_tokens"] += response.usage.total_tokens
            assert sorted(item.index for item in response.data) == list(range(len(keys)))
            for item in response.data:
                assert len(item.embedding) == 1536 and all(math.isfinite(v) for v in item.embedding)
                cache[keys[item.index]] = item.embedding
                accounting["successful_embeddings"] += 1
        except Exception:
            accounting["failures"] += 1
            raise
    return cache


def paired_counts(rows: list[dict[str, Any]], candidate: str) -> dict[str, Any]:
    """Count per-cutoff binary coverage gains/losses against same-run B0."""
    result = {}
    for metric in METRICS[:-1]:
        result[metric] = {}
        for k in ("1", "3", "5"):
            groups: dict[str, list[str]] = {name:[] for name in ("improved", "unchanged", "regressed")}
            for row in rows:
                delta = int(row["variants"][candidate]["metrics"][k][metric]) - int(row["variants"]["B0"]["metrics"][k][metric])
                groups["improved" if delta > 0 else "regressed" if delta < 0 else "unchanged"].append(row["question"]["id"])
            result[metric][k] = {name:dict(count=len(ids), ids=ids) for name, ids in groups.items()}
    return result


def _result_from_saved(question: ev.DocumentQuestion, row: dict[str, Any]) -> ev.DocumentResult:
    ranks = [ev.DocumentRank(r["rank"], r["chunk_id"], ev.source_identity.DocumentSourceKey.parse(r["document_source_key"]), r["document_id"], r["legislation_number"]) for r in row["ranks"]]
    return ev.evaluate_question(question, ranks)


def run() -> None:
    """Attempt the authorized real experiment once; persist failures without retry."""
    state = _load()
    assert state["status"] == "prepared", "Already attempted; do not rerun"
    eligible, audit = detector_audit()
    assert audit == state["detector"]
    assert all(m12d._hash(ROOT / p) == h for p, h in state["input_hashes"].items())
    production, copy = (Path(state["chroma"][k]).resolve() for k in ("production_path", "copy_path"))
    assert copy != production and production not in copy.parents
    assert m12d._tree(production) == state["chroma"]["production_files_before"]
    collection = m12d.chromadb.PersistentClient(path=str(copy)).get_collection(config.COLLECTION_NAME, embedding_function=None)
    assert m12d._logical(collection) == state["chroma"]["logical_before"]
    assert retrieve.distance_metric(collection) == "l2"
    model = state["configuration"]["model"]
    inputs = {q.id:dict(raw=q.question, enriched=state["titles"][detect_laws(q.question)[0]] + "\n\n" + q.question) for q in eligible}
    state["embedding_inputs"] = inputs
    state["status"] = "running"
    _save(state)
    try:
        with m12d.OpenAI(api_key=config.OPENAI_API_KEY, max_retries=0, timeout=60.0) as client:
            cache = cached_embeddings(client.embeddings, [(model, text) for item in inputs.values() for text in item.values()], state["api"])
        _save(state)
        assert len(cache) == 2 * len(eligible)
        for q in eligible:
            law = detect_laws(q.question)[0]
            row = dict(question=q.to_dict(), detected_law=law, detected_document=m12d.DOCS[law],
                       accepted_wrong_top1=q.id in WRONG_TOP1, accepted_complete_miss=q.id in MISSES, variants={})
            for variant in VARIANTS:
                text = inputs[q.id]["enriched" if variant in ("A1", "A3") else "raw"]
                where = document_filter(law) if variant in ("A2", "A3") else None
                chunks = retrieve.retrieve_by_embedding(cache[(model, text)], collection=collection, top_k=5, where=where)
                assert len(chunks) == 5
                if where and any(c.metadata["document_id"] != m12d.DOCS[law] for c in chunks):
                    raise RuntimeError("STOP — FILTER IMPLEMENTATION ERROR")
                result = ev.evaluate_retrieved(q, chunks).to_dict()
                for rank, chunk in zip(result["ranks"], chunks):
                    rank.update(distance=chunk.distance, text_sha256=hashlib.sha256(chunk.text.encode("utf-8")).hexdigest())
                result["where"] = where
                result["query_input_sha256"] = hashlib.sha256(text.encode("utf-8")).hexdigest()
                row["variants"][variant] = result
            state["results"].append(row)
            _save(state)
            print(f"Completed {q.id}: B0/A1/A2/A3", flush=True)
        state["status"] = "completed"
    except Exception as exc:
        state["status"] = "blocked"
        # Do not serialize arbitrary SDK messages/headers or credential-bearing URLs.
        state["error_type"] = type(exc).__name__
        print("Experiment stopped: " + type(exc).__name__, flush=True)
    finally:
        state["chroma"]["production_unchanged"] = m12d._tree(production) == state["chroma"]["production_files_before"]
        state["chroma"]["logical_after"] = m12d._logical(collection)
        state["chroma"]["logical_unchanged"] = state["chroma"]["logical_after"] == state["chroma"]["logical_before"]
        state["inputs_unchanged"] = all(m12d._hash(ROOT / p) == h for p, h in state["input_hashes"].items())
        if not all((state["chroma"]["production_unchanged"], state["chroma"]["logical_unchanged"], state["inputs_unchanged"])):
            state["status"] = "blocked"
        if state["status"] == "completed":
            state["verdict"] = "M12F-A READY FOR REVIEW"
        _save(state)
        render()
    if state["status"] != "completed":
        raise SystemExit(1)


def render() -> None:
    """Recompute saved metrics and render reports offline without opening Chroma."""
    state = _load()
    questions = {q.id:q for q in m12d._questions()}
    rows = state["results"]
    state["summaries"] = {}
    for v in VARIANTS:
        results = [_result_from_saved(questions[r["question"]["id"]], r["variants"][v]) for r in rows]
        assert all(result.to_dict()["metrics"] == row["variants"][v]["metrics"] for result, row in zip(results, rows))
        state["summaries"][v] = ev.summarize(results)
    state["paired_definition"] = "At each cutoff and each binary coverage metric: false to true = improved; true to false = regressed; same flag = unchanged. Source ANY/ALL and Document Hit/ALL reported separately; no cross-cutoff aggregate hides tradeoffs. Intrusion is a slot fraction, reported separately."
    state["paired"] = {v:paired_counts(rows, v) for v in VARIANTS[1:]}
    state["wrong_document_filtered_slots"] = {v:sum(rank["document_id"] != row["detected_document"] for row in rows for rank in row["variants"][v]["ranks"]) for v in ("A2", "A3")}
    saved = {r["question"]["id"]:r for r in json.loads(m12d.JSON_PATH.read_bytes())["results"]}
    state["B0_vs_saved_M12D"] = {r["question"]["id"]:dict(rank_ids_equal=[x["chunk_id"] for x in r["variants"]["B0"]["ranks"]] == [x["chunk_id"] for x in saved[r["question"]["id"]]["ranks"]], saved_metrics=saved[r["question"]["id"]]["metrics"], fresh_metrics=r["variants"]["B0"]["metrics"]) for r in rows}
    _save(state)
    fields = ["id", "question", "detected_law", "expected_sources", "variant", "rank", "chunk_id", "document_source_key", "document_id", "distance"]
    fields += [f"{m}@{k}" for m in METRICS for k in (1,3,5)]
    with OUT.with_suffix(".csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            q = questions[row["question"]["id"]]
            for v, result in row["variants"].items():
                for rank in result["ranks"]:
                    record = {k:rank[k] for k in fields if k in rank}
                    record.update(id=q.id, question=q.question, detected_law=row["detected_law"], expected_sources=" | ".join(sorted(map(str,q.expected_sources))), variant=v)
                    record.update({f"{m}@{k}":result["metrics"][str(k)][m] for m in METRICS for k in (1,3,5)})
                    writer.writerow(record)
    a = state["detector"]
    lines = ["# M12F-A — Explicit-Law Signal Experiment", "", state["verdict"], "", NOTICE,
             "A NEW UNSEEN HOLDOUT is mandatory before production adoption. No production winner is selected. M10E B2 remains NOT VALIDATED.", "",
             "## Offline detector and scope", "", f"Exact M12D loader/adapter reused; 105/105 full question records match. Eligible: {a['eligible_count']}/105 ({a['eligible_fraction']:.2%}); breakdown {a['breakdown']}; ambiguous {a['ambiguous_count']}; no explicit law {a['no_explicit_count']}. Gold contradictions and false activations: 0.",
             "Detector reads only question text with Unicode word boundaries; repeated mentions of one number are one law. Gold is consulted only for the post-detection safety check and scoring.",
             "Eligible IDs: " + ", ".join(a["eligible_ids"]),
             f"Scope ceiling: {len(a['complete_miss_eligible'])}/6 complete 5607 misses; {len(a['wrong_top1_eligible'])}/10 accepted wrong-document Top1 failures. Eligible failure IDs: {a['wrong_top1_eligible']}. This is not a recovery forecast.",
             "Untouched complete misses: " + ", ".join(a["untouched_complete_misses"]),
             "Untouched wrong-document Top1 failures: " + ", ".join(a["untouched_wrong_top1"]), "",
             "## Configuration and accounting", "", "B0 uses original raw text. A1 uses the admitted official display title, one blank line, then unchanged original text. A2 shares B0's vector and adds detected-document equality filtering; A3 shares A1's vector and adds that filter. K=5, native L2, no reranking, deduplication, lexical retrieval or corpus re-embedding.",
             "Query embeddings use text-embedding-3-small, 1536 dimensions; SDK max_retries=0. [Official embedding API documentation](https://developers.openai.com/api/docs/guides/embeddings).", "", "```json", json.dumps(state["api"], indent=2), "```", "",
             f"Copy verified byte-for-byte before opening. Logical state: {state['chroma']['logical_before']}. Production bytes unchanged: {state['chroma'].get('production_unchanged')}; copy logical state unchanged: {state['chroma'].get('logical_unchanged')}; frozen inputs/code unchanged: {state.get('inputs_unchanged')}.",
             "Only the copy was opened; full before-copy file hashes and input fingerprints are in JSON.", "", "## Metrics", "",
             "Eligible-subset scores below are not 105-question system scores. The accepted full M12D baseline is reported separately; excluded questions were not rerun or intervened upon.", "",
             "| Population / candidate | Metric | @1 | @3 | @5 |", "|---|---|---:|---:|---:|"]
    for label, summary in [(f"Eligible n={len(rows)} / {v}",state["summaries"][v]) for v in VARIANTS] + [("M12D accepted n=105",state["baseline_m12d_105"])]:
        for metric in METRICS:
            vals = [summary["overall"]["metrics"][str(k)][metric] for k in (1,3,5)]
            lines.append("| " + label + " | " + metric + " | " + " | ".join(f"{v:.2%}" if v is not None else "N/A" for v in vals) + " |")
    lines += ["", "## Paired changes versus fresh B0", "", state["paired_definition"], "", "| Candidate | Metric | K | Improved | Unchanged | Regressed |", "|---|---|---:|---:|---:|---:|"]
    for v, metrics in state["paired"].items():
        for metric, cutoffs in metrics.items():
            for k, counts in cutoffs.items():
                lines.append(f"| {v} | {metric} | {k} | {counts['improved']['count']} | {counts['unchanged']['count']} | {counts['regressed']['count']} |")
    lines += ["", f"A2/A3 wrong-document returned slots: {state['wrong_document_filtered_slots']}. Zero intrusion is mechanically expected from filtering; it is not evidence by itself of better Article coverage.", "", "## Every eligible paired ranking", ""]
    for row in rows:
        q = questions[row["question"]["id"]]
        lines += [f"### {q.id}", "", q.question, "", "Expected: " + ", ".join(sorted(map(str,q.expected_sources))), f"Detected law: {row['detected_law']}; accepted complete miss: {row['accepted_complete_miss']}; accepted wrong-document Top1: {row['accepted_wrong_top1']}.", "", "| Candidate | Rank | Chunk | DocumentSourceKey | L2 |", "|---|---:|---|---|---:|"]
        for v, result in row["variants"].items():
            for r in result["ranks"]:
                lines.append(f"| {v} | {r['rank']} | {r['chunk_id']} | {r['document_source_key']} | {r['distance']:.9f} |")
        lines += ["", "Source ANY @1/@3/@5: " + "; ".join(v + "=" + "/".join(str(int(result["metrics"][k]["source_any"])) for k in ("1","3","5")) for v,result in row["variants"].items()), ""]
    lines += ["## Interpretation boundary", "", "The eligible population is six 5607 questions only. k5607-002 is the only eligible accepted wrong-document/complete-miss case. The remaining five complete 5607 misses cannot be affected by this strategy. Same-run B0 is the comparator; saved M12D is historical context, and per-question B0 drift checks are in JSON.", "No corpus re-embedding is needed for these query-side candidates. No production code, index or frozen dataset was changed. No commit or adoption. A new unseen holdout is mandatory.", ""]
    OUT.with_suffix(".md").write_text("\n".join(line.rstrip() for line in lines).rstrip()+"\n", encoding="utf-8")


def main() -> None:
    """Keep preparation, one-shot real run and offline rendering distinct."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("detector", "prepare", "run", "render"))
    args = parser.parse_args()
    {"detector":detector_audit, "prepare":prepare, "run":run, "render":render}[args.phase]()


if __name__ == "__main__":
    main()
