"""Offline M10E-C diagnostics from frozen reports; standard library only."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
INPUTS = ("m10e-retrieval-experiments", "m10e-holdout-b0-vs-b2")
Row = dict[str, Any]


def allocate(dense: list[Row], hybrid: list[Row], strategy: str) -> list[Row]:
    """Select five unique chunks using a dense anchor or equal-turn allocation.

    Only ranked records are accepted: question text, gold, law selection and
    scores cannot influence allocation. Input order resolves all priorities.
    """
    if strategy == "C1":
        stream = dense[:1] + hybrid
    elif strategy == "C2":
        stream = []
        # Each turn consumes the next not-yet-selected chunk from that list.
        offsets = [0, 0]
        seen: set[str] = set()
        lists = (dense, hybrid)
        while len(stream) < 5:
            progress = False
            for turn, ranking in enumerate(lists):
                while offsets[turn] < len(ranking) and ranking[offsets[turn]]["chunk_id"] in seen:
                    offsets[turn] += 1
                if offsets[turn] < len(ranking):
                    item = ranking[offsets[turn]]
                    offsets[turn] += 1
                    stream.append(item)
                    seen.add(item["chunk_id"])
                    progress = True
                    if len(stream) == 5:
                        break
            if not progress:
                break
    else:
        raise ValueError("Unknown strategy")
    result = []
    selected: set[str] = set()
    for item in stream:
        if item["chunk_id"] not in selected:
            selected.add(item["chunk_id"])
            result.append(dict(item, rank=len(result) + 1))
        if len(result) == 5:
            break
    if len(result) != 5:
        raise ValueError("Insufficient persisted candidates for exact Top-5 replay")
    return result


def measure(question: Row, ranking: list[Row]) -> Row:
    """Apply frozen source-set and known-law denominators to saved rankings."""
    gold = set(question["expected_sources"])
    laws = set(question["expected_legislations"])
    result: Row = {}
    for k in (1, 3, 5):
        keys = {r["qualified_source_key"] for r in ranking[:k]}
        result[f"ANY@{k}"] = bool(gold & keys)
        result[f"ALL@{k}"] = gold <= keys
        result[f"Legislation Hit@{k}"] = any(r["legislation_number"] in laws for r in ranking[:k])
    known = [r for r in ranking[:5] if r["legislation_number"] is not None]
    result["cross-law intrusion@5"] = sum(r["legislation_number"] not in laws for r in known) / len(known) if known else None
    return result


def classify(question: Row, dense: list[Row], hybrid: list[Row]) -> list[str]:
    """Return overlapping diagnostic labels, with coverage checked at 1/3/5."""
    gold = set(question["expected_sources"])
    labels = []
    coverage = [(gold & {r["qualified_source_key"] for r in ranks[:k]})
                for k in (1, 3, 5) for ranks in (dense, hybrid)]
    if any(coverage[i + 1] - coverage[i] for i in (0, 2, 4)):
        labels.append("HYBRID RECOVERY")
    if any(coverage[i] - coverage[i + 1] for i in (0, 2, 4)):
        labels.append("DENSE EVIDENCE DISPLACEMENT")
    b0, b2 = measure(question, dense), measure(question, hybrid)
    if len(gold) > 1:
        if b0["ALL@5"] and not b2["ALL@5"]:
            labels.append("MULTI-SOURCE COMPLETENESS LOSS")
        if not b0["ALL@5"] and b2["ALL@5"]:
            labels.append("MULTI-SOURCE COMPLETENESS GAIN")
    original = {r["chunk_id"] for r in dense}
    if any(r["chunk_id"] not in original and r["legislation_number"] is not None
           and r["legislation_number"] not in question["expected_legislations"] for r in hybrid):
        labels.append("CROSS-LAW INTRUSION")
    if not labels and [r["chunk_id"] for r in dense] != [r["chunk_id"] for r in hybrid]:
        labels.append("BENIGN REORDERING")
    return labels


def analyze() -> Row:
    """Read only the two frozen JSON reports and replay C1/C2 on saved Top-5."""
    output: Row = {"development_only": True, "selected_candidate": None, "input_sha256": {}, "questions": [], "summaries": {}}
    for benchmark, name in zip(("M10E-A", "M10E-B"), INPUTS):
        path = ROOT / "reports/evaluation" / (name + ".json")
        raw = path.read_bytes()
        output["input_sha256"][name + ".json"] = hashlib.sha256(raw).hexdigest()
        report = json.loads(raw)
        b2 = {r["id"]: r for r in report["results"]["B2"]}
        for q in report["results"]["B0"]:
            hybrid = b2[q["id"]]
            assert sorted(q["expected_sources"]) == sorted(hybrid["expected_sources"])
            rankings = {"B0": q["ranks"], "B2": hybrid["ranks"]}
            for strategy in ("C1", "C2"):
                rankings[strategy] = allocate(rankings["B0"], rankings["B2"], strategy)
            metrics = {s: measure(q, ranks) for s, ranks in rankings.items()}
            # Verify compatibility with every frozen Boolean score before replay reporting.
            for strategy, frozen in (("B0", q), ("B2", hybrid)):
                for label, field in (("ANY", "any_source_hit_at_"), ("ALL", "all_sources_match_at_"), ("Legislation Hit", "expected_legislation_hit_at_")):
                    for k in (1, 3, 5):
                        assert metrics[strategy][f"{label}@{k}"] == frozen[field + str(k)]
                assert metrics[strategy]["cross-law intrusion@5"] == frozen["non_expected_legislation_share_at_5"]
            output["questions"].append({"benchmark": benchmark, "id": q["id"], "dataset": q["dataset"],
                "expected_sources": q["expected_sources"], "labels": classify(q, rankings["B0"], rankings["B2"]),
                "rankings": rankings, "metrics": metrics})
    for benchmark in ("M10E-A", "M10E-B", "combined"):
        for law in ("all", "5326", "4458"):
            rows = [q for q in output["questions"] if (benchmark == "combined" or q["benchmark"] == benchmark) and (law == "all" or q["dataset"] == law)]
            group = output["summaries"][benchmark + "/" + law] = {}
            for strategy in ("B0", "B2", "C1", "C2"):
                summary = {m: sum(q["metrics"][strategy][m] for q in rows) / len(rows) for m in rows[0]["metrics"][strategy]}
                for label, multi, metric in (("single-source ANY@5", False, "ANY@5"), ("multi-source ALL@5", True, "ALL@5")):
                    subset = [q for q in rows if (len(q["expected_sources"]) > 1) == multi]
                    summary[label] = sum(q["metrics"][strategy][metric] for q in subset) / len(subset) if subset else None
                    summary[label + " denominator"] = len(subset)
                group[strategy] = dict(summary, count=len(rows))
    return output


def main() -> None:
    """Write development replay JSON and one CSV row per question/strategy."""
    report = analyze()
    base = ROOT / "reports/evaluation/m10e-hybrid-failure-analysis"
    base.with_suffix(".json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    rows = []
    for q in report["questions"]:
        for strategy, ranks in q["rankings"].items():
            rows.append({"benchmark": q["benchmark"], "id": q["id"], "dataset": q["dataset"], "strategy": strategy,
                "development_only": True, "expected_sources": " | ".join(q["expected_sources"]),
                "top5_chunk_ids": " | ".join(r["chunk_id"] for r in ranks),
                "top5_sources": " | ".join(r["qualified_source_key"] for r in ranks),
                "b0_b2_taxonomy": " | ".join(q["labels"]), **q["metrics"][strategy]})
    with base.with_suffix(".csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
