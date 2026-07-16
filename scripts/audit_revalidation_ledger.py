#!/usr/bin/env python3
"""Verify that corpus revalidation covers every input without promotion."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "auditoria" / "execucoes" / "revalidacao-corpus-2026-07-16"


def entries(name: str) -> list[dict]:
    payload = json.loads((ROOT / "data" / name).read_text(encoding="utf-8"))
    rows = payload.get("entries", []) if isinstance(payload, dict) else []
    if not isinstance(rows, list):
        raise ValueError(f"{name} sem entries")
    return rows


def main() -> int:
    cards = entries("benefits_crosswalk.json")
    quarantine = entries("benefits_quarantine.json")
    path = RUN / "ledger_cards.csv"
    errors: list[str] = []
    if not path.exists():
        errors.append("ledger_cards.csv ausente")
    else:
        rows = list(csv.DictReader(path.open(encoding="utf-8")))
        expected = {str(row.get("id") or "") for row in cards + quarantine}
        observed = [str(row.get("record_id") or "") for row in rows]
        if len(observed) != len(expected) or set(observed) != expected or len(set(observed)) != len(observed):
            errors.append(f"bijeção do ledger falhou: esperado={len(expected)} observado={len(observed)} únicos={len(set(observed))}")
        by_id = {row["record_id"]: row for row in rows if row.get("record_id")}
        for card in cards:
            row = by_id.get(str(card.get("id") or ""))
            if not row:
                continue
            if row.get("record_kind") != "crosswalk" or row.get("decision") not in {"QUARENTENA_NAO_PUBLICA", "QUARENTENA_AGUARDANDO_REVISAO_INDEPENDENTE"}:
                errors.append(f"card legado fora de quarentena: {card.get('id')}")
            reasons = str(row.get("reasons") or "")
            if "field_provenance_ausente" not in reasons or "recibo_de_verificacao_ausente" not in reasons:
                errors.append(f"card sem motivo material de bloqueio: {card.get('id')}")
        for item in quarantine:
            row = by_id.get(str(item.get("id") or ""))
            if not row:
                continue
            if row.get("record_kind") != "quarantine" or row.get("decision") not in {"DESCARTAR_NAO_BENEFICIO", "QUARENTENA_REVALIDAR_BENEFICIO"}:
                errors.append(f"quarentena sem decisão terminal: {item.get('id')}")
        decision_counts = Counter(row.get("decision") for row in rows)
        if decision_counts.get("PUBLICAR", 0):
            errors.append("ledger contém promoção pública sem gate material")
        print("decisoes=" + json.dumps(dict(sorted(decision_counts.items())), ensure_ascii=False))
    summary_path = RUN / "summary.json"
    if not summary_path.exists():
        errors.append("summary.json ausente")
    else:
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        if summary.get("input", {}).get("total") != len(cards) + len(quarantine):
            errors.append("summary não cobre o total de entradas")
        if summary.get("publication") != "BLOQUEADA: nenhuma decisão deste executor promove conteúdo público":
            errors.append("summary permite publicação indevida")
        if summary.get("http", {}).get("receipt_kind") == "PLATFORM_NATIVE":
            errors.append("recibo local foi falsamente rotulado como nativo")
    if errors:
        print("Falhas no ledger de revalidação:")
        for error in errors[:50]:
            print("- " + error)
        return 1
    print(f"Ledger de revalidação íntegro: {len(cards)} cards e {len(quarantine)} itens de quarentena, sem promoção pública.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
