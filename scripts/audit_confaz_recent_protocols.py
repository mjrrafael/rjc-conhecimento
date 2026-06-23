#!/usr/bin/env python3
"""Adversarial check for recent CONFAZ protocol capture and search exposure."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TARGET_TITLE = "PROTOCOLO ICMS 52/26"
TARGET_URL = "https://www.confaz.fazenda.gov.br/legislacao/protocolos/2026/protocolo-icms-52-26"


def read_text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8", errors="ignore")


def load_json(rel: str) -> object:
    return json.loads(read_text(rel))


def main() -> int:
    errors: list[str] = []
    confaz = load_json("data/confaz_ultimos_5_anos.json")
    protocols = confaz.get("families", {}).get("protocolos", {}) if isinstance(confaz, dict) else {}
    year_2026 = next((year for year in protocols.get("years", []) if year.get("year") == 2026), {})
    acts = year_2026.get("acts", [])
    if year_2026.get("count", 0) < 52:
        errors.append("protocolos 2026 abaixo do marcador oficial 52/26")
    if not any(act.get("title") == TARGET_TITLE and act.get("url") == TARGET_URL for act in acts):
        errors.append(f"{TARGET_TITLE} ausente do JSON CONFAZ com URL oficial")

    confaz_html = read_text("confaz/ultimos-5-anos.html")
    if TARGET_TITLE not in confaz_html or TARGET_URL not in confaz_html:
        errors.append(f"{TARGET_TITLE} nao aparece no HTML CONFAZ com URL oficial")

    search_js = read_text("assets/portal-search.js")
    if TARGET_TITLE not in search_js:
        errors.append(f"{TARGET_TITLE} ausente da busca leve")

    full_search = load_json("assets/portal-search-full.json")
    full_hits = [
        item
        for item in full_search
        if isinstance(item, dict) and TARGET_TITLE in str(item.get("title", ""))
    ]
    if not full_hits:
        errors.append(f"{TARGET_TITLE} ausente da busca integral")
    for item in full_hits:
        if item.get("kind") != "Ato CONFAZ":
            errors.append(f"{TARGET_TITLE} com kind inesperado na busca integral: {item.get('kind')}")
        if not str(item.get("url", "")).startswith("confaz/ultimos-5-anos.html#protocolos"):
            errors.append(f"{TARGET_TITLE} deveria apontar para pagina CONFAZ interna, nao {item.get('url')}")

    freshness = load_json("assets/build-freshness.json")
    artifacts = freshness.get("artifacts", {}) if isinstance(freshness, dict) else {}
    if "data/confaz_ultimos_5_anos.json" not in artifacts:
        errors.append("build-freshness sem checksum do indice CONFAZ")

    if errors:
        print("Falhas no passe adversarial CONFAZ:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Passe adversarial CONFAZ OK: {TARGET_TITLE} em JSON, HTML, busca e frescor.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
