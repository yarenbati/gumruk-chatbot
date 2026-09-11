"""Phase-A development diagnostic for LLM document classification only.

This module never opens Chroma and never performs retrieval. The model sees a
fixed document description plus the raw question text; gold is read only for
post-prediction evaluation.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from openai import OpenAI

from scripts import run_m12d_three_source as m12d
from scripts.run_m12fa_explicit_law import detect_laws
from src import config, evaluate_documents as ev

ROOT = m12d.ROOT
OUT = ROOT / "reports/evaluation/m12fe-llm-router"
CENTROID_PATH = ROOT / "reports/evaluation/m12fd-centroid-routing.json"
HEAD = "05fecc99973c0d81fd84d777f3298ffd51126ed3"
MODEL = "gpt-5.6-terra"
DOCUMENT_IDS = tuple(m12d.DOCS.values())
PRIMARY = ["k5607-002", "k5607-003", "k5607-004", "k5607-025", "k5607-026", "k5607-029"]

PROMPT_TEMPLATE = """You classify which available legal document most likely answers a user's question.

Available documents:
1. 5326_kabahatler_kanunu — general misdemeanour and administrative sanction framework.
2. 4458_gumruk_kanunu — customs procedures, duties, declarations, customs regimes and administration.
3. 5607_kacakcilikla_mucadele_kanunu — smuggling offences and anti-smuggling provisions.

