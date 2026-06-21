#!/usr/bin/env python3
"""Adversarial tests for the PIS/Cofins NCM dataset validator."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from audit_pis_cofins_ncm import PUBLIC_NDJSON, load_ndjson, validate_public_row  # noqa: E402


def base_row() -> dict:
    rows = load_ndjson(PUBLIC_NDJSON)
    if not rows:
        raise AssertionError("public dataset has no rows to mutate")
    return copy.deepcopy(rows[0])


def expect_failure(name: str, row: dict, expected_fragment: str) -> None:
    errors = validate_public_row(row)
    joined = "\n".join(errors)
    if expected_fragment not in joined:
        raise AssertionError(f"{name}: expected {expected_fragment!r}; got {joined!r}")


def main() -> int:
    row = base_row()

    bad = copy.deepcopy(row)
    bad["id"] = "q-" + bad["id"]
    expect_failure("quarantine id", bad, "quarantine id cannot be public")

    bad = copy.deepcopy(row)
    bad["classification_confidence"] = 0.42
    expect_failure("low confidence", bad, "classification_confidence below 0.80")

    bad = copy.deepcopy(row)
    bad["ato_oficial"]["http_status"] = 404
    expect_failure("broken link", bad, "official source must be HTTPS HTTP 200")

    bad = copy.deepcopy(row)
    bad["inicio_eficacia"] = ""
    expect_failure("missing efficacy", bad, "incomplete validity dates")

    bad = copy.deepcopy(row)
    bad["mercadoria_servico"] = "02, 01."
    expect_failure("short human description", bad, "mercadoria_servico too short")

    bad = copy.deepcopy(row)
    bad["provenance"]["origem"] = "keyword_only"
    expect_failure("keyword-only provenance", bad, "provenance must be ato_oficial")

    bad = copy.deepcopy(row)
    bad["transicao_cbs"] = {}
    expect_failure("missing transition", bad, "missing transicao_cbs status/reference")

    bad = copy.deepcopy(row)
    bad["ncm"]["digitos"] = "2026"
    bad["ncm"]["codigo"] = "2026"
    bad["trecho_legal"] = "Art. 47 da Lei 10.865 de 2004, sem contexto NCM suficiente para publicar."
    errors = validate_public_row(bad)
    if not errors:
        raise AssertionError("date/article-like code should not pass with short legal excerpt")

    print(json.dumps({"status": "OK", "adversarial_cases": 8}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
