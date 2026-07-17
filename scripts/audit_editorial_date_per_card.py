#!/usr/bin/env python3
"""Require per-card verification dates and derived editorial dating."""

from __future__ import annotations

from audit_v2_helpers import benefit_entries, benefit_payload, stale_date_hits


def main() -> int:
    errors: list[str] = []
    entries = benefit_entries()
    for item in entries:
        if not str(item.get("verificado_em", "")).strip():
            errors.append(f"{item.get('id', '?')}: publicado sem verificado_em por card")
        if len(errors) >= 40:
            break
    payload = benefit_payload()
    summary = payload.get("summary", {}) if isinstance(payload, dict) else {}
    fail_closed = (
        isinstance(payload, dict)
        and payload.get("publication_status") == "BLOQUEADO_SEM_PROVA_MATERIAL"
        and entries == []
    )
    if not fail_closed:
        if summary.get("editorial_date_source") != "min_verificado_em":
            errors.append("summary.editorial_date_source deve ser min_verificado_em")
        if not str(summary.get("editorial_date", "")).strip():
            errors.append("summary.editorial_date ausente")
    errors.extend(stale_date_hits()[:20])
    if errors:
        print("Falhas de data editorial por card:")
        for error in errors:
            print(f"- {error}")
        return 1
    if fail_closed:
        print("Sem cards públicos materiais: regra editorial por card não se aplica.")
    print("Data editorial derivada e verificado_em presentes nos cards publicados.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
