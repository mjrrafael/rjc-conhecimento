#!/usr/bin/env python3
"""Audit the complete fail-closed Pages projection for the quarantined portal."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / "_site"
RUN = ROOT / "auditoria" / "execucoes" / "monitor-v3-2026-07-12"
ALLOWED = {"index.html", "404.html", "robots.txt", "llms.txt"}


def canonical_sha(path: Path) -> str:
    raw = path.read_bytes()
    if b"\x00" not in raw:
        raw = raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(raw).hexdigest()


def audit_site(errors: list[str]) -> None:
    files = {path.relative_to(SITE).as_posix() for path in SITE.rglob("*") if path.is_file()}
    if files != ALLOWED:
        errors.append(f"projeção Pages divergente: faltam={sorted(ALLOWED-files)} sobram={sorted(files-ALLOWED)}")
    joined = "\n".join((SITE / rel).read_text(encoding="utf-8", errors="ignore") for rel in sorted(files))
    forbidden = re.compile(r"\b(publishable|A_VALIDAR|verificado_em|field_provenance|cClassTrib|cBenef|NCM\s*\d|art\.\s*\d|lei\s+n[ºo])\b", re.I)
    if forbidden.search(joined):
        errors.append("artefato seguro contém campo ou fato jurídico")
    if "Disallow: /" not in (SITE / "robots.txt").read_text(encoding="utf-8"):
        errors.append("robots.txt não bloqueia indexação integral")
    for rel in ("index.html", "404.html"):
        raw = (SITE / rel).read_text(encoding="utf-8")
        if "noindex,nofollow,noarchive" not in raw:
            errors.append(f"{rel} sem meta robots fail-closed")


def audit_generator(errors: list[str]) -> None:
    raw = (ROOT / "scripts" / "validated_benefits.py").read_text(encoding="utf-8")
    forbidden = {
        'iso_date(source.get("captured_on")) or TODAY': "data jurídica sintética",
        '"internalizado_uf": len(': "internalização presumida por sigla",
        '"verificado_em": TODAY': "verificação renovada em massa",
        '"publishable": True': "publicação incondicional",
        'source.get("validity_start", source.get("captured_on"': "vigência derivada da captura",
    }
    for needle, label in forbidden.items():
        if needle in raw:
            errors.append(label)
    for required in ("material_publication_blockers", "field_provenance", "independent_http_receipt_ids", "verification_receipt_id"):
        if required not in raw:
            errors.append(f"controle fail-closed ausente: {required}")


def audit_inventory(errors: list[str]) -> None:
    path = RUN / "inventario_integral.csv"
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    fs = {p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*") if p.is_file() and ".git" not in p.parts and "_site" not in p.parts}
    inv = {row["caminho_ou_id"] for row in rows}
    if fs != inv:
        errors.append(f"inventário divergente: faltam={len(fs-inv)} sobram={len(inv-fs)}")
    for row in rows:
        rel = row["caminho_ou_id"]
        if row["sha256"] == "SELF_REFERENTIAL_GIT_TREE":
            continue
        target = ROOT / rel
        if target.is_file() and row["sha256"] != canonical_sha(target):
            errors.append(f"hash divergente: {rel}")
            if len(errors) > 20:
                break


def audit_scope(errors: list[str]) -> None:
    rows = list(csv.DictReader((RUN / "matriz_fontes_canonicas.csv").open(encoding="utf-8")))
    ufs = set("AC AL AM AP BA CE DF ES GO MA MG MS MT PA PB PE PI PR RJ RN RO RR RS SC SE SP TO".split())
    state_classes = {"SEFAZ_LEGISLACAO", "DOE", "ASSEMBLEIA_LEGISLATIVA"}
    state = {(row["jurisdicao"], row["classe"]) for row in rows if row["jurisdicao"] in ufs}
    expected = {(uf, cls) for uf in ufs for cls in state_classes}
    federal = [row for row in rows if row["jurisdicao"] == "BR"]
    if state != expected or len(federal) != 13:
        errors.append("matriz canônica não contém 81 linhas estaduais e 13 federais")


def audit_quarantine(errors: list[str]) -> None:
    quarantine = ROOT / "data" / "benefits_quarantine.json"
    if not quarantine.exists():
        return
    payload = json.loads(quarantine.read_text(encoding="utf-8"))
    site_text = " ".join((SITE / rel).read_text(encoding="utf-8", errors="ignore") for rel in ALLOWED)
    for item in payload.get("entries", []):
        item_id = str(item.get("id", ""))
        if item_id and item_id in site_text:
            errors.append(f"ID de quarentena vazou no Pages: {item_id}")
            break


def main() -> int:
    errors: list[str] = []
    audit_site(errors)
    audit_generator(errors)
    audit_inventory(errors)
    audit_scope(errors)
    audit_quarantine(errors)
    if errors:
        print("Falhas na projeção segura:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Projeção Pages integralmente auditada: 4 arquivos seguros; corpus e quarentena fora do artefato.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
