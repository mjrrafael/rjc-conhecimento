#!/usr/bin/env python3
"""Property-directed mutants for the fail-closed Pages projection gate."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

import audit_safe_pages_projection as gate


def load_items(rel: str, collection: str) -> list[dict]:
    return json.loads((gate.ROOT / rel).read_text(encoding="utf-8"))[collection]


def legal_shingle(item: dict) -> str:
    for field in ("legal_excerpt", "scope_summary", "product_or_operation", "conditions"):
        words = gate.normalized_words(item.get(field, ""))
        if len(words) >= 8:
            return " ".join(words[:8])
    raise AssertionError("fixture sem oito palavras jurídicas")


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("uso: test_safe_pages_projection_gate.py SITE")
    clean = Path(sys.argv[1]).resolve()
    quarantine = load_items("data/benefits_quarantine.json", "entries")
    cards = load_items("data/benefits_crosswalk.json", "entries")
    ncm = load_items("data/ncm_benefits_index.json", "rows")
    pcncm = load_items("data/pis-cofins/ncm-index.json", "records")
    hashes = sorted({str(item.get("sha256", "")) for item in cards + ncm if item.get("sha256")})

    mutants: list[tuple[str, str, str]] = []
    if quarantine:
        mutants.extend([
            ("quarantine_id_first", "index.html", quarantine[0]["id"]),
            ("quarantine_id_last", "index.html", quarantine[-1]["id"]),
            ("legal_shingle_quarantine", "index.html", legal_shingle(quarantine[0])),
        ])
    if cards:
        card_with_excerpt = next(item for item in cards if len(gate.normalized_words(item.get("legal_excerpt", ""))) >= 8)
        mutants.extend([
            ("card_id_first", "index.html", cards[0]["id"]),
            ("card_id_last", "index.html", cards[-1]["id"]),
            ("legal_shingle_card", "index.html", legal_shingle(card_with_excerpt)),
        ])
    mutants.extend([
        ("ncm_id", "index.html", ncm[0]["id"]),
        ("pis_cofins_ncm_id", "index.html", pcncm[0]["id"]),
        ("source_hash_first", "index.html", hashes[0]),
        ("source_hash_last", "index.html", hashes[-1]),
        ("card_markup_class", "index.html", "<article class='benefit-card'>x</article>"),
        ("card_markup_data", "index.html", "<section data-card-id='opaque'>x</section>"),
        ("legal_field", "index.html", "field_provenance"),
        ("legal_act", "index.html", "Lei nº 123"),
    ])

    clean_errors: list[str] = []
    gate.SITE = clean
    gate.audit_site(clean_errors)
    if clean_errors:
        raise SystemExit(f"corpus limpo reprovado: {clean_errors}")

    failures: list[str] = []
    with tempfile.TemporaryDirectory(prefix="rjc-gate-mutants-") as temp:
        base = Path(temp)
        for index, (name, rel, injected) in enumerate(mutants):
            site = base / f"m{index:02d}"
            shutil.copytree(clean, site)
            target = site / rel
            original = target.read_text(encoding="utf-8")
            target.write_text(original + "\n" + injected, encoding="utf-8")
            gate.SITE = site
            errors: list[str] = []
            gate.audit_site(errors)
            if not errors:
                failures.append(name)

        structural = [
            ("extra_file", "extra.json", "{}"),
            ("nested_extra", "assets/renamed.html", "x"),
        ]
        for index, (name, rel, body) in enumerate(structural, len(mutants)):
            site = base / f"m{index:02d}"
            shutil.copytree(clean, site)
            target = site / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(body, encoding="utf-8")
            gate.SITE = site
            errors = []
            gate.audit_site(errors)
            if not errors:
                failures.append(name)

        replacement_mutants = [
                ("index_noindex_removed", "index.html", "noindex,nofollow,noarchive", "index,follow"),
                ("404_noindex_removed", "404.html", "noindex,nofollow,noarchive", "index,follow"),
                ("robots_allow_all", "robots.txt", "Disallow: /", "Disallow:"),
                ("robots_empty", "robots.txt", "Disallow: /", ""),
                ("robots_allow_conflict", "robots.txt", "Disallow: /", "Disallow: /\nAllow: /"),
                ("robots_commented", "robots.txt", "Disallow: /", "# Disallow: /"),
                ("meta_conflict", "index.html", "</head>", "<meta name='robots' content='index,follow'></head>"),
                (
                    "meta_comment_only",
                    "index.html",
                    '<meta name="robots" content="noindex,nofollow,noarchive">',
                    "<!-- noindex,nofollow,noarchive --><meta name='robots' content='index,follow'>",
                ),
                ("short_fact_index", "index.html", "</main>", "<p>ICMS aplicável: 18% nas operações internas.</p></main>"),
                ("short_fact_404", "404.html", "</main>", "<p>ICMS aplicável: 18% nas operações internas.</p></main>"),
                ("short_fact_llms", "llms.txt", "Não há fatos", "ICMS aplicável: 18%. Não há fatos"),
        ]
        for index, (name, rel, old, new) in enumerate(
            replacement_mutants,
            len(mutants) + len(structural),
        ):
            site = base / f"m{index:02d}"
            shutil.copytree(clean, site)
            target = site / rel
            target.write_text(target.read_text(encoding="utf-8").replace(old, new), encoding="utf-8")
            gate.SITE = site
            errors = []
            gate.audit_site(errors)
            if not errors:
                failures.append(name)

    if failures:
        print("Mutantes não detectados: " + ", ".join(failures))
        return 1
    total = len(mutants) + len(structural) + len(replacement_mutants)
    print(f"Gate eficaz: corpus limpo aprovado e {total}/{total} mutantes materiais rejeitados.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
