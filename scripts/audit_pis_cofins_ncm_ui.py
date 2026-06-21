#!/usr/bin/env python3
"""Audit the human and LLM-facing PIS/Cofins NCM publication surfaces."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NDJSON = ROOT / "data" / "pis-cofins" / "ncm.ndjson"
HTML = ROOT / "federal" / "legislacao" / "pis-cofins" / "ncm.html"
LANDING = ROOT / "federal" / "pis-cofins-ncm.html"
BENEFITS_NCM = ROOT / "beneficios" / "ncm.html"
SEARCH = ROOT / "assets" / "portal-search-full.json"
JS = ROOT / "assets" / "portal-tributario.js"
CSS = ROOT / "assets" / "portal-tributario.css"


def load_ndjson(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> int:
    errors: list[str] = []
    rows = [row for row in load_ndjson(NDJSON) if row.get("publishable") is True]
    html = HTML.read_text(encoding="utf-8", errors="ignore")
    landing = LANDING.read_text(encoding="utf-8", errors="ignore")
    benefits_ncm = BENEFITS_NCM.read_text(encoding="utf-8", errors="ignore")
    js = JS.read_text(encoding="utf-8", errors="ignore")
    css = CSS.read_text(encoding="utf-8", errors="ignore")
    search_entries = json.loads(SEARCH.read_text(encoding="utf-8"))
    search_urls = {str(entry.get("url", "")) for entry in search_entries if isinstance(entry, dict)}

    required_html = [
        'id="consulta-pis-cofins-ncm"',
        'data-pis-ncm-explorer',
        'id="pisNcmSearch"',
        'data-pis-filter="tratamento"',
        'data-pis-filter="setor"',
        'data-pis-filter="status"',
        'data-pis-filter="source"',
        'data-pis-count',
        'pis-ncm-card-grid',
        'pis-ncm-record-summary',
        'pis-ncm-guardrail',
        'pis-ncm-audit-table',
        'Como validar',
        'Não usar sem',
    ]
    for token in required_html:
        if token not in html:
            errors.append(f"missing UI token in PIS/Cofins NCM page: {token}")

    if "bindPisNcmExplorer" not in js or "[data-pis-ncm-explorer]" not in js:
        errors.append("local PIS/Cofins NCM search binder is missing from portal JS")
    required_css = [".pis-ncm-card-grid", ".pis-ncm-query", ".pis-ncm-entry-panel", ".pis-ncm-audit-table"]
    for token in required_css:
        if token not in css:
            errors.append(f"PIS/Cofins NCM responsive styles are missing: {token}")
    if ".pis-ncm-card-grid" not in css or ".pis-ncm-query" not in css:
        errors.append("PIS/Cofins NCM responsive styles are missing")
    if "legislacao/pis-cofins/ncm.html" not in landing:
        errors.append("landing page does not link to the NCM table")
    if "Tabela completa por NCM" in landing:
        errors.append("landing page still presents the human route as a complete table")

    forbidden_human_tokens = [
        "Linhas pesquisaveis",
        "Linhas pesquisáveis",
        "abrir na tabela",
    ]
    for token in forbidden_human_tokens:
        if token.lower() in html.lower():
            errors.append(f"old table-first human wording leaked into PIS/Cofins NCM page: {token}")

    explorer_pos = html.find('id="consulta-pis-cofins-ncm"')
    cards_pos = html.find('pis-ncm-card-grid')
    audit_pos = html.find('pis-ncm-audit-table')
    table_pos = html.find('ncm-benefits-table')
    if not (0 <= explorer_pos < cards_pos < audit_pos < table_pos):
        errors.append("PIS/Cofins NCM page does not place guided search/cards before the technical table")
    if re.search(r'<details[^>]*class="[^"]*pis-ncm-table-details[^"]*"[^>]*\bopen\b', html, re.I):
        errors.append("PIS/Cofins NCM technical table is open by default")
    if '<details class="pis-ncm-table-details">' not in html:
        errors.append("PIS/Cofins NCM technical table is not wrapped in closed details")
    if '<details class="ncm-audit-table-details">' not in benefits_ncm:
        errors.append("generic NCM benefits table is not wrapped in closed details")
    if benefits_ncm.find("ncm-benefits-table") < benefits_ncm.find("ncm-audit-table-details"):
        errors.append("generic NCM benefits table appears before the closed audit details wrapper")

    card_count = html.count('data-pis-result="card"')
    row_count = html.count('data-pis-result="row"')
    if card_count != len(rows):
        errors.append(f"HTML card count {card_count} differs from NDJSON rows {len(rows)}")
    if row_count != len(rows):
        errors.append(f"HTML table row count {row_count} differs from NDJSON rows {len(rows)}")

    for row in rows:
        row_id = str(row.get("id", ""))
        if f'id="card-{row_id}"' not in html:
            errors.append(f"{row_id}: missing human card")
        if f'id="{row_id}"' not in html:
            errors.append(f"{row_id}: missing technical table row")
        if not any(url.endswith(f"#{row_id}") for url in search_urls):
            errors.append(f"{row_id}: missing structured full-search entry")
        if re.search(rf'id="q-{re.escape(row_id)}"', html):
            errors.append(f"{row_id}: quarantine-like id leaked into HTML")

    if errors:
        print("\n".join(errors))
        return 1
    print(f"OK: PIS/Cofins NCM UI, local search hooks and LLM search entries cover {len(rows)} rows.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
