#!/usr/bin/env python3
"""Check whether HTML, manifest and search artifacts expose a coherent build."""

from __future__ import annotations

from audit_v2_helpers import (
    BENEFIT_INDEX,
    BUILD_FRESHNESS,
    LLM_MANIFEST,
    LLMS_TXT,
    ROOT,
    SEARCH_FULL,
    SEARCH_JS,
    benefit_entries,
    canonical_sha256,
    load_json,
    read_text,
    stale_date_hits,
)


def main() -> int:
    errors: list[str] = []
    manifest = load_json(LLM_MANIFEST, [])
    if not isinstance(manifest, list) or not manifest:
        errors.append("assets/llm-manifest.json ausente ou vazio")
    if not read_text(LLMS_TXT):
        errors.append("llms.txt ausente ou vazio")
    if not read_text(SEARCH_JS):
        errors.append("assets/portal-search.js ausente ou vazio")
    full_search = load_json(SEARCH_FULL, [])
    if not isinstance(full_search, list) or not full_search:
        errors.append("assets/portal-search-full.json ausente ou vazio")
    if not BENEFIT_INDEX.exists():
        errors.append("beneficios/index.html ausente")
    else:
        html_mtime = BENEFIT_INDEX.stat().st_mtime
        for path in (LLM_MANIFEST, LLMS_TXT, SEARCH_JS, SEARCH_FULL):
            if path.exists() and path.stat().st_mtime + 1 < html_mtime:
                errors.append(f"{path.relative_to(path.parents[1])} mais antigo que beneficios/index.html")
    stale = stale_date_hits()
    if stale:
        errors.extend(stale[:20])
    if benefit_entries() and isinstance(full_search, list):
        sample = benefit_entries()[0]
        sample_url = f"beneficios/index.html#{sample.get('id', '')}"
        if not any(item.get("url") == sample_url for item in full_search if isinstance(item, dict)):
            errors.append(f"benefício publicado ausente da busca integral: {sample_url}")
    freshness = load_json(BUILD_FRESHNESS, {})
    artifacts = freshness.get("artifacts", {}) if isinstance(freshness, dict) else {}
    if not artifacts:
        errors.append("assets/build-freshness.json ausente ou sem artefatos")
    for rel in (
        "beneficios/index.html",
        "llms.txt",
        "assets/llm-manifest.json",
        "assets/portal-search.js",
        "assets/portal-search-full.json",
        "assets/portal-tributario.js",
        "data/benefits_crosswalk.json",
        "data/ncm_benefits_index.json",
        "produto.html",
        "data/produtos-ncm/index.json",
        "data/produtos-ncm/cap-10.json",
        "data/corpus-local/legal_sources_registry.json",
        "data/corpus-local/uf-sealing-plan.json",
        "data/reforma-tributaria/reselo-lc214-lc224-lc227.ndjson",
    ):
        path = ROOT / rel
        expected = artifacts.get(rel, {}) if isinstance(artifacts, dict) else {}
        if not path.exists():
            errors.append(f"{rel} ausente")
            continue
        if expected.get("sha256") != canonical_sha256(path):
            errors.append(f"{rel} diverge do checksum registrado em assets/build-freshness.json")
    if errors:
        print("Falhas de frescor/coerência de índices:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Índices e HTML aparentam ter sido regenerados no mesmo build.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
