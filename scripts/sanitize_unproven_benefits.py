#!/usr/bin/env python3
"""Externalize unproven benefit datasets before a public release.

The command is intentionally destructive only after it has copied both input
files, checked their hashes and written an archive manifest outside this
repository.  It never derives a legal fact or promotes an entry.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CROSSWALK = ROOT / "data" / "benefits_crosswalk.json"
DEFAULT_QUARANTINE = ROOT / "data" / "benefits_quarantine.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_entries(path: Path) -> tuple[dict, list[dict]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    entries = payload.get("entries") if isinstance(payload, dict) else None
    if not isinstance(entries, list) or not all(isinstance(entry, dict) for entry in entries):
        raise ValueError(f"{path} não contém entries válidos")
    return payload, entries


def sanitized_crosswalk(count: int, run_date: str) -> dict:
    return {
        "schema": "rjc-validated-benefits-crosswalk-v3",
        "publication_status": "BLOQUEADO_SEM_PROVA_MATERIAL",
        "revalidation": {
            "run_date": run_date,
            "public_entries": 0,
            "legacy_entries_externalized": count,
            "reason": "proveniencia_por_campo_e_recibos_nativos_ausentes",
        },
        "entries": [],
    }


def sanitized_quarantine(count: int, run_date: str) -> dict:
    return {
        "schema": "rjc-benefits-quarantine-v1",
        "publication_status": "NAO_PUBLICA_EXTERNALIZADA",
        "revalidation": {
            "run_date": run_date,
            "public_entries": 0,
            "legacy_entries_externalized": count,
            "reason": "quarentena_material_nao_permanecera_em_repositorio_publico",
        },
        "entries": [],
    }


def write_json_atomic(path: Path, value: dict) -> None:
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="\n", dir=path.parent, delete=False) as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        temporary = Path(handle.name)
    temporary.replace(path)


def archive_and_sanitize(crosswalk: Path, quarantine: Path, archive_dir: Path, run_date: str) -> dict:
    crosswalk_payload, crosswalk_entries = load_entries(crosswalk)
    quarantine_payload, quarantine_entries = load_entries(quarantine)
    archive_dir = archive_dir.resolve()
    if archive_dir.is_relative_to(ROOT.resolve()):
        raise ValueError("o arquivo de evidências deve ficar fora do repositório público")
    if archive_dir.exists() and any(archive_dir.iterdir()):
        raise FileExistsError(f"arquivo de evidências já existe e não será sobrescrito: {archive_dir}")
    archive_dir.mkdir(parents=True, exist_ok=False)

    copies = ((crosswalk, "benefits_crosswalk.legacy.json"), (quarantine, "benefits_quarantine.legacy.json"))
    manifest_files: list[dict[str, object]] = []
    for source, name in copies:
        destination = archive_dir / name
        shutil.copy2(source, destination)
        source_sha = sha256_file(source)
        archived_sha = sha256_file(destination)
        if source_sha != archived_sha:
            raise RuntimeError(f"cópia de evidência divergente: {source}")
        manifest_files.append({"name": name, "sha256": archived_sha, "bytes": destination.stat().st_size})

    manifest = {
        "schema": "rjc-benefit-sanitization-archive-v1",
        "run_date": run_date,
        "inputs": {
            "crosswalk_entries": len(crosswalk_entries),
            "quarantine_entries": len(quarantine_entries),
            "files": manifest_files,
        },
        "result": "dados_legados_externalizados_sem_promocao_publica",
    }
    write_json_atomic(archive_dir / "archive_manifest.json", manifest)

    write_json_atomic(crosswalk, sanitized_crosswalk(len(crosswalk_entries), run_date))
    write_json_atomic(quarantine, sanitized_quarantine(len(quarantine_entries), run_date))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--crosswalk", type=Path, default=DEFAULT_CROSSWALK)
    parser.add_argument("--quarantine", type=Path, default=DEFAULT_QUARANTINE)
    parser.add_argument("--archive-dir", type=Path, required=True)
    parser.add_argument("--run-date", required=True, help="data editorial AAAA-MM-DD; não é data jurídica")
    parser.add_argument("--apply", action="store_true", help="executa cópia verificada e saneamento")
    args = parser.parse_args()
    _, cards = load_entries(args.crosswalk)
    _, quarantine = load_entries(args.quarantine)
    if not args.apply:
        print(json.dumps({"cards": len(cards), "quarantine": len(quarantine), "action": "dry-run"}, ensure_ascii=False))
        return 0
    manifest = archive_and_sanitize(args.crosswalk, args.quarantine, args.archive_dir, args.run_date)
    print(json.dumps(manifest, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