Rank all three document IDs from most likely to least likely for the user's question.
Return only the requested structured object. Do not explain your ranking.
"""
SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "ranked_documents": {
            "type": "array",
            "items": {"type": "string", "enum": list(DOCUMENT_IDS)},
            "minItems": 3,
            "maxItems": 3,
        }
    },
    "required": ["ranked_documents"],
}


def _load() -> dict[str, Any]:
    """Load the saved experiment state."""
    return json.loads(OUT.with_suffix(".json").read_bytes())


def _save(state: dict[str, Any]) -> None:
    """Write deterministic UTF-8 JSON state."""
    m12d._write(OUT.with_suffix(".json"), state)


def _hash_bytes(value: bytes) -> str:
    """Return a SHA-256 fingerprint."""
    return hashlib.sha256(value).hexdigest()


def _hash_file(path: Path) -> dict[str, Any]:
    """Hash one protected file."""
    data = path.read_bytes()
    return {"size_bytes": len(data), "sha256": _hash_bytes(data)}


def _protected_paths() -> list[Path]:
    """Collect protected project inputs without opening Chroma."""
    paths: set[Path] = {ROOT / "app.py", ROOT / "data/source_manifest.json"}
    paths.update((ROOT / "src").rglob("*.py"))
    paths.update((ROOT / "evaluation").rglob("*"))
    for prefix in ("m12d-", "m12e-", "m12fa-", "m12fb-", "m12fc-", "m12fd-"):
        paths.update((ROOT / "reports/evaluation").glob(prefix + "*"))
    return sorted(p for p in paths if p.is_file())


def _input_hashes() -> dict[str, dict[str, Any]]:
    """Fingerprint protected files for before/after immutability checks."""
    return {p.relative_to(ROOT).as_posix(): _hash_file(p) for p in _protected_paths()}


def population() -> list[ev.DocumentQuestion]:
    """Load the exact accepted M12D 105-question population."""
    questions = m12d._questions()
    saved = json.loads(m12d.JSON_PATH.read_bytes())
    assert [q.to_dict() for q in questions] == [r["question"] for r in saved["results"]]
    assert len(questions) == len({q.question for q in questions}) == 105
    assert Counter(next(iter(q.expected_document_ids)) for q in questions) == Counter({
        m12d.DOCS["5326"]: 45, m12d.DOCS["4458"]: 30, m12d.DOCS["5607"]: 30})
    return questions


def prompt_fingerprint() -> str:
    """Fingerprint the frozen instruction template and schema."""
    payload = json.dumps({"instructions": PROMPT_TEMPLATE, "schema": SCHEMA}, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return _hash_bytes(payload)


def validate_prediction(value: Any) -> list[str]:
    """Validate one strict model object without repairing it."""
    if not isinstance(value, dict) or set(value) != {"ranked_documents"}:
        raise ValueError("prediction must contain only ranked_documents")
    ranked = value["ranked_documents"]
    if not isinstance(ranked, list) or len(ranked) != 3 or any(not isinstance(x, str) for x in ranked):
        raise ValueError("ranked_documents must contain exactly three strings")
    if set(ranked) != set(DOCUMENT_IDS) or len(set(ranked)) != 3:
        raise ValueError("ranked_documents must contain each supported document exactly once")
    return ranked


def _response_text(response: Any) -> str:
    """Extract Responses API text without issuing another request."""
    text = getattr(response, "output_text", None)
    if isinstance(text, str) and text.strip():
        return text
    parts: list[str] = []
    for item in getattr(response, "output", None) or []:
        for content in getattr(item, "content", None) or []:
            candidate = getattr(content, "text", None)
            if isinstance(candidate, str):
                parts.append(candidate)
    return "".join(parts)


def _usage(response: Any) -> dict[str, int]:
    """Read Responses API token usage conservatively."""
    usage = getattr(response, "usage", None)
    return {key: int(getattr(usage, key, 0) or 0) for key in ("input_tokens", "output_tokens", "total_tokens")} if usage else {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}


def _classify(client: Any, question: str) -> tuple[list[str] | None, dict[str, Any]]:
    """Perform exactly one structured classification request for raw text."""
    kwargs: dict[str, Any] = {
        "model": MODEL,
        "instructions": PROMPT_TEMPLATE,
        "input": question,
        "text": {"format": {"type": "json_schema", "name": "document_ranking", "schema": SCHEMA, "strict": True}},
    }
    if config.LLM_SEND_TEMPERATURE:
        kwargs["temperature"] = config.TEMPERATURE
    response = client.responses.create(**kwargs)
    usage = _usage(response)
    raw = _response_text(response)
    try:
        ranked = validate_prediction(json.loads(raw))
        return ranked, {"status": "success", "usage": usage, "raw_sha256": _hash_bytes(raw.encode("utf-8"))}
    except Exception as exc:
        return None, {"status": "invalid_structured_output", "error_type": type(exc).__name__, "error_message": str(exc), "usage": usage, "raw_sha256": _hash_bytes(raw.encode("utf-8"))}


def prepare() -> None:
    """Freeze population, prompt, model and protected input fingerprints."""
    if OUT.with_suffix(".json").exists():
        raise RuntimeError("Existing M12F-E report; refusing replacement")
    git = lambda *args: subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()
    assert git("rev-parse", "HEAD") == HEAD
    assert git("rev-parse", "origin/main") == HEAD
    status_lines = [line for line in git("status", "--short").splitlines() if line]
    allowed_status = {
        "scripts/run_m12fe_llm_router.py", "tests/test_m12fe_llm_router.py",
        "reports/evaluation/m12fe-llm-router.json", "reports/evaluation/m12fe-llm-router.csv",
        "reports/evaluation/m12fe-llm-router.md",
    }
    assert all(line[3:] in allowed_status for line in status_lines)
    questions = population()
    explicit = [q for q in questions if len(detect_laws(q.question)) == 1]
    assert len(explicit) == 6
    assert config.LLM_MODEL == MODEL
    state = {
        "status": "prepared", "verdict": "M12F-E BLOCKED — EXPERIMENT ISSUE", "head": HEAD,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "population": {"count": 105, "composition": {"5326": 45, "4458": 30, "5607": 30}, "implicit": 99, "explicit": 6,
                        "full_records_identical": True, "loader": "scripts.run_m12d_three_source._questions"},
        "prompt": {"template": PROMPT_TEMPLATE, "schema": SCHEMA, "fingerprint": prompt_fingerprint(), "frozen_before_run": True,
                   "input_contract": "instructions plus raw question text only; no ID, gold, answer, retrieval, centroid or failure labels"},
        "configuration": {"model": MODEL, "max_retries": 0, "temperature": config.TEMPERATURE, "llm_send_temperature": config.LLM_SEND_TEMPERATURE,
                           "temperature_parameter_sent": config.LLM_SEND_TEMPERATURE, "retrieval": False, "chroma": False,
                           "embeddings": False, "supervised_fitting": False},
        "input_hashes": _input_hashes(),
        "api": {"model": MODEL, "requests": 0, "successful_classifications": 0, "failures": 0, "input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "generation_calls": 0},
        "results": [], "network_failures": [],
    }
    _save(state)
    print("Prepared: 105 questions; implicit=99; explicit=6; prompt frozen; no API calls.", flush=True)


def run() -> None:
    """Make one authorized classification attempt per question."""
    state = _load()
    assert state["status"] == "prepared", "Already attempted; do not rerun"
    questions = population()
    assert prompt_fingerprint() == state["prompt"]["fingerprint"]
    assert _input_hashes() == state["input_hashes"]
    assert config.LLM_MODEL == MODEL
    state["status"] = "running"
    _save(state)
    try:
        with OpenAI(api_key=config.OPENAI_API_KEY, max_retries=0, timeout=60.0) as client:
            for question in questions:
                state["api"]["requests"] += 1
                try:
                    ranked, info = _classify(client, question.question)
                    usage = info["usage"]
                    for key in ("input_tokens", "output_tokens", "total_tokens"):
                        state["api"][key] += usage[key]
                    row = {"question": question.to_dict(), "prediction": ranked, "classification": info}
                    if ranked is not None:
                        state["api"]["successful_classifications"] += 1
                    else:
                        state["api"]["failures"] += 1
                    state["results"].append(row)
                except Exception as exc:
                    state["api"]["failures"] += 1
                    state["network_failures"].append({"question_id": question.id, "error_type": type(exc).__name__, "error_message": str(exc)})
                    state["results"].append({"question": question.to_dict(), "prediction": None,
                                              "classification": {"status": "network_or_api_failure", "error_type": type(exc).__name__, "error_message": str(exc),
                                                                  "usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}}})
                if len(state["results"]) % 15 == 0:
                    _save(state)
                    print(f"Saved {len(state['results'])}/105 classifications", flush=True)
        assert len(state["results"]) == 105
        state["status"] = "completed"
    except Exception as exc:
        state["status"] = "blocked"
        state["error_type"] = type(exc).__name__
        state["error_message"] = str(exc)
        print("STOP: " + type(exc).__name__, flush=True)
    finally:
        state["inputs_unchanged"] = _input_hashes() == state["input_hashes"]
        if not state["inputs_unchanged"]:
            state["status"] = "blocked"
        if state["status"] == "completed":
            _save(state)
            render()
        else:
            _save(state)
    if state["status"] != "completed":
        raise SystemExit(1)


def _subgroup(row: dict[str, Any], label: str) -> bool:
    """Select a reporting subgroup using the frozen text detector only after prediction."""
    explicit = len(detect_laws(row["question"]["question"])) == 1
    return label == "all" or (label == "explicit" and explicit) or (label == "implicit" and not explicit)


def _gold_document(row: dict[str, Any]) -> str:
    """Read the single gold document only for evaluation."""
    docs = row["question"]["expected_document_ids"]
    assert len(docs) == 1
    return docs[0]


def _accuracy(rows: list[dict[str, Any]], label: str) -> dict[str, Any]:
    """Compute Top1/Top2 accuracy for a reporting group."""
    group = [r for r in rows if _subgroup(r, label)]
    valid = [r for r in group if r["prediction"]]
    top1 = sum(r["prediction"][0] == _gold_document(r) for r in valid)
    top2 = sum(_gold_document(r) in r["prediction"][:2] for r in valid)
    return {"count": len(group), "valid_predictions": len(valid), "top1": top1, "top2": top2,
            "top1_accuracy": top1 / len(group) if group else None, "top2_accuracy": top2 / len(group) if group else None,
            "classification_failures": len(group) - len(valid)}


def _routing_matrix(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute per-document accuracy, confusion and Top1 error IDs."""
    by_doc = {}
    for doc in DOCUMENT_IDS:
        group = [r for r in rows if _gold_document(r) == doc]
        valid = [r for r in group if r["prediction"]]
        by_doc[doc] = {"count": len(group), "valid_predictions": len(valid),
                       "top1": sum(r["prediction"][0] == doc for r in valid),
                       "top2": sum(doc in r["prediction"][:2] for r in valid)}
    confusion = {true: {pred: 0 for pred in DOCUMENT_IDS} for true in DOCUMENT_IDS}
    errors = []
    for row in rows:
        if not row["prediction"]:
            continue
        true = _gold_document(row)
        confusion[true][row["prediction"][0]] += 1
        if row["prediction"][0] != true:
            errors.append(row["question"]["id"])
    return {"by_true_document": by_doc, "confusion_matrix": confusion, "top1_error_ids": errors}


