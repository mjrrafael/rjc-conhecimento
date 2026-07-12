#!/usr/bin/env python3
"""Write a classified SHA-256 manifest for every path changed from origin/main."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "auditoria" / "execucoes" / "monitor-v3-2026-07-12" / "manifesto_diff.csv"
CYCLIC_GENERATED = {
    OUT.relative_to(ROOT).as_posix(),
    "auditoria/execucoes/monitor-v3-2026-07-12/inventario_integral.csv",
}


def purpose(path: str) -> str:
    if path.startswith(".github/workflows/"):
        return "CI obrigatório fail-closed"
    if path.startswith("auditoria/") or path.startswith("docs/monitoramento/"):
        return "evidência e ledger da vigília"
    if path.startswith("scripts/"):
        return "controle fail-closed e auditoria"
    if path in {"index.html", "404.html", "robots.txt", "llms.txt", "_config.yml", ".nojekyll"}:
        return "quarentena segura do Pages legado"
    if path.startswith("public/"):
        return "artefato público neutro"
    return "A_VALIDAR"


def main() -> int:
    raw = subprocess.check_output(["git", "diff", "--name-status", "origin/main...HEAD"], cwd=ROOT, text=True, encoding="utf-8")
    rows = []
    for line in raw.splitlines():
        status, path = line.split("\t", 1)
        target = ROOT / path
        digest = (
            hashlib.sha256(target.read_bytes()).hexdigest()
            if target.is_file() and path not in CYCLIC_GENERATED
            else "SELF_REFERENTIAL_GENERATED_SET"
        )
        rows.append((path, status, digest, purpose(path), "rederivado de origin/main"))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(("caminho", "status_git", "sha256", "finalidade", "origem"))
        writer.writerows(rows)
    print(f"manifested={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
