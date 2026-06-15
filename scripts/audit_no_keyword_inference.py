#!/usr/bin/env python3
"""Block publishable benefits that still depend on keyword-only inference."""

from __future__ import annotations

from audit_v2_helpers import benefit_entries, confidence_score


def main() -> int:
    errors: list[str] = []
    for item in benefit_entries():
        item_id = item.get("id", "?")
        provenance = str(item.get("provenance", "") or "").strip().lower()
        score = confidence_score(item.get("classification_confidence"))
        if provenance in {"keyword_only", "keyword-only"}:
            errors.append(f"{item_id}: publicado com provenance=keyword_only")
        elif not provenance:
            errors.append(f"{item_id}: publicado sem provenance explícito")
        if score is None:
            errors.append(f"{item_id}: publicado sem classificação numérica auditável")
        elif score < 0.80:
            errors.append(f"{item_id}: publicado com classification_confidence={score:.2f} (< 0.80)")
        if len(errors) >= 40:
            break
    if errors:
        print("Falhas de inferência/publicação:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Nenhum benefício público depende de inferência por palavra-chave.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
