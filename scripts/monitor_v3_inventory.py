#!/usr/bin/env python3
"""Rebuild the v3 repository inventory and the mandatory closed source skeleton."""

from __future__ import annotations

import csv
import hashlib
import os
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def resolve_run() -> Path:
    configured = os.environ.get("RJC_MONITOR_RUN", "").strip()
    if configured:
        path = Path(configured)
        return path if path.is_absolute() else ROOT / path
    base = ROOT / "auditoria" / "execucoes"
    candidates = sorted(path for path in base.glob("monitor-v3-*") if path.is_dir())
    if not candidates:
        raise RuntimeError("nenhuma execução monitor-v3 encontrada; defina RJC_MONITOR_RUN")
    return candidates[-1]


RUN = resolve_run()
UFS = "AC AL AM AP BA CE DF ES GO MA MG MS MT PA PB PE PI PR RJ RN RO RR RS SC SE SP TO".split()
STATE_CLASSES = ("SEFAZ_LEGISLACAO", "DOE", "ASSEMBLEIA_LEGISLATIVA")
FEDERAL_FAMILIES = (
    "PLANALTO",
    "DOU_IMPRENSA_NACIONAL",
    "RFB_SIJUT_NORMAS",
    "PGFN",
    "CONFAZ_CONVENIOS",
    "CONFAZ_PROTOCOLOS",
    "CONFAZ_AJUSTES_SINIEF",
    "CONFAZ_ATOS_COTEPE",
    "CGIBS_PORTAL_NACIONAL_TCS",
    "SENADO",
    "STF",
    "STJ",
    "CARF",
)
URL_RE = re.compile(r"https?://[^\s\"'<>]+", re.I)


def sha256(path: Path) -> str:
    raw = path.read_bytes()
    # Text files are normalized so inventory hashes are stable across the
    # Windows authoring worktree and Linux GitHub Actions checkouts.
    if b"\x00" not in raw:
        raw = raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(raw).hexdigest()


def git_files() -> set[str]:
    raw = subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", "HEAD"], cwd=ROOT, text=True, encoding="utf-8"
    )
    return {line.strip().replace("\\", "/") for line in raw.splitlines() if line.strip()}


def fs_files() -> set[str]:
    result: set[str] = set()
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT).as_posix()
        if rel == ".git" or rel.startswith(".git/"):
            continue
        result.add(rel)
    return result


def referenced_urls(paths: set[str]) -> set[str]:
    urls: set[str] = set()
    generated_scope = {
        (RUN / name).relative_to(ROOT).as_posix()
        for name in (
            "escopo_fontes_canonico.yaml",
            "matriz_fontes_canonicas.csv",
            "inventario_integral.csv",
            "inventory_exclusions.csv",
        )
    }
    for rel in sorted(paths):
        if rel in generated_scope:
            continue
        path = ROOT / rel
        try:
            if path.stat().st_size > 20_000_000:
                continue
            raw = path.read_bytes()
            if b"\x00" in raw:
                continue
            text = raw.decode("utf-8", errors="ignore")
        except OSError:
            continue
        urls.update(value.rstrip(".,);]") for value in URL_RE.findall(text))
    return urls


def write_inventory(tracked: set[str], filesystem: set[str]) -> None:
    path = RUN / "inventario_integral.csv"
    self_rel = path.relative_to(ROOT).as_posix()
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(("chave", "caminho_ou_id", "git", "filesystem", "sha256", "status", "evidencia"))
        for rel in sorted(tracked | filesystem):
            present = rel in filesystem
            digest = "SELF_REFERENTIAL_GIT_TREE" if rel == self_rel else (sha256(ROOT / rel) if present else "")
            status = "OK" if rel in tracked and present else "A_VALIDAR"
            writer.writerow((f"arquivo::{rel}", rel, rel in tracked, present, digest, status, "git ls-tree + filesystem"))


def write_scope(urls: set[str]) -> None:
    scope = RUN / "escopo_fontes_canonico.yaml"
    lines = [
        "schema: rjc-canonical-source-scope-v3",
        "baseline_sha: " + subprocess.check_output(
            ["git", "merge-base", "HEAD", "origin/main"], cwd=ROOT, text=True, encoding="utf-8"
        ).strip(),
        "jurisdicoes:",
        "  - BR",
        *[f"  - {uf}" for uf in UFS],
        "classes_estaduais:",
        *[f"  - {item}" for item in STATE_CLASSES],
        "familias_federais:",
        *[f"  - {item}" for item in FEDERAL_FAMILIES],
        "urls_referenciadas:",
        *[f"  - {url}" for url in sorted(urls)],
    ]
    scope.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def write_matrix(urls: set[str]) -> None:
    path = RUN / "matriz_fontes_canonicas.csv"
    existing_by_key: dict[tuple[str, str], dict[str, str]] = {}
    existing_by_url: dict[str, dict[str, str]] = {}
    if path.exists():
        with path.open(encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                existing_by_key[(row.get("jurisdicao", ""), row.get("classe", ""))] = row
                if row.get("jurisdicao") == "REFERENCIADA" and row.get("url_inicial"):
                    existing_by_url[row["url_inicial"]] = row

    fields = ("jurisdicao", "classe", "url_inicial", "url_final", "dominio", "http_receipt_id", "status_http", "sha256_corpo", "resultado")

    def material_row(jurisdiction: str, source_class: str, url: str = "") -> tuple[str, ...]:
        previous = existing_by_url.get(url) if jurisdiction == "REFERENCIADA" else existing_by_key.get((jurisdiction, source_class))
        if previous:
            return tuple(str(previous.get(field, "")) for field in fields)
        return (jurisdiction, source_class, url, "", "", "", "", "", "A_VALIDAR")

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(fields)
        for uf in UFS:
            for source_class in STATE_CLASSES:
                writer.writerow(material_row(uf, source_class))
        for family in FEDERAL_FAMILIES:
            writer.writerow(material_row("BR", family))
        for index, url in enumerate(sorted(urls), 1):
            previous = existing_by_url.get(url)
            if previous:
                row = {field: str(previous.get(field, "")) for field in fields}
                row["classe"] = f"URL_{index:05d}"
                writer.writerow(tuple(row[field] for field in fields))
            else:
                writer.writerow(material_row("REFERENCIADA", f"URL_{index:05d}", url))


def main() -> int:
    RUN.mkdir(parents=True, exist_ok=True)
    tracked = git_files()
    filesystem = fs_files()
    urls = referenced_urls(tracked | filesystem)
    write_scope(urls)
    write_matrix(urls)
    (RUN / "inventory_exclusions.csv").write_text(
        "chave,caminho,justificativa,sha256,prova_nao_rastreado,prova_nao_servido,prova_nao_referenciado\n",
        encoding="utf-8",
        newline="\n",
    )
    # Inventory is written last so hashes for every other generated artifact
    # reflect their final bytes from this same run.
    write_inventory(tracked, filesystem)
    symmetric = tracked ^ filesystem
    print(f"tracked={len(tracked)} filesystem={len(filesystem)} urls={len(urls)} symmetric_diff={len(symmetric)}")
    return 1 if symmetric else 0


if __name__ == "__main__":
    raise SystemExit(main())
