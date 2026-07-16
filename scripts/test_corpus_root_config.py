#!/usr/bin/env python3
"""Regression tests for portable local-corpus discovery."""

from __future__ import annotations

import os
import unittest
from pathlib import Path
from unittest.mock import patch

import ingest_bd_legislacao
import validated_benefits


class CorpusRootConfigTests(unittest.TestCase):
    def test_ingest_respects_explicit_corpus_root(self) -> None:
        with patch.dict(os.environ, {"RJC_BD_LEGISLACAO": r"D:\evidencias\BD_LEGISLACAO"}, clear=False):
            self.assertEqual(
                ingest_bd_legislacao.default_bd_root(),
                Path(r"D:\evidencias\BD_LEGISLACAO"),
            )

    def test_benefit_generator_respects_explicit_corpus_root(self) -> None:
        with patch.dict(os.environ, {"RJC_BD_LEGISLACAO": r"D:\evidencias\BD_LEGISLACAO"}, clear=False):
            self.assertEqual(
                validated_benefits.federal_corpus_root(),
                Path(r"D:\evidencias\BD_LEGISLACAO\#FEDERAIS-COMPILADO-ONLINE\legislacao_txt_completa"),
            )


if __name__ == "__main__":
    unittest.main()
