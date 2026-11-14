#!/usr/bin/env python3
"""Regression tests for the material-proof card gate."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "scripts" / "audit_proof_material_cards.py"
CARDS = ROOT / "data" / "prova_material" / "cards_em_reconstrucao.json"


class AuditProofMaterialCardsTest(unittest.TestCase):
    def run_gate(self, payload: dict) -> int:
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "cards.json"
            path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            return subprocess.run([sys.executable, str(AUDIT), "--cards", str(path)], check=False, capture_output=True, text=True).returncode

    def test_clean_registry_passes(self) -> None:
        payload = json.loads(CARDS.read_text(encoding="utf-8"))
        self.assertEqual(self.run_gate(payload), 0)

    def test_synthetic_date_marker_fails(self) -> None:
        payload = json.loads(CARDS.read_text(encoding="utf-8"))
        payload["cards"][0]["field_provenance"]["ato.data"]["regra_normalizacao"] = "copiado de captured_on"
        self.assertNotEqual(self.run_gate(payload), 0)

    def test_missing_field_provenance_fails(self) -> None:
        payload = json.loads(CARDS.read_text(encoding="utf-8"))
        del payload["cards"][1]["field_provenance"]["temporal.inicio_eficacia"]
        self.assertNotEqual(self.run_gate(payload), 0)

    def test_truncated_literal_fails(self) -> None:
        payload = json.loads(CARDS.read_text(encoding="utf-8"))
        payload["cards"][0]["field_provenance"]["titulo_humano"]["trecho_literal"] = "Texto... truncado"
        self.assertNotEqual(self.run_gate(payload), 0)

    def test_provenance_value_mismatch_fails(self) -> None:
        payload = json.loads(CARDS.read_text(encoding="utf-8"))
        payload["cards"][1]["field_provenance"]["regra_estruturada.tributos"]["valor"] = ["CBS", "IBS"]
        self.assertNotEqual(self.run_gate(payload), 0)


if __name__ == "__main__":
    unittest.main()
