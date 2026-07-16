#!/usr/bin/env python3
"""Reject material benefit or quarantine entries in the public datasets."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load(path: Path, schema: str, status: str) -> list[str]:
    errors: list[str] = []
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != schema:
        errors.append(f"schema inesperado: {path.relative_to(ROOT)}")
    if payload.get("publication_status") != status:
        errors.append(f"status de saneamento ausente: {path.relative_to(ROOT)}")
    if payload.get("entries") != []:
        errors.append(f"dados materiais ainda presentes: {path.relative_to(ROOT)}")
    serialized = json.dumps(payload, ensure_ascii=False).casefold()
    for protected in ("official_url", "legal_excerpt", "field_provenance", "verification_receipt_id"):
        if protected in serialized:
            errors.append(f"campo material protegido ainda público: {path.relative_to(ROOT)}:{protected}")
    return errors


def main() -> int:
    errors = []
    errors.extend(load(ROOT / "data" / "benefits_crosswalk.json", "rjc-validated-benefits-crosswalk-v3", "BLOQUEADO_SEM_PROVA_MATERIAL"))
    errors.extend(load(ROOT / "data" / "benefits_quarantine.json", "rjc-benefits-quarantine-v1", "NAO_PUBLICA_EXTERNALIZADA"))
    if errors:
        print("Saneamento de datasets reprovado:")
        print("\n".join(f"- {error}" for error in errors))
        return 1
    print("Datasets de cards e quarentena saneados: zero entradas materiais públicas.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
