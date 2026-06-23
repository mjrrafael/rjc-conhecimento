#!/usr/bin/env python3
"""Adversarial tests for Produto/NCM validation."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from audit_produtos_ncm import (  # noqa: E402
    CAP10,
    CORPUS,
    INDEX,
    UF_PLAN,
    load_json,
    validate_corpus,
    validate_no_local_paths,
    validate_payloads,
    validate_product,
    validate_source,
    validate_uf_plan,
)


def expect_failure(name: str, errors: list[str], expected_fragment: str) -> None:
    joined = "\n".join(errors)
    if expected_fragment not in joined:
        raise AssertionError(f"{name}: expected {expected_fragment!r}; got {joined!r}")


def main() -> int:
    index = load_json(INDEX)
    cap10 = load_json(CAP10)
    corpus = load_json(CORPUS)
    uf_plan = load_json(UF_PLAN)
    assert isinstance(index, dict)
    assert isinstance(cap10, dict)
    assert isinstance(corpus, dict)
    assert isinstance(uf_plan, dict)
    product = copy.deepcopy(cap10["products"][0])
    source_ids = {source["id"] for source in index["official_sources"]}

    bad_source = copy.deepcopy(index["official_sources"][0])
    bad_source["http_status"] = 404
    bad_source["url_resolve"] = False
    expect_failure("broken official URL", validate_source(bad_source), "live official URL must resolve HTTP 200")

    bad_source = copy.deepcopy(index["official_sources"][0])
    bad_source["live_sha256"] = ""
    expect_failure("missing live hash", validate_source(bad_source), "missing/invalid live_sha256")

    bad_product = copy.deepcopy(product)
    bad_product["status"] = "VERIFICADO"
    expect_failure("green seed product", validate_product(bad_product, source_ids), "must remain A_VALIDAR")

    bad_product = copy.deepcopy(product)
    bad_product["publishable"] = True
    expect_failure("publishable imported seed", validate_product(bad_product, source_ids), "cannot be publishable")

    bad_product = copy.deepcopy(product)
    bad_product["search_text"] = "arroz"
    expect_failure("weak search text", validate_product(bad_product, source_ids), "search_text missing 1006")

    bad_product = copy.deepcopy(product)
    bad_product["reselos"][0]["status"] = "vigente"
    bad_product["reselos"][0]["publicacao"] = "A_VALIDAR"
    expect_failure("green reselo without dates", validate_product(bad_product, source_ids), "green status with incomplete temporal envelope")

    bad_corpus = copy.deepcopy(corpus)
    bad_corpus["selo_maximo_atual"] = "VERDE"
    expect_failure("green local corpus", validate_corpus(bad_corpus), "capped at AMARELO_CORPUS_LOCAL")

    bad_corpus = copy.deepcopy(corpus)
    bad_corpus["entries"][0]["storage"]["path"] = r"G:\vaza\fonte.txt"
    expect_failure("absolute path leak", validate_no_local_paths("bad corpus", bad_corpus), "leaks an absolute local drive path")

    bad_corpus = copy.deepcopy(corpus)
    bad_corpus["entries"][0]["storage"]["source_relative_path"] = "Outros computadores/LOCALHOST/fonte.txt"
    expect_failure("local marker leak", validate_no_local_paths("bad corpus", bad_corpus), "leaks local environment markers")

    bad_plan = copy.deepcopy(uf_plan)
    first_non_go = next(row for row in bad_plan["ufs"] if row["uf"] != "GO")
    first_non_go["cbenef_status"] = "VERDE"
    expect_failure("non-GO cBenef green", validate_uf_plan(bad_plan), "non-GO cBenef must remain A_VALIDAR_SEFAZ_VIVA")

    bad_plan = copy.deepcopy(uf_plan)
    bad_plan["ufs"][0]["publicavel_verde"] = True
    expect_failure("UF plan green", validate_uf_plan(bad_plan), "cannot be green/publishable")

    bad_index = copy.deepcopy(index)
    bad_cap10 = copy.deepcopy(cap10)
    bad_cap10["products"][0]["reselos"][0]["official_source_ids"] = ["fonte_inventada"]
    expect_failure(
        "unknown source",
        validate_payloads(bad_index, bad_cap10, corpus, uf_plan),
        "unknown source id fonte_inventada",
    )

    print(json.dumps({"status": "OK", "adversarial_cases": 12}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
