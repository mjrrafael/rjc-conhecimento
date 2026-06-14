#!/usr/bin/env python3
"""Audit public benefit cards and LLM-facing benefit indexes.

The goal is not to decide tax merit. It blocks editorial/AI noise from being
published as if it were a validated benefit: serialized lists, page markers,
low-confidence extractions, missing scope and quarantined records in public data.
"""

from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BENEFITS = ROOT / "data" / "benefits_crosswalk.json"
QUARANTINE = ROOT / "data" / "benefits_quarantine.json"
SEARCH_FULL = ROOT / "assets" / "portal-search-full.json"
BENEFIT_PAGES = [
    ROOT / "beneficios" / "index.html",
    ROOT / "beneficios" / "setores.html",
    ROOT / "beneficios" / "uf.html",
    ROOT / "beneficios" / "reforma.html",
    ROOT / "beneficios" / "compensacao-icms.html",
    ROOT / "beneficios" / "cesta-basica.html",
    ROOT / "beneficios" / "regimes-diferenciados.html",
    ROOT / "beneficios" / "documentos-de-prova.html",
    ROOT / "beneficios" / "ncm.html",
]

NOISE_RE = re.compile(
    r"\[\]\s*\[\]|\[\s*(?:&#x27;|')|(?:&#x27;|')\s*,\s*(?:&#x27;|')|(?:=+\s*)?(?:PÁGINA|PAGINA|PÃ.?GINA)\s+\d+|�",
    re.I,
)
FORBIDDEN_CESTA_RE = re.compile(
    r"\b(diesel|g[aá]s natural|combust[ií]vel|combustiveis|energia|querosene|biodiesel|biocombust|etanol|AEHC|fotovoltaica|hidrel[eé]trica|PCH|metanol)\b",
    re.I,
)
SUSPECT_PUBLIC_RE = re.compile(
    r"\b(auto de infra[cç][aã]o|penalidade|multa|cadastro fiscal|gia-st|obriga[cç][aã]o acess[oó]ria)\b",
    re.I,
)
BENEFIT_EFFECT_RE = re.compile(
    r"\b(isen[cç][aã]o|redu[cç][aã]o de base|cr[eé]dito (?:presumido|outorgado)|diferimento|suspens[aã]o|al[ií]quota zero|n[aã]o incid[eê]ncia|imunidade|cbenef|cst|cclasstrib|ccredpres)\b",
    re.I,
)


class BenefitCardParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.cards = 0
        self.search_values: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_map = {name.lower(): value or "" for name, value in attrs}
        classes = attrs_map.get("class", "")
        if tag.lower() == "article" and "benefit-cross-card" in classes:
            self.cards += 1
            self.search_values.append(attrs_map.get("data-search", ""))


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def audit_public_benefits(errors: list[str]) -> None:
    if not BENEFITS.exists():
        errors.append("data/benefits_crosswalk.json ausente")
        return
    payload = read_json(BENEFITS)
    if payload.get("quarantine"):
        errors.append("matriz publica ainda contem bloco quarantine")
    entries = payload.get("entries", [])
    if not entries:
        errors.append("matriz publica de beneficios ficou vazia")
    required = {
        "id",
        "official_url",
        "legal_basis",
        "legal_excerpt",
        "scope_summary",
        "goods_or_services",
        "validity_status",
        "classification_confidence",
        "validation_status",
        "publishable",
    }
    for index, item in enumerate(entries):
        missing = sorted(required - set(item))
        if missing:
            errors.append(f"beneficio publico {index} sem campos saneados: {missing}")
        item_id = item.get("id", f"#{index}")
        if item.get("validation_status") != "validado":
            errors.append(f"beneficio publico nao validado: {item_id}")
        if item.get("publishable") is not True:
            errors.append(f"beneficio publico sem publishable=true: {item_id}")
        if item.get("classification_confidence") == "baixa":
            errors.append(f"beneficio publico com baixa confianca: {item_id}")
        if not str(item.get("scope_summary", "")).strip():
            errors.append(f"beneficio publico sem escopo publicado: {item_id}")
        if not str(item.get("official_url", "")).startswith(("http://", "https://")):
            errors.append(f"beneficio publico sem URL oficial: {item_id}")
        joined = json.dumps(item, ensure_ascii=False)
        if NOISE_RE.search(joined):
            errors.append(f"beneficio publico com ruido editorial: {item_id}")
        if SUSPECT_PUBLIC_RE.search(joined) and not BENEFIT_EFFECT_RE.search(joined):
            errors.append(f"beneficio publico parece obrigacao/penalidade sem efeito favorecido: {item_id}")


def audit_quarantine(errors: list[str]) -> None:
    if not QUARANTINE.exists():
        errors.append("data/benefits_quarantine.json ausente")
        return
    payload = read_json(QUARANTINE)
    if payload.get("schema") != "rjc-benefits-quarantine-v1":
        errors.append("quarentena de beneficios em schema inesperado")
    for index, item in enumerate(payload.get("entries", [])):
        if item.get("validation_status") != "a_validar":
            errors.append(f"quarentena {index} sem status a_validar")
        if not item.get("quarantine_reasons"):
            errors.append(f"quarentena {index} sem motivo")
        if not str(item.get("official_url", "")).startswith(("http://", "https://")):
            errors.append(f"quarentena {index} sem URL oficial")


def audit_public_files(errors: list[str]) -> None:
    for path in BENEFIT_PAGES:
        if not path.exists():
            errors.append(f"pagina de beneficios ausente: {path.relative_to(ROOT)}")
            continue
        raw = path.read_text(encoding="utf-8", errors="ignore")
        if NOISE_RE.search(raw):
            errors.append(f"pagina de beneficios com ruido editorial: {path.relative_to(ROOT)}")
        parser = BenefitCardParser()
        parser.feed(raw)
        if path.name != "ncm.html" and parser.cards and "Escopo publicado:" not in raw:
            errors.append(f"cards sem rotulo de escopo publicado: {path.relative_to(ROOT)}")
        for value in parser.search_values:
            if NOISE_RE.search(value):
                errors.append(f"data-search ruidoso em {path.relative_to(ROOT)}")
                break
        if path.name == "cesta-basica.html" and FORBIDDEN_CESTA_RE.search(raw):
            errors.append("cesta-basica.html contem energia/combustivel em card publico")
    if SEARCH_FULL.exists():
        raw = SEARCH_FULL.read_text(encoding="utf-8", errors="ignore")
        if NOISE_RE.search(raw):
            errors.append("assets/portal-search-full.json contem ruido editorial")


def main() -> int:
    errors: list[str] = []
    audit_public_benefits(errors)
    audit_quarantine(errors)
    audit_public_files(errors)
    if errors:
        print("Falhas na auditoria de cards de beneficios:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Auditoria de cards de beneficios concluida sem falhas.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
