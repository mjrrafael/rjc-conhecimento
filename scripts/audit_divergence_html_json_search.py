#!/usr/bin/env python3
"""Detect divergence between benefit HTML, JSON registry and search index."""

from __future__ import annotations

import re
import unicodedata
from html import unescape

from audit_v2_helpers import benefit_articles_by_id, benefit_entries, search_full_entries


def normalize_text(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-z0-9]+", " ", text.lower())
    return re.sub(r"\s+", " ", text).strip()


def main() -> int:
    html_cards = benefit_articles_by_id()
    search = {
        item.get("url"): item for item in search_full_entries()
        if isinstance(item, dict) and str(item.get("url", "")).startswith("beneficios/index.html#")
    }
    errors: list[str] = []
    for item in benefit_entries():
        item_id = item.get("id", "?")
        block = html_cards.get(item_id)
        if not block:
            errors.append(f"{item_id}: ausente do HTML canônico de benefícios")
            continue
        block_text = unescape(block)
        scope = str(item.get("scope_summary", "") or item.get("product_or_operation", "")).strip()
        status = str(item.get("validity_status", "")).strip()
        normalized_block = normalize_text(block_text)
        if scope and normalize_text(scope) not in normalized_block:
            errors.append(f"{item_id}: escopo diverge entre JSON e HTML")
        if status and normalize_text(status) not in normalized_block:
            errors.append(f"{item_id}: status/vigência diverge entre JSON e HTML")
        search_item = search.get(f"beneficios/index.html#{item_id}")
        if not search_item:
            errors.append(f"{item_id}: ausente da busca integral")
        else:
            search_body = unescape(str(search_item.get("body", "")))
            normalized_body = normalize_text(search_body)
            if scope and normalize_text(scope) not in normalized_body:
                errors.append(f"{item_id}: escopo diverge entre JSON e busca")
            if status and normalize_text(status) not in normalized_body:
                errors.append(f"{item_id}: status diverge entre JSON e busca")
        if len(errors) >= 40:
            break
    if errors:
        print("Falhas de convergência entre HTML, JSON e busca:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("HTML, JSON e busca convergem para os benefícios publicados.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
