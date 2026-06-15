#!/usr/bin/env python3
"""Require explicit RT-2026 transition labeling for legacy consumption taxes."""

from __future__ import annotations

from audit_v2_helpers import benefit_entries, tax_requires_transition


def main() -> int:
    errors: list[str] = []
    for item in benefit_entries():
        tax = str(item.get("tax", "")).strip()
        if not tax_requires_transition(tax):
            continue
        if not str(item.get("transicao_rt", "")).strip():
            errors.append(f"{item.get('id', '?')}: {tax} sem campo transicao_rt")
        if len(errors) >= 40:
            break
    if errors:
        print("Falhas no selo de transição RT-2026:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Todos os benefícios dos tributos legados trazem transicao_rt.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
