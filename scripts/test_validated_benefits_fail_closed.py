#!/usr/bin/env python3
"""Regression tests for calendar and field-level material provenance gates."""

from __future__ import annotations

import copy

import validated_benefits as vb


FIELDS = ("publication_date", "validity_start", "effectiveness_start")
EXCERPT = (
    "Fica concedida isenção do IPI nas operações internas com aeronave classificada "
    "no código NCM 88022010, desde que o estabelecimento industrial seja habilitado "
    "nos termos deste Decreto oficial."
)


def strong_source() -> dict:
    values = {
        "publication_date": "2027-01-10",
        "validity_start": "2027-01-11",
        "effectiveness_start": "2027-01-12",
    }
    provenance = {}
    for field, value in values.items():
        provenance[field] = {
            "card_id": "card-material-001",
            "field": field,
            "value": value,
            "final_url": "https://www.gov.br/receitafederal/pt-br/assuntos/legislacao/ato-9999",
            "official_domain": "www.gov.br",
            "redirects": [],
            "http_status": 200,
            "mime": "text/html",
            "body_sha256": "a" * 64,
            "literal_excerpt": f"O ato oficial fixa {field} na data de {value} para o benefício descrito.",
            "locator": "art. 1, caput",
            "normalization_rule": "data literal normalizada para ISO-8601",
        }
    return {
        "jurisdiction": "BR",
        "name": "Brasil",
        "tax": "IPI",
        "title": "Decreto oficial 9.999/2027",
        "source_file": "ato-9999.txt",
        "source_path": "ato-9999.txt",
        "official_url": "https://www.gov.br/receitafederal/pt-br/assuntos/legislacao/ato-9999",
        "sha256": "b" * 64,
        "publishable": True,
        **values,
        "verified_on": "2027-01-13",
        "field_provenance": provenance,
        "independent_http_receipt_ids": ["native-http-001", "native-http-002"],
        "verification_receipt_id": "verification-001",
    }


def rejected(source: dict) -> bool:
    entry, reasons = vb.evaluate_entry(source, EXCERPT, 1)
    return entry is None and bool(reasons) and bool(vb.material_publication_blockers(source))


def main() -> int:
    if vb.iso_date("2027-99-99") or vb.iso_date("2027-02-29") or vb.iso_date("2027/13/01"):
        raise SystemExit("data calendárica impossível foi aceita")
    if vb.iso_date("2028-02-29") != "2028-02-29":
        raise SystemExit("data bissexta válida foi rejeitada")

    source = strong_source()
    blockers = vb.material_publication_blockers(source)
    if blockers:
        raise SystemExit(f"fixture material forte reprovada: {blockers}")
    entry, reasons = vb.evaluate_entry(source, EXCERPT, 1)
    if not entry or reasons or entry.get("publishable") is not True:
        raise SystemExit(f"fixture material forte não publicou: {reasons}")

    variants = []
    for field in (*FIELDS, "verified_on"):
        item = copy.deepcopy(source)
        item[field] = "2027-99-99"
        variants.append((f"invalid_date_{field}", item))
    for field in FIELDS:
        item = copy.deepcopy(source)
        item["field_provenance"][field]["value"] = "2027-01-31"
        variants.append((f"mismatched_value_{field}", item))
        item = copy.deepcopy(source)
        item["field_provenance"][field]["final_url"] = "https://example.invalid/a"
        item["field_provenance"][field]["official_domain"] = "example.invalid"
        variants.append((f"non_official_url_{field}", item))
        item = copy.deepcopy(source)
        item["field_provenance"][field]["body_sha256"] = "x"
        variants.append((f"short_hash_{field}", item))
        item = copy.deepcopy(source)
        item["field_provenance"][field]["literal_excerpt"] = "x"
        variants.append((f"empty_excerpt_{field}", item))
    item = copy.deepcopy(source)
    item["official_url"] = "https://example.invalid/a"
    variants.append(("non_official_source", item))
    item = copy.deepcopy(source)
    item["sha256"] = "x"
    variants.append(("short_source_hash", item))
    item = copy.deepcopy(source)
    item["independent_http_receipt_ids"] = ["same-id", "same-id"]
    variants.append(("non_independent_receipts", item))
    item = copy.deepcopy(source)
    item["verification_receipt_id"] = "v1"
    variants.append(("short_verification_receipt", item))

    missed = [name for name, item in variants if not rejected(item)]
    if missed:
        raise SystemExit("variantes materiais aceitas: " + ", ".join(missed))
    print(f"Gerador fail-closed: fixture forte aprovada e {len(variants)}/{len(variants)} variantes rejeitadas.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
