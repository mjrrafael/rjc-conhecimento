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
    "ncm": ROOT / "data" / "ncm_benefits_index.json",
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
    ncm_index = read_json(FILES["ncm"])
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
    benefits_fail_closed = (
        benefits.get("publication_status") == "BLOQUEADO_SEM_PROVA_MATERIAL"
        and benefit_entries == []
    )
    if not benefit_entries and not benefits_fail_closed:
        errors.append("matriz de beneficios vazia")
    if benefits.get("schema") != "rjc-validated-benefits-crosswalk-v3":
        errors.append("matriz de beneficios precisa estar no schema validado v3")
    required_benefit_keys = {
        "id",
        "jurisdiction",
        "tax",
        "benefit_group",
        "benefit_type",
        "product_or_operation",
        "ncm",
        "cest",
        "cbenef",
        "cst",
        "source_file",
        "official_url",
        "legal_basis",
        "legal_excerpt",
        "validation_status",
        "proof_required",
        "risk",
        "validation_basis",
    }
    for index, item in enumerate(benefit_entries):
        missing = sorted(required_benefit_keys - set(item))
        if missing:
            errors.append(f"beneficio {index} sem campos obrigatorios: {missing}")
        if item.get("validation_status") != "validado":
            errors.append(f"beneficio nao validado publicado: {item.get('id')}")
        joined = json.dumps(item, ensure_ascii=False).lower()
        if "a validar" in joined or "aguardando_revis" in joined:
            errors.append(f"beneficio contem pendencia publica: {item.get('id')}")
        if not item.get("official_url", "").startswith(("http://", "https://")):
            errors.append(f"beneficio sem URL oficial: {item.get('id')}")
        if not item.get("legal_excerpt") or len(item.get("legal_excerpt", "")) < 80:
            errors.append(f"beneficio sem trecho legal suficiente: {item.get('id')}")
        if not any(item.get(key) for key in ("ncm", "cest", "cbenef", "cst", "cclasstrib")) and "Produto ou operação descrito literalmente" in item.get("product_or_operation", ""):
            errors.append(f"beneficio sem codigo nem descricao operacional especifica: {item.get('id')}")

    ncm_rows = ncm_index.get("rows", [])
    if ncm_index.get("schema") != "rjc-ncm-benefits-index-v1":
        errors.append("indice NCM x beneficios precisa estar no schema v1")
    if not ncm_rows:
        errors.append("indice NCM x beneficios vazio")
    required_ncm_keys = {
        "id",
        "ncm",
        "ncm_digits",
        "origin",
        "jurisdiction",
        "tax",
        "benefit_group",
        "benefit_type",
        "conditions",
        "legal_basis",
        "official_url",
        "legal_excerpt",
    }
    for index, item in enumerate(ncm_rows):
        missing = sorted(required_ncm_keys - set(item))
        if missing:
            errors.append(f"linha NCM {index} sem campos obrigatorios: {missing}")
        digits = str(item.get("ncm_digits", ""))
        if len(digits) not in {4, 6, 8} or not digits.isdigit() or digits.startswith("00"):
            errors.append(f"linha NCM com codigo invalido: {item.get('id')} -> {digits}")
        joined = json.dumps(item, ensure_ascii=False).lower()
        if "a validar" in joined or "aguardando_revis" in joined:
            errors.append(f"linha NCM contem pendencia publica: {item.get('id')}")
        if not item.get("official_url", "").startswith(("http://", "https://")):
            errors.append(f"linha NCM sem URL oficial: {item.get('id')}")
        if item.get("origin") == "CONFAZ" and not item.get("official_url", "").startswith("https://www.confaz.fazenda.gov.br/"):
            errors.append(f"linha CONFAZ sem URL oficial CONFAZ: {item.get('id')}")
        if not item.get("legal_excerpt") or len(item.get("legal_excerpt", "")) < 80:
            errors.append(f"linha NCM sem trecho legal suficiente: {item.get('id')}")

    if len(confaz.get("years", [])) != 5:
        errors.append("indice CONFAZ nao cobre exatamente 5 anos")
    families = confaz.get("families", {})
    for family_id in ("convenios", "ajustes", "protocolos"):
        if family_id not in families:
            errors.append(f"familia CONFAZ ausente: {family_id}")
            continue
        if len(families[family_id].get("years", [])) != 5:
            errors.append(f"familia CONFAZ sem 5 anos: {family_id}")
    protocolo_2026 = next(
        (
            year
            for year in families.get("protocolos", {}).get("years", [])
            if year.get("year") == 2026
        ),
        {},
    )
    protocolo_2026_titles = {act.get("title") for act in protocolo_2026.get("acts", [])}
    if protocolo_2026.get("count", 0) < 52:
        errors.append("protocolos CONFAZ 2026 parecem desatualizados: esperado ao menos 52 atos oficiais")
    if "PROTOCOLO ICMS 52/26" not in protocolo_2026_titles:
        errors.append("PROTOCOLO ICMS 52/26 ausente do indice CONFAZ 2026")

    print(f"Requisitos federais auditados: {len(federal)}")
    print(f"Estados auditados: {len(states)}")
    if benefits_fail_closed:
        print("Matriz de beneficios: fail-closed, sem entradas públicas materiais.")
    print(f"Entradas de beneficios auditadas: {len(benefit_entries)}")
    print(f"Linhas NCM x beneficios auditadas: {len(ncm_rows)}")
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