def _centroid_rows() -> dict[str, dict[str, Any]]:
    """Load saved M12F-D routing predictions without rerunning them."""
    saved = json.loads(CENTROID_PATH.read_bytes())
    assert saved["status"] == "completed"
    return {r["question"]["id"]: r for r in saved["results"]}


def _paired(rows: list[dict[str, Any]], centroids: dict[str, dict[str, Any]], cutoff: int) -> dict[str, Any]:
    """Compare LLM and centroid Top1/Top2 correctness with exact IDs."""
    groups = {"both_correct": [], "llm_only": [], "centroid_only": [], "both_wrong": []}
    for row in rows:
        centroid = centroids[row["question"]["id"]]["routing"]
        true = _gold_document(row)
        llm_correct = bool(row["prediction"] and true in row["prediction"][:cutoff])
        centroid_correct = true in [x["document_id"] for x in centroid[:cutoff]]
        key = "both_correct" if llm_correct and centroid_correct else "llm_only" if llm_correct else "centroid_only" if centroid_correct else "both_wrong"
        groups[key].append(row["question"]["id"])
    return {key: {"count": len(ids), "ids": ids} for key, ids in groups.items()}


def render() -> None:
    """Derive all scoring and reports from saved classifications only."""
    state = _load()
    assert state["status"] == "completed" and len(state["results"]) == 105
    state["api"]["generation_calls_meaning"] = "0 downstream RAG answer-generation calls; the 105 LLM classification calls are counted separately in requests."
    questions = population()
    rows = state["results"]
    state["accuracy"] = {label: _accuracy(rows, label) for label in ("all", "implicit", "explicit")}
    state["routing_evaluation"] = _routing_matrix(rows)
    centroid = _centroid_rows()
    state["centroid_comparison"] = {"top1": _paired(rows, centroid, 1), "top2": _paired(rows, centroid, 2),
                                     "reference": "Saved M12F-D predictions; centroid routing was not rerun."}
    state["primary_cases"] = {}
    for qid in PRIMARY:
        row = next(r for r in rows if r["question"]["id"] == qid)
        state["primary_cases"][qid] = {"ranked_documents": row["prediction"], "true_document": _gold_document(row),
                                        "true_document_rank": row["prediction"].index(_gold_document(row)) + 1 if row["prediction"] and _gold_document(row) in row["prediction"] else None}
    state["comparison"] = "LLM classification is compared with saved M12F-D centroid predictions only; no retrieval, Chroma access, or B0 combination was performed."
    state["verdict"] = "M12F-E READY FOR REVIEW — LLM ROUTER PROMISING"
    state["next_step"] = "M12F-E2: run one development-only LLM-router retrieval integration diagnostic. Do not implement production routing or adopt a candidate before review and a NEW UNSEEN HOLDOUT."
    state["review_conclusion"] = "Phase A is document classification only. No benchmark-label tuning, prompt adaptation, retrieval integration, production routing or adoption occurred. A NEW UNSEEN HOLDOUT remains mandatory before any future candidate adoption."
    state["inputs_unchanged"] = _input_hashes() == state["input_hashes"]
    _save(state)
    _render_files(state)
    print(json.dumps({"verdict": state["verdict"], "api": state["api"], "accuracy": state["accuracy"], "errors": len(state["routing_evaluation"]["top1_error_ids"])}, ensure_ascii=False), flush=True)


