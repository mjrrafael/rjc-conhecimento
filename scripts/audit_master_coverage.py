#!/usr/bin/env python3
"""Audit the master knowledge indexes used by the portal."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

FILES = {
    "taxonomy": ROOT / "data" / "master_taxonomy.json",
    "coverage": ROOT / "data" / "master_source_coverage.json",
    "benefits": ROOT / "data" / "benefits_crosswalk.json",
    "confaz": ROOT / "data" / "confaz_ultimos_5_anos.json",
}


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    errors: list[str] = []
    for label, path in FILES.items():
        if not path.exists():
            errors.append(f"arquivo mestre ausente: {label} -> {path.relative_to(ROOT)}")
    if errors:
        for error in errors:
            print(error)
        return 1

    taxonomy = read_json(FILES["taxonomy"])
    coverage = read_json(FILES["coverage"])
    benefits = read_json(FILES["benefits"])
    confaz = read_json(FILES["confaz"])

    if taxonomy.get("schema") != "rjc-master-taxonomy-v2":
        errors.append("taxonomia mestre em schema inesperado")
    if len(taxonomy.get("federal_requirements", [])) < 12:
        errors.append("taxonomia federal insuficiente para o plano mestre")
    if len(taxonomy.get("benefit_groups", [])) < 8:
        errors.append("grupos de beneficios insuficientes")

    federal = coverage.get("federal", [])
    states = coverage.get("states", [])
    if len(federal) != len(taxonomy.get("federal_requirements", [])):
        errors.append("cobertura federal nao conversa com a taxonomia")
    if len(states) != 27:
        errors.append("cobertura estadual nao cobre as 27 UFs")
    for item in federal:
        if not item.get("id") or not item.get("status") or not item.get("minimum"):
            errors.append(f"requisito federal incompleto: {item}")
    for item in states:
        if not item.get("uf") or not item.get("status"):
            errors.append(f"estado incompleto na cobertura: {item}")
        if item.get("publish_deep") and item.get("status") == "aguardando_revisao":
            errors.append(f"estado marcado profundo e aguardando revisao ao mesmo tempo: {item.get('uf')}")

    benefit_entries = benefits.get("entries", [])
    if not benefit_entries:
        errors.append("matriz de beneficios vazia")
    required_benefit_keys = {
        "jurisdiction",
        "tax",
        "benefit_group",
        "benefit_type",
        "ncm_cest",
        "source_file",
        "evidence_status",
        "proof_required",
        "risk",
        "validation",
    }
    for index, item in enumerate(benefit_entries):
        missing = sorted(required_benefit_keys - set(item))
        if missing:
            errors.append(f"beneficio {index} sem campos obrigatorios: {missing}")
        if item.get("publish_deep") and item.get("evidence_status") == "aguardando_revisao":
            errors.append(f"beneficio publicado como profundo mas ainda aguardando revisao: {item.get('jurisdiction')} {item.get('benefit_group')}")

    if len(confaz.get("years", [])) != 5:
        errors.append("indice CONFAZ nao cobre exatamente 5 anos")
    families = confaz.get("families", {})
    for family_id in ("convenios", "ajustes", "protocolos"):
        if family_id not in families:
            errors.append(f"familia CONFAZ ausente: {family_id}")
            continue
        if len(families[family_id].get("years", [])) != 5:
            errors.append(f"familia CONFAZ sem 5 anos: {family_id}")

    print(f"Requisitos federais auditados: {len(federal)}")
    print(f"Estados auditados: {len(states)}")
    print(f"Entradas de beneficios auditadas: {len(benefit_entries)}")
    print(f"Familias CONFAZ auditadas: {len(families)}")
    if errors:
        print("Falhas encontradas:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Auditoria mestre concluida sem falhas estruturais.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
