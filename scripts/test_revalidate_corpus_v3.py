#!/usr/bin/env python3
"""Focused properties for the fail-closed corpus revalidator."""

from __future__ import annotations

import unittest

from revalidate_corpus_v3 import crosswalk_decision, inherited_dates, quarantine_decision, validate_capture_url


class RevalidationProperties(unittest.TestCase):
    def test_captured_date_never_promotes(self) -> None:
        for field in ("publicacao", "inicio_vigencia", "inicio_eficacia", "fim_vigencia"):
            with self.subTest(field=field):
                card = {"captured_on": "2026-04-26", field: "2026-04-26", "tax": "ICMS", "classification_confidence": 0.95}
                self.assertEqual(inherited_dates(card), [field])
                self.assertEqual(crosswalk_decision(card)[0], "QUARENTENA_NAO_PUBLICA")

    def test_benefit_in_quarantine_stays_nonpublic_without_proof(self) -> None:
        self.assertEqual(quarantine_decision({"legal_excerpt": "Fica concedida isenção do ICMS."})[0], "QUARENTENA_REVALIDAR_BENEFICIO")

    def test_icms_not_proven_is_never_treated_as_internalized(self) -> None:
        decision, reasons = crosswalk_decision({
            "tax": "ICMS", "classification_confidence": 0.95,
            "internalization": "NÃO_COMPROVADA",
        })
        self.assertEqual(decision, "QUARENTENA_NAO_PUBLICA")
        self.assertIn("internalizacao_nao_comprovada", reasons)

    def test_non_benefit_is_not_recast_as_benefit(self) -> None:
        self.assertEqual(quarantine_decision({"legal_excerpt": "O contribuinte deve atualizar seu cadastro."})[0], "DESCARTAR_NAO_BENEFICIO")

    def test_capture_refuses_nonpublic_or_credentialed_urls(self) -> None:
        for url in ("file:///tmp/ato.html", "https://user:secret@example.gov.br/ato", "http://127.0.0.1/ato"):
            with self.subTest(url=url):
                with self.assertRaises(ValueError):
                    validate_capture_url(url)
        validate_capture_url("https://www.gov.br/receitafederal/pt-br")


if __name__ == "__main__":
    unittest.main()
