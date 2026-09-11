"""Deterministic, source-preparation-only legacy Office normalization."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
import zipfile
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.annex_ingest import detect_file_type

ROOT = Path(__file__).resolve().parents[1]
ZIP_PATH = ROOT / "data/raw/gumruk-yonetmeligi-ekler.zip"
OUTPUT_ROOT = ROOT / "data/processed/gumruk-yonetmeligi-annex-normalized"
OLE_SIGNATURE = bytes.fromhex("d0cf11e0a1b11ae1")


def sha256_bytes(data: bytes) -> str:
    """Return a SHA256 digest."""
    return hashlib.sha256(data).hexdigest()


def find_soffice() -> Path | None:
    """Find LibreOffice without installing it."""
    candidates = [shutil.which(name) for name in ("soffice.com", "soffice.exe", "soffice", "libreoffice.exe", "libreoffice")]
    candidates += [r"C:\Program Files\LibreOffice\program\soffice.com", r"C:\Program Files\LibreOffice\program\soffice.exe", r"C:\Program Files (x86)\LibreOffice\program\soffice.com", r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"]
    return next((Path(candidate).resolve() for candidate in candidates if candidate and Path(candidate).exists()), None)


def probe_libreoffice(executable: Path) -> tuple[str, bool]:
    """Return version text and whether isolated headless startup succeeds."""
    with tempfile.TemporaryDirectory(prefix="m13b2b-profile-") as profile:
        uri = "file:///" + Path(profile).as_posix().lstrip("/")
        result = subprocess.run([str(executable), "--headless", "--version", "--norestore", "--nofirststartwizard", "--nodefault", "--nolockcheck", f"-env:UserInstallation={uri}"], capture_output=True, text=True, timeout=30, check=False)
    version = (result.stdout or result.stderr).strip()
    return version, result.returncode == 0 and bool(version)


def derived_relative_path(member_name: str, member_sha256: str, normalized_format: str) -> str:
    """Return a stable, collision-safe derived path."""
    stem = Path(member_name).stem.replace(" ", "_").replace("/", "_").replace("\\", "_")
    suffix = ".docx" if normalized_format == "DOCX" else ".xlsx"
    folder = "docx" if normalized_format == "DOCX" else "xlsx"
    return f"{folder}/{stem}-{member_sha256[:16]}{suffix}"


def valid_normalized_artifact(path: Path, normalized_format: str) -> bool:
    """Validate an OOXML artifact and open DOCX output through python-docx."""
    if not path.is_file() or path.stat().st_size == 0:
        return False
    try:
        with zipfile.ZipFile(path) as package:
            required = "word/document.xml" if normalized_format == "DOCX" else "xl/workbook.xml"
            if required not in set(package.namelist()):
                return False
        if normalized_format == "DOCX":
            from docx import Document
            Document(str(path))
        return True
    except (OSError, zipfile.BadZipFile, ValueError):
        return False


def cache_valid(entry: dict[str, Any], output_root: Path, tool_version: str) -> bool:
    """Return true only when source, tool, output path, and output hash match."""
    if entry.get("conversion_status") != "SUCCESS" or entry.get("normalization_tool_version") != tool_version:
        return False
    path = output_root / entry["normalized_relative_path"]
    return valid_normalized_artifact(path, entry["normalized_format"]) and sha256_bytes(path.read_bytes()) == entry.get("normalized_sha256")


def _legacy_members(zip_path: Path) -> list[tuple[str, bytes, str]]:
    with zipfile.ZipFile(zip_path) as archive:
        result = []
        for info in archive.infolist():
            data = archive.read(info)
            if info.is_dir() or not data.startswith(OLE_SIGNATURE):
                continue
            if Path(info.filename).suffix.lower() == ".doc":
                result.append((info.filename, data, "DOCX"))
            elif Path(info.filename).suffix.lower() == ".xls":
                result.append((info.filename, data, "XLSX"))
        return result


def normalize(zip_path: Path = ZIP_PATH, output_root: Path = OUTPUT_ROOT) -> dict[str, Any]:
    """Normalize legacy members and idempotently reuse valid derived files."""
    executable = find_soffice()
    if executable is None:
        raise RuntimeError("M13B-2B DEPENDENCY REVIEW REQUIRED — LIBREOFFICE NOT AVAILABLE")
    version, headless_ok = probe_libreoffice(executable)
    if not headless_ok:
        raise RuntimeError(f"M13B-2B BLOCKED — LEGACY OFFICE NORMALIZATION GAP: headless probe failed ({version!r})")
    output_root.mkdir(parents=True, exist_ok=True)
    manifest_path = output_root / "normalization-manifest.json"
    old = {}
    if manifest_path.exists():
        old = {x["archive_member_path"]: x for x in json.loads(manifest_path.read_text(encoding="utf-8")).get("entries", [])}
    zip_hash = sha256_bytes(zip_path.read_bytes())
    entries = []
    for member_name, data, normalized_format in _legacy_members(zip_path):
        member_hash = sha256_bytes(data)
        relative = derived_relative_path(member_name, member_hash, normalized_format)
        entry: dict[str, Any] = {"document_id": "gumruk_yonetmeligi", "source_zip_path": str(zip_path.relative_to(ROOT)), "source_zip_sha256": zip_hash, "archive_member_path": member_name, "archive_member_filename": Path(member_name).name, "archive_member_sha256": member_hash, "declared_extension": Path(member_name).suffix.lower(), "detected_source_type": detect_file_type(data), "normalization_tool": "LibreOffice", "normalization_tool_version": version, "normalization_command_family": "soffice --headless --convert-to", "normalized_format": normalized_format, "normalized_relative_path": relative, "normalized_size_bytes": 0, "normalized_sha256": None, "conversion_status": "FAILED", "warnings": []}
        previous = old.get(member_name)
        target = output_root / relative
        if previous and previous.get("archive_member_sha256") == member_hash and cache_valid(previous, output_root, version):
            entry.update(previous); entry["warnings"] = [warning for warning in entry.get("warnings", []) if warning != "CACHE_REUSED"]; entries.append(entry); continue
        expected_suffix = ".docx" if normalized_format == "DOCX" else ".xlsx"
        with tempfile.TemporaryDirectory(prefix="m13b2b-source-") as temp:
            source_dir, out_dir, profile_dir = (Path(temp) / name for name in ("source", "output", "profile"))
            source_dir.mkdir(); out_dir.mkdir(); profile_dir.mkdir()
            source = source_dir / Path(member_name).name; source.write_bytes(data)
            uri = "file:///" + profile_dir.as_posix().lstrip("/")
            convert_format = "docx:Office Open XML Text" if normalized_format == "DOCX" else "xlsx:Calc MS Excel 2007 XML"
            result = subprocess.run([str(executable), "--headless", "--convert-to", convert_format, "--outdir", str(out_dir), "--norestore", "--nofirststartwizard", "--nodefault", "--nolockcheck", f"-env:UserInstallation={uri}", str(source)], capture_output=True, text=True, timeout=120, check=False)
            candidates = list(out_dir.glob("*" + expected_suffix))
            if result.returncode != 0:
                entry["warnings"].append(f"RETURN_CODE_{result.returncode}")
            if len(candidates) != 1:
                entry["conversion_status"] = "OUTPUT_MISSING" if not candidates else "OUTPUT_AMBIGUOUS"; entry["warnings"].append((result.stderr or result.stdout or "conversion produced no unique output").strip()[:1000])
            elif not valid_normalized_artifact(candidates[0], normalized_format):
                entry["warnings"].append("NORMALIZED_OUTPUT_INVALID")
            else:
                target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(candidates[0].read_bytes()); normalized_data = target.read_bytes(); entry["normalized_size_bytes"] = len(normalized_data); entry["normalized_sha256"] = sha256_bytes(normalized_data); entry["conversion_status"] = "SUCCESS"
        entries.append(entry)
    manifest = {"schema_version": 1, "normalization_tool": "LibreOffice", "normalization_tool_version": version, "source_zip_sha256": zip_hash, "entries": sorted(entries, key=lambda x: x["archive_member_path"])}
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    """Run normalization and print a status summary."""
    parser = argparse.ArgumentParser(); parser.add_argument("--zip", type=Path, default=ZIP_PATH); parser.add_argument("--output-root", type=Path, default=OUTPUT_ROOT); args = parser.parse_args()
    manifest = normalize(args.zip, args.output_root)
    statuses: dict[str, int] = {}
    for entry in manifest["entries"]: statuses[entry["conversion_status"]] = statuses.get(entry["conversion_status"], 0) + 1
    print(json.dumps({"tool": manifest["normalization_tool"], "version": manifest["normalization_tool_version"], "members": len(manifest["entries"]), "statuses": statuses, "manifest": str((args.output_root / "normalization-manifest.json").relative_to(ROOT))}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
