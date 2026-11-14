"""Regression tests for the human and AI renderings of the same card registry."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RENDER = ROOT / "scripts" / "render_proven_cards.py"
CARDS = ROOT / "data" / "prova_material" / "cards_em_reconstrucao.json"


class RenderProvenCardsTest(unittest.TestCase):
    def test_preview_has_same_card_ids_for_people_and_ai(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            completed = subprocess.run(
                [sys.executable, str(RENDER), "--cards", str(CARDS), "--output-dir", str(output)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            registry = json.loads(CARDS.read_text(encoding="utf-8"))
            ai = json.loads((output / "normas-ia.json").read_text(encoding="utf-8"))
            page = (output / "index.html").read_text(encoding="utf-8")
            expected = [card["id"] for card in registry["cards"]]
            self.assertEqual([card["id"] for card in ai["cards"]], expected)
            for card_id in expected:
                self.assertIn(f'id="{card_id}"', page)

    def test_public_render_rejects_unapproved_cards(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            completed = subprocess.run(
                [sys.executable, str(RENDER), "--cards", str(CARDS), "--output-dir", tmp, "--public"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("Recusada emissão pública", completed.stderr)


if __name__ == "__main__":
    unittest.main()
