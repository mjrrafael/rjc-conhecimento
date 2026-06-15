#!/usr/bin/env python3
"""Block public benefit cards that do not expose the v2 contract in HTML."""

from __future__ import annotations

from audit_v2_helpers import BENEFIT_PAGES, raw_benefit_articles


REQUIRED_MARKERS = [
    "Escopo publicado:",
    "Mercadoria/operação",
    "Vigência/status",
    "Base legal",
    "Condição",
    "Vedação",
    "Prova",
    "Risco",
    "Ato oficial",
    "Publicação",
    "Início vigência",
    "Início eficácia",
    "Fim vigência",
    "Transição RT-2026",
    "Status",
    "Verificado em",
]


def main() -> int:
    errors: list[str] = []
    for path in BENEFIT_PAGES:
        for index, block in enumerate(raw_benefit_articles(path), start=1):
            missing = [marker for marker in REQUIRED_MARKERS if marker not in block]
            if missing:
                errors.append(
                    f"{path.relative_to(path.parents[1])} card #{index} sem campos visíveis do contrato v2: {', '.join(missing[:8])}"
                )
                if len(errors) >= 25:
                    break
        if len(errors) >= 25:
            break
    if errors:
        print("Falhas na visibilidade do contrato dos cards:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Todos os cards públicos expõem o contrato v2 no HTML.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
