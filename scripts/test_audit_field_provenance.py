"""Regression tests for raw-body matching of legal excerpts."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "scripts" / "audit_field_provenance.py"
CARDS = ROOT / "data" / "prova_material" / "cards_em_reconstrucao.json"


class AuditFieldProvenanceTest(unittest.TestCase):
    def run_gate(self, cards: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(AUDIT), "--cards", str(cards)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_clean_cards_match_raw_bodies(self) -> None:
        result = self.run_gate(CARDS)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_fabricated_literal_fails(self) -> None:
        payload = json.loads(CARDS.read_text(encoding="utf-8"))
        payload["cards"][0]["field_provenance"]["titulo_humano"]["trecho_literal"] = "Trecho inexistente na fonte oficial"
        with tempfile.TemporaryDirectory() as raw:
            cards = Path(raw) / "cards.json"
            cards.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            result = self.run_gate(cards)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("não ocorre no corpo bruto", result.stdout)


if __name__ == "__main__":
    unittest.main()
