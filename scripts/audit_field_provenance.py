#!/usr/bin/env python3
"""Verify that each recorded legal excerpt actually occurs in its captured raw body.

This is deliberately stricter than a schema check: a hash and a URL are not enough
when the literal citation was shortened, copied from a different source or made up.
It validates only the local reproducibility stage; native platform receipts and a
blind refetch remain separate publication requirements.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import unicodedata
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "auditoria" / "execucoes" / "reconstrucao-provas-2026-07-16"
DEFAULT_CARDS = ROOT / "data" / "prova_material" / "cards_em_reconstrucao.json"


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def normalized(value: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", value)).strip()


def load_receipts(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"recibos inválidos: {path}")
    return [item for item in payload if isinstance(item, dict)]


def source_text(path: Path, mime: str) -> str:
    if mime.lower() == "application/pdf":
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "source.txt"
            completed = subprocess.run(["pdftotext", "-raw", str(path), str(out)], capture_output=True, text=True, check=False)
            if completed.returncode != 0:
                raise ValueError(f"pdftotext falhou para {path}: {completed.stderr.strip()}")
            return out.read_text(encoding="utf-8", errors="strict")
    extractor = TextExtractor()
    extractor.feed(path.read_text(encoding="utf-8", errors="strict"))
    return "\n".join(extractor.parts)


def literal_parts(literal: str) -> list[str]:
    # Separate non-contiguous articles while preserving literal text inside each article.
    return [part for part in re.split(r"\n\s*\n", literal) if normalized(part)]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cards", type=Path, default=DEFAULT_CARDS)
    parser.add_argument("--first", type=Path, default=RUN / "act_capture_receipts_tentativa_3.json")
    parser.add_argument("--second", type=Path, default=RUN / "act_capture_receipts_tentativa_4.json")
    args = parser.parse_args()
    cards = json.loads(args.cards.read_text(encoding="utf-8")).get("cards", [])
    one, two = load_receipts(args.first), load_receipts(args.second)
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for receipt in one + two:
        response, body = receipt.get("response", {}), receipt.get("body", {})
        key = (str(response.get("url_final", "")), str(body.get("sha256", "")))
        grouped.setdefault(key, []).append(receipt)
    errors: list[str] = []
    cache: dict[tuple[str, str], str] = {}
    for card in cards:
        card_id = str(card.get("id", "<sem-id>"))
        for field, proof in card.get("field_provenance", {}).items():
            additional = proof.get("fundamentos_adicionais", [])
            if not isinstance(additional, list) or any(not isinstance(entry, dict) for entry in additional):
                errors.append(f"{card_id}/{field}: fundamentos adicionais inválidos")
                additional = []
            entries = [(field, proof)] + [(f"{field}.fundamento[{index}]", entry) for index, entry in enumerate(additional, start=1)]
            for entry_field, entry in entries:
                key = (str(entry.get("url_final", "")), str(entry.get("sha256_corpo_bruto", "")))
                receipts = grouped.get(key, [])
                if len(receipts) != 2:
                    errors.append(f"{card_id}/{entry_field}: não há exatamente dois recibos para URL e hash da proveniência")
                    continue
                chosen = receipts[0]
                response, body = chosen.get("response", {}), chosen.get("body", {})
                raw_path = Path(str(body.get("path_externo", "")))
                if chosen.get("result") != "CAPTURADA_PENDENTE_DE_REFETCH" or response.get("status") != 200:
                    errors.append(f"{card_id}/{entry_field}: recibo não é captura HTTP 200")
                    continue
                if not raw_path.is_file():
                    errors.append(f"{card_id}/{entry_field}: corpo bruto ausente: {raw_path}")
                    continue
                actual_hash = hashlib.sha256(raw_path.read_bytes()).hexdigest()
                if actual_hash != key[1]:
                    errors.append(f"{card_id}/{entry_field}: hash do corpo bruto diverge")
                    continue
                if key not in cache:
                    try:
                        cache[key] = normalized(source_text(raw_path, str(response.get("mime", ""))))
                    except Exception as exc:  # noqa: BLE001
                        errors.append(f"{card_id}/{entry_field}: não foi possível extrair fonte: {exc}")
                        continue
                literal = str(entry.get("trecho_literal", ""))
                if "..." in literal or "…" in literal:
                    errors.append(f"{card_id}/{entry_field}: citação com reticências é proibida")
                    continue
                for index, part in enumerate(literal_parts(literal), start=1):
                    if normalized(part) not in cache[key]:
                        errors.append(f"{card_id}/{entry_field}: trecho literal {index} não ocorre no corpo bruto identificado")
    if errors:
        print("FALHOU")
        print("\n".join(f"- {item}" for item in errors))
        return 1
    print("OK: cada trecho de proveniência ocorre no corpo bruto com hash e dupla captura local correspondentes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