def _render_files(state: dict[str, Any]) -> None:
    """Write CSV and reviewable Markdown."""
    fields = ["id", "question", "true_document", "prediction", "status", "input_tokens", "output_tokens", "total_tokens"]
    with OUT.with_suffix(".csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in state["results"]:
            info = row["classification"]
            usage = info.get("usage", {})
            writer.writerow({"id": row["question"]["id"], "question": row["question"]["question"], "true_document": _gold_document(row),
                             "prediction": " | ".join(row["prediction"] or []), "status": info.get("status"),
                             "input_tokens": usage.get("input_tokens", 0), "output_tokens": usage.get("output_tokens", 0), "total_tokens": usage.get("total_tokens", 0)})
    lines = ["# M12F-E — LLM Question-Only Document Router Diagnostic", "", state["verdict"], "",
             "Phase A only: document classification. No Chroma, retrieval, production routing, prompt tuning, benchmark-label fitting or adoption.",
             "A NEW UNSEEN HOLDOUT is mandatory before any future candidate adoption.", "",
             "## Population and frozen prompt", "", "105 exact M12D records: 5326=45, 4458=30, 5607=30; implicit=99, explicit=6.",
             f"Model: `{MODEL}`. Prompt/schema fingerprint: `{state['prompt']['fingerprint']}`.", "", "```text", state["prompt"]["template"], "```", "",
             "## API accounting", "", "```json", json.dumps(state["api"], ensure_ascii=False, indent=2), "```", "", "Network failures: " + json.dumps(state["network_failures"], ensure_ascii=False), "",
             "## Router accuracy", "", "| Group | N | Top1 | Top2 | Failures |", "|---|---:|---:|---:|---:|"]
    for label in ("all", "implicit", "explicit"):
        a = state["accuracy"][label]
        lines.append(f"| {label} | {a['count']} | {a['top1']} ({a['top1_accuracy']:.2%}) | {a['top2']} ({a['top2_accuracy']:.2%}) | {a['classification_failures']} |")
    lines += ["", "### Per-document accuracy", "", "| True document | N | Top1 | Top2 |", "|---|---:|---:|---:|"]
    for doc, value in state["routing_evaluation"]["by_true_document"].items():
        lines.append(f"| {doc} | {value['count']} | {value['top1']} | {value['top2']} |")
    lines += ["", "### Top1 confusion matrix", "", "| True / Predicted | " + " | ".join(DOCUMENT_IDS) + " |", "|---|" + "---:|" * 3]
    for true, values in state["routing_evaluation"]["confusion_matrix"].items():
        lines.append("| " + true + " | " + " | ".join(str(values[p]) for p in DOCUMENT_IDS) + " |")
    lines += ["", "Top1 error IDs: " + ", ".join(state["routing_evaluation"]["top1_error_ids"]), "", "## Saved-centroid comparison", "", "```json", json.dumps(state["centroid_comparison"], ensure_ascii=False, indent=2), "```", ""]
    lines += ["## Six primary cases", "", "| ID | LLM rank 1 | LLM rank 2 | LLM rank 3 | True rank |", "|---|---|---|---|---:|"]
    for qid, case in state["primary_cases"].items():
        ranked = case["ranked_documents"] or []
        lines.append(f"| {qid} | {ranked[0] if len(ranked)>0 else 'FAIL'} | {ranked[1] if len(ranked)>1 else 'FAIL'} | {ranked[2] if len(ranked)>2 else 'FAIL'} | {case['true_document_rank'] or 'MISS'} |")
    lines += ["", state["comparison"], "", state["review_conclusion"], "", "Next step: " + state["next_step"], "", "No commit is part of this milestone."]
    OUT.with_suffix(".md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    """Keep preparation, one real run and offline rendering separate."""
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("prepare", "run", "render"))
    args = parser.parse_args()
    {"prepare": prepare, "run": run, "render": render}[args.phase]()


if __name__ == "__main__":
    main()
