#!/usr/bin/env python3
"""Fail-closed readiness gate for the Portal RJC v3 publication contract."""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "auditoria" / "execucoes" / "monitor-v3-2026-07-12"
UFS = set("AC AL AM AP BA CE DF ES GO MA MG MS MT PA PB PE PI PR RJ RN RO RR RS SC SE SP TO".split())
STATE_CLASSES = {"SEFAZ_LEGISLACAO", "DOE", "ASSEMBLEIA_LEGISLATIVA"}
FEDERAL_CLASSES = {
    "PLANALTO", "DOU_IMPRENSA_NACIONAL", "RFB_SIJUT_NORMAS", "PGFN",
    "CONFAZ_CONVENIOS", "CONFAZ_PROTOCOLOS", "CONFAZ_AJUSTES_SINIEF",
    "CONFAZ_ATOS_COTEPE", "CGIBS_PORTAL_NACIONAL_TCS", "SENADO", "STF", "STJ", "CARF",
}
MANDATORY_ARTIFACTS = {
    "escopo_fontes_canonico.yaml", "matriz_fontes_canonicas.csv", "inventario_integral.csv",
    "inventory_exclusions.csv", "subagents.json", "subagents_platform_receipts.json",
    "http_platform_receipts.json", "ledger_verificacao.csv", "fontes_lidas.csv",
    "achados_e_pendencias.md", "revisao_adversarial.md", "conformidade.json",
    "gate_mutation_results.json", "gate_invariant_matrix.csv", "manifesto_diff.csv",
}
NEW_GATES = {
    "audit_field_provenance.py", "audit_no_synthetic_legal_dates.py",
    "audit_verification_receipts.py", "audit_http_platform_receipts.py",
    "audit_link_receipts.py", "audit_internalization_evidence.py",
    "audit_full_content_coverage.py", "audit_canonical_source_scope.py",
    "audit_public_set_algebra.py", "audit_quarantine_fingerprints.py",
    "audit_subagent_independence.py", "audit_publication.py", "audit_public_http_hashes.py",
}


def check_matrix(errors: list[str]) -> None:
    path = RUN / "matriz_fontes_canonicas.csv"
    if not path.exists():
        errors.append("matriz_fontes_canonicas.csv ausente")
        return
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    state = {(row["jurisdicao"], row["classe"]) for row in rows if row["jurisdicao"] in UFS}
    expected = {(uf, source_class) for uf in UFS for source_class in STATE_CLASSES}
    if state != expected:
        errors.append(f"matriz estadual divergente: faltam={len(expected - state)} sobram={len(state - expected)}")
    federal = {row["classe"] for row in rows if row["jurisdicao"] == "BR"}
    if federal != FEDERAL_CLASSES:
        errors.append(f"matriz federal divergente: faltam={sorted(FEDERAL_CLASSES - federal)}")
    required = ("url_inicial", "url_final", "dominio", "http_receipt_id", "status_http", "sha256_corpo")
    incomplete = [row for row in rows if row["jurisdicao"] in UFS | {"BR"} and any(not row.get(field) for field in required)]
    if incomplete:
        errors.append(f"{len(incomplete)} linhas canônicas sem URL/recibo/hash material")


def check_generator(errors: list[str]) -> None:
    raw = (ROOT / "scripts" / "validated_benefits.py").read_text(encoding="utf-8")
    forbidden = {
        'iso_date(source.get("captured_on")) or TODAY': "data jurídica derivada de captura/hoje",
        '"internalizado_uf": len(': "internalização presumida por sigla",
        '"verificado_em": TODAY': "revalidação em massa pela data atual",
        '"publishable": True': "publicação incondicional",
        'source.get("validity_start", source.get("captured_on"': "vigência derivada da captura",
    }
    for needle, label in forbidden.items():
        if needle in raw:
            errors.append(label)
    for name in ("material_publication_blockers", "field_provenance", "independent_http_receipt_ids", "verification_receipt_id"):
        if name not in raw:
            errors.append(f"gerador sem controle fail-closed: {name}")


def check_public(errors: list[str]) -> None:
    public = ROOT / "public"
    expected = {"index.html", "404.html", "robots.txt", "llms.txt"}
    actual = {path.relative_to(public).as_posix() for path in public.rglob("*") if path.is_file()} if public.exists() else set()
    if actual != expected:
        errors.append(f"artefato público fora da allowlist segura: {sorted(actual ^ expected)}")
    for rel in actual:
        raw = (public / rel).read_text(encoding="utf-8", errors="ignore")
        if "A_VALIDAR" in raw or "publishable" in raw:
            errors.append(f"estado indevido no artefato público: {rel}")
    if (ROOT / ".nojekyll").exists():
        errors.append(".nojekyll mantém o acervo bruto exposto no Pages legado")
    config = ROOT / "_config.yml"
    if not config.exists():
        errors.append("_config.yml de quarentena integral ausente")
        return
    excluded = {
        line.strip()[2:].strip()
        for line in config.read_text(encoding="utf-8").splitlines()
        if line.strip().startswith("- ")
    }
    allowed = {"_config.yml", "index.html", "404.html", "robots.txt", "llms.txt"}
    top_level = {path.name for path in ROOT.iterdir() if path.name != ".git"}
    leaked = top_level - excluded - allowed
    if leaked:
        errors.append("raízes não excluídas do Pages legado: " + ", ".join(sorted(leaked)))


def main() -> int:
    errors: list[str] = []
    missing = sorted(name for name in MANDATORY_ARTIFACTS if not (RUN / name).exists())
    if missing:
        errors.append("artefatos obrigatórios ausentes: " + ", ".join(missing))
    missing_gates = sorted(name for name in NEW_GATES if not (ROOT / "scripts" / name).exists())
    if missing_gates:
        errors.append("hard gates ausentes: " + ", ".join(missing_gates))
    roots = list((RUN / "trust_roots").glob("*.attestation.json")) if (RUN / "trust_roots").exists() else []
    if len(roots) < 2:
        errors.append("duas raízes de confiança preexistentes não comprovadas")
    check_matrix(errors)
    check_generator(errors)
    check_public(errors)
    if errors:
        print("PORTAL V3 NÃO PRONTO:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Portal v3 pronto para os gates detalhados.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
