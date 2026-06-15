#!/usr/bin/env python3
"""Ensure quarantine ids do not leak into public discovery artifacts."""

from __future__ import annotations

import re

from audit_v2_helpers import (
    BENEFIT_PAGES,
    LLMS_TXT,
    SEARCH_FULL,
    SEARCH_JS,
    SITEMAP_TXT,
    SITEMAP_XML,
    quarantine_entries,
    read_text,
)


def main() -> int:
    ids = {str(item.get("id", "")).strip() for item in quarantine_entries() if str(item.get("id", "")).strip()}
    targets = [SEARCH_JS, SEARCH_FULL, LLMS_TXT, SITEMAP_TXT, SITEMAP_XML, *BENEFIT_PAGES]
    target_text = {path: read_text(path) for path in targets}
    errors: list[str] = []
    for path, text in target_text.items():
        found = set(re.findall(r"\bq-[a-z0-9-]{8,}\b", text, flags=re.I))
        for item_id in sorted(found & ids):
            errors.append(f"{item_id} vazou para {path.relative_to(path.parents[1])}")
            if len(errors) >= 25:
                break
        if len(errors) >= 25:
            break
    if errors:
        print("Falhas de isolamento da quarentena:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Quarentena isolada dos artefatos públicos ({len(ids)} ids verificados).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
