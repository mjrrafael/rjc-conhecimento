#!/usr/bin/env python3
"""Fail closed when a reconstructed card lacks field-level material provenance."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / "data" / "prova_material" / "cards_em_reconstrucao.json"
SAFE_STATES = {"NAO_PUBLICAR_SEM_RECIBO_NATIVO_E_REVISAO_CEGA", "APROVADA_PARA_PUBLICACAO"}
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def error(errors: list[str], card_id: str, message: str) -> None:
    errors.append(f"{card_id}: {message}")


def field_value(card: dict, path: str):
    value = card
    for piece in path.split("."):
        if not isinstance(value, dict) or piece not in value:
            raise KeyError(path)
        value = value[piece]
    if isinstance(value, dict) and "valor" in value:
        return value["valor"]
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cards", type=Path, default=DEFAULT)
    args = parser.parse_args()
    payload = json.loads(args.cards.read_text(encoding="utf-8"))
    errors: list[str] = []
    if payload.get("schema") != "rjc-prova-material-cards-v1":
        errors.append("schema inválido")
    cards = payload.get("cards")
    if not isinstance(cards, list) or not cards:
        errors.append("cards ausentes")
        cards = []
    seen: set[str] = set()
    forbidden = ("captured_on", "today", "mtime", "build", "generated_on")
    for card in cards:
        card_id = card.get("id", "<sem-id>")
        if not isinstance(card_id, str) or card_id in seen:
            error(errors, str(card_id), "id ausente ou duplicado")
            continue
        seen.add(card_id)
        if card.get("estado_publicacao") not in SAFE_STATES:
            error(errors, card_id, "estado_publicacao inválido")
        provenance = card.get("field_provenance")
        if not isinstance(provenance, dict):
            error(errors, card_id, "field_provenance ausente")
            continue
        required = {"titulo_humano", "resumo_humano", "jurisdicao", "ato.tipo", "ato.numero", "ato.data", "ato.autoridade_emissora", "temporal.publicacao", "temporal.inicio_vigencia"}
        if card_id == "br-lc214-ibs-cbs-incidencia-geral":
            required |= {"regra_estruturada.tributos", "regra_estruturada.instituicao", "regra_estruturada.incidencia_geral", "temporal.inicio_eficacia", "regra_estruturada.transicao_rt"}
        else:
            required.add("regra_estruturada.regra")
        missing = required - set(provenance)
        if missing:
            error(errors, card_id, f"proveniência ausente: {sorted(missing)}")
        for key, proof in provenance.items():
            if proof.get("card_id") != card_id or proof.get("campo") != key:
                error(errors, card_id, f"proveniência desalinhada: {key}")
            try:
                if proof.get("valor") != field_value(card, key):
                    error(errors, card_id, f"valor da proveniência diverge do campo: {key}")
            except KeyError:
                error(errors, card_id, f"campo de proveniência não existe no card: {key}")
            additional = proof.get("fundamentos_adicionais", [])
            if not isinstance(additional, list) or any(not isinstance(item, dict) for item in additional):
                error(errors, card_id, f"fundamentos adicionais inválidos: {key}")
                additional = []
            entries = [(key, proof)] + [(f"{key}.fundamento[{index}]", item) for index, item in enumerate(additional, start=1)]
            for entry_key, entry in entries:
                if entry.get("card_id") != card_id:
                    error(errors, card_id, f"fundamento sem card_id correto: {entry_key}")
                if not str(entry.get("url_final", "")).startswith("https://"):
                    error(errors, card_id, f"URL final inválida: {entry_key}")
                if entry.get("http_status") != 200:
                    error(errors, card_id, f"status HTTP não é 200: {entry_key}")
                if not HEX64.fullmatch(str(entry.get("sha256_corpo_bruto", ""))):
                    error(errors, card_id, f"hash bruto inválido: {entry_key}")
                if not entry.get("trecho_literal") or not entry.get("localizador") or not entry.get("regra_normalizacao"):
                    error(errors, card_id, f"trecho/localizador/normalização ausente: {entry_key}")
                if "..." in str(entry.get("trecho_literal", "")) or "…" in str(entry.get("trecho_literal", "")):
                    error(errors, card_id, f"trecho literal truncado por reticências: {entry_key}")
                if len(entry.get("recibos", [])) != 2:
                    error(errors, card_id, f"capturas locais independentes ausentes: {entry_key}")
                if not entry.get("web_tool_references"):
                    error(errors, card_id, f"referência de chamada nativa ausente: {entry_key}")
                serialized = json.dumps(entry, ensure_ascii=False).lower()
                if any(marker in serialized for marker in forbidden):
                    error(errors, card_id, f"marcador de data sintética em {entry_key}")
        temporal = card.get("temporal", {})
        for field in ("publicacao", "inicio_vigencia", "inicio_eficacia", "fim_vigencia"):
            if field not in temporal or temporal[field].get("status") not in {"COMPROVADA", "AUSENTE", "INDETERMINADO", "NÃO_APLICÁVEL"}:
                error(errors, card_id, f"campo temporal inválido: {field}")
        canonical = dict(card)
        expected_hash = canonical.pop("sha256_registro", "")
        actual_hash = hashlib.sha256(json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        if expected_hash != actual_hash:
            error(errors, card_id, "hash do registro divergente")
    if errors:
        print("FALHOU")
        print("\n".join(f"- {item}" for item in errors))
        return 1
    print(f"OK: {len(cards)} cards com proveniência por campo, datas tipadas e dupla captura local.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
