#!/usr/bin/env python3
"""Property tests for archival-before-sanitization."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from sanitize_unproven_benefits import archive_and_sanitize, sha256_file


class SanitizationTests(unittest.TestCase):
    def test_archive_precedes_empty_public_datasets(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            crosswalk = base / "benefits_crosswalk.json"
            quarantine = base / "benefits_quarantine.json"
            crosswalk.write_text(json.dumps({"entries": [{"id": "card-1", "legal_excerpt": "isenção"}]}), encoding="utf-8")
            quarantine.write_text(json.dumps({"entries": [{"id": "q-1", "legal_excerpt": "suspensão"}]}), encoding="utf-8")
            before_crosswalk, before_quarantine = sha256_file(crosswalk), sha256_file(quarantine)
            manifest = archive_and_sanitize(crosswalk, quarantine, base / "private-evidence", "2026-07-16")
            self.assertEqual(manifest["inputs"]["crosswalk_entries"], 1)
            self.assertEqual(manifest["inputs"]["quarantine_entries"], 1)
            self.assertEqual(json.loads(crosswalk.read_text(encoding="utf-8"))["entries"], [])
            self.assertEqual(json.loads(quarantine.read_text(encoding="utf-8"))["entries"], [])
            self.assertEqual(sha256_file(base / "private-evidence" / "benefits_crosswalk.legacy.json"), before_crosswalk)
            self.assertEqual(sha256_file(base / "private-evidence" / "benefits_quarantine.legacy.json"), before_quarantine)


if __name__ == "__main__":
    unittest.main()
