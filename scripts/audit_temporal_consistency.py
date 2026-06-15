#!/usr/bin/env python3
"""Validate temporal envelope and status consistency for public benefit cards."""

from __future__ import annotations

from datetime import date

from audit_v2_helpers import benefit_entries


TODAY = date.today().isoformat()
REQUIRED_FIELDS = ("publicacao", "inicio_vigencia", "inicio_eficacia", "status")


def parse_iso(value: object) -> date | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def main() -> int:
    errors: list[str] = []
    today = date.fromisoformat(TODAY)
    for item in benefit_entries():
        item_id = item.get("id", "?")
        missing = [field for field in REQUIRED_FIELDS if not str(item.get(field, "")).strip()]
        if missing:
            errors.append(f"{item_id}: sem envelope temporal completo ({', '.join(missing)})")
            if len(errors) >= 40:
                break
            continue
        status = str(item.get("status", "")).strip().lower()
        start = parse_iso(item.get("inicio_eficacia"))
        end = parse_iso(item.get("fim_vigencia"))
        if not start:
            errors.append(f"{item_id}: inicio_eficacia inválido")
        if item.get("fim_vigencia") and not end:
            errors.append(f"{item_id}: fim_vigencia inválido")
        if start and status == "vigente" and start > today:
            errors.append(f"{item_id}: marcado vigente com início de eficácia futuro ({start.isoformat()})")
        if end and status == "vigente" and end < today:
            errors.append(f"{item_id}: marcado vigente com fim_vigencia passado ({end.isoformat()})")
        if len(errors) >= 40:
            break
    if errors:
        print("Falhas de consistência temporal:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Envelope temporal consistente nos benefícios públicos.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
