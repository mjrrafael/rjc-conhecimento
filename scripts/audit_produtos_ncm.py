#!/usr/bin/env python3
"""Audit Produto/NCM datasets imported from the Cowork package."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "data" / "produtos-ncm" / "index.json"
CAP10 = ROOT / "data" / "produtos-ncm" / "cap-10.json"
CORPUS = ROOT / "data" / "corpus-local" / "legal_sources_registry.json"
UF_PLAN = ROOT / "data" / "corpus-local" / "uf-sealing-plan.json"
PROJECT_MANIFEST = ROOT / "data" / "cowork" / "portal-package-manifest.json"
REFORMA_RESELO = ROOT / "data" / "reforma-tributaria" / "reselo-lc214-lc224-lc227.ndjson"
HTML = ROOT / "produto.html"
SEARCH_FULL = ROOT / "assets" / "portal-search-full.json"
LLMS = ROOT / "llms.txt"

SHA_RE = re.compile(r"^[0-9a-f]{64}$")
ABSOLUTE_DRIVE_RE = re.compile(r"\b[A-Z]:[\\/]", re.I)
LOCAL_ENV_RE = re.compile(r"(Outros computadores|LOCALHOST|#administra)", re.I)


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def load_ndjson(path: Path) -> list[dict]:
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def validate_no_local_paths(name: str, payload: object) -> list[str]:
    serialized = json.dumps(payload, ensure_ascii=False) if not isinstance(payload, str) else payload
    errors: list[str] = []
    if ABSOLUTE_DRIVE_RE.search(serialized):
        errors.append(f"{name} leaks an absolute local drive path")
    if LOCAL_ENV_RE.search(serialized):
        errors.append(f"{name} leaks local environment markers")
    return errors


def validate_source(source: dict) -> list[str]:
    errors: list[str] = []
    source_id = str(source.get("id", "<sem-id>"))
    if not str(source.get("url", "")).startswith("https://www.planalto.gov.br/"):
        errors.append(f"{source_id}: official source must be a Planalto HTTPS URL")
    if source.get("http_status") != 200:
        errors.append(f"{source_id}: live official URL must resolve HTTP 200")
    for field in ("snapshot_sha256", "live_sha256"):
        value = str(source.get(field) or "")
        if not SHA_RE.match(value):
            errors.append(f"{source_id}: missing/invalid {field}")
    if source.get("url_resolve") is not True:
        errors.append(f"{source_id}: url_resolve must be true")
    return errors


def validate_product(product: dict, source_ids: set[str]) -> list[str]:
    errors: list[str] = []
    product_id = str(product.get("id", "<sem-id>"))
    if product.get("publishable") is True:
        errors.append(f"{product_id}: imported seed cannot be publishable as a benefit card")
    if not str(product.get("status", "")).startswith("A_VALIDAR"):
        errors.append(f"{product_id}: product seed must remain A_VALIDAR until full validity envelope is extracted")
    if not product.get("why_not_green"):
        errors.append(f"{product_id}: missing why_not_green safeguards")
    search_text = str(product.get("search_text", ""))
    for token in ("arroz", "1006", "100620", "100630", "10064000"):
        if token not in search_text:
            errors.append(f"{product_id}: search_text missing {token}")
    for ncm in product.get("ncm", []):
        digits = re.sub(r"\D", "", str(ncm.get("digitos") or ncm.get("codigo") or ""))
        if len(digits) not in {6, 8}:
            errors.append(f"{product_id}: invalid NCM digits {digits}")
        if not str(ncm.get("status", "")).startswith("A_VALIDAR"):
            errors.append(f"{product_id}: NCM {digits} cannot be green in the seed")
    for reselo in product.get("reselos", []):
        reselo_id = str(reselo.get("id", "<sem-id>"))
        if reselo.get("publishable") is True:
            errors.append(f"{reselo_id}: reselo seed cannot be publishable")
        missing_dates = [
            field
            for field in ("publicacao", "inicio_vigencia", "inicio_eficacia", "fim_vigencia")
            if str(reselo.get(field, "")).strip() in {"", "A_VALIDAR"}
        ]
        if missing_dates and str(reselo.get("status", "")).lower() in {"verificado", "vigente", "publishable"}:
            errors.append(f"{reselo_id}: green status with incomplete temporal envelope")
        for source_id in reselo.get("official_source_ids", []):
            if source_id not in source_ids:
                errors.append(f"{reselo_id}: unknown source id {source_id}")
        if not reselo.get("transicao_rt"):
            errors.append(f"{reselo_id}: missing transicao_rt")
    return errors


def validate_corpus(corpus: dict) -> list[str]:
    errors: list[str] = []
    if corpus.get("selo_maximo_atual") != "AMARELO_CORPUS_LOCAL":
        errors.append("corpus registry must be capped at AMARELO_CORPUS_LOCAL")
    entries = corpus.get("entries", [])
    if not isinstance(entries, list) or not entries:
        errors.append("corpus registry has no entries")
    return errors


def validate_uf_plan(plan: dict) -> list[str]:
    errors: list[str] = []
    for row in plan.get("ufs", []):
        uf = str(row.get("uf", ""))
        if row.get("publicavel_verde") is True:
            errors.append(f"{uf}: UF plan cannot be green/publishable from local corpus")
        if uf != "GO" and row.get("cbenef_status") != "A_VALIDAR_SEFAZ_VIVA":
            errors.append(f"{uf}: non-GO cBenef must remain A_VALIDAR_SEFAZ_VIVA")
        if uf == "GO" and "REVALIDAR_SEFAZ" not in str(row.get("cbenef_status", "")):
            errors.append("GO: cBenef local snapshot must still require SEFAZ revalidation")
    return errors


def validate_rendered_outputs() -> list[str]:
    errors: list[str] = []
    if not HTML.exists():
        errors.append("produto.html missing")
        return errors
    html = HTML.read_text(encoding="utf-8", errors="ignore")
    for token in ("data-product-ncm-explorer", "produto-arroz-ncm-1006", "A_VALIDAR", "1006.20", "1006.40.00"):
        if token not in html:
            errors.append(f"produto.html missing {token}")
    search = load_json(SEARCH_FULL) if SEARCH_FULL.exists() else []
    if not any(isinstance(item, dict) and item.get("url") == "produto.html#produto-arroz-ncm-1006" for item in search):
        errors.append("Produto/NCM entry missing from full search")
    llms = LLMS.read_text(encoding="utf-8", errors="ignore") if LLMS.exists() else ""
    for token in ("Produto/NCM", "data/produtos-ncm/index.json", "data/corpus-local/legal_sources_registry.json"):
        if token not in llms:
            errors.append(f"llms.txt missing {token}")
    return errors


def validate_payloads(index: dict, cap10: dict, corpus: dict, uf_plan: dict) -> list[str]:
    errors: list[str] = []
    if index.get("schema") != "rjc-produto-ncm-v1":
        errors.append("invalid product index schema")
    if cap10.get("schema") != "rjc-produto-ncm-chapter-v1":
        errors.append("invalid chapter schema")
    sources = index.get("official_sources", [])
    if len(sources) < 4:
        errors.append("product index must carry all four official source records")
    source_ids = {str(source.get("id")) for source in sources if isinstance(source, dict)}
    for source in sources:
        if isinstance(source, dict):
            errors.extend(validate_source(source))
    products = cap10.get("products", [])
    if not products:
        errors.append("chapter has no products")
    for product in products:
        if isinstance(product, dict):
            errors.extend(validate_product(product, source_ids))
    errors.extend(validate_corpus(corpus))
    errors.extend(validate_uf_plan(uf_plan))
    return errors


def main() -> int:
    errors: list[str] = []
    required = [INDEX, CAP10, CORPUS, UF_PLAN, PROJECT_MANIFEST, REFORMA_RESELO]
    for path in required:
        if not path.exists():
            errors.append(f"{path.relative_to(ROOT)} missing")
    if not errors:
        index = load_json(INDEX)
        cap10 = load_json(CAP10)
        corpus = load_json(CORPUS)
        uf_plan = load_json(UF_PLAN)
        project_manifest = load_json(PROJECT_MANIFEST)
        reforma_rows = load_ndjson(REFORMA_RESELO)
        if all(isinstance(obj, dict) for obj in (index, cap10, corpus, uf_plan)):
            errors.extend(validate_payloads(index, cap10, corpus, uf_plan))
        else:
            errors.append("one or more product/corpus payloads are not JSON objects")
        payloads = {
            "produto index": index,
            "produto cap-10": cap10,
            "corpus registry": corpus,
            "uf sealing plan": uf_plan,
            "cowork manifest": project_manifest,
            "reforma reselo": reforma_rows,
        }
        for name, payload in payloads.items():
            errors.extend(validate_no_local_paths(name, payload))
    errors.extend(validate_rendered_outputs())
    if errors:
        print("Falhas na auditoria Produto/NCM:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("OK: Produto/NCM, re-selo federal, corpus local amarelo e plano cBenef A_VALIDAR estao coerentes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
