#!/usr/bin/env python3
"""Audit the public PIS/Cofins by NCM dataset."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_NDJSON = ROOT / "data" / "pis-cofins" / "ncm.ndjson"
QUARANTINE_NDJSON = ROOT / "data" / "pis-cofins" / "quarentena.ndjson"

REQUIRED_TOP_LEVEL = {
    "schema",
    "id",
    "ncm",
    "mercadoria_servico",
    "resumo_operacional",
    "pesquisa_texto",
    "leitura_humana",
    "setor",
    "aplicacao",
    "tratamento",
    "tributos",
    "operacao",
    "etapa_cadeia",
    "ato_oficial",
    "trecho_legal",
    "publicacao",
    "inicio_vigencia",
    "inicio_eficacia",
    "vigencia",
    "validity_status",
    "status",
    "condicoes",
    "vedacoes",
    "prova_documental",
    "transicao_cbs",
    "risco",
    "provenance",
    "classification_confidence",
    "validation_status",
    "publishable",
    "verificado_em",
}

VALID_NCM_DIGIT_LENGTHS = {4, 6, 7, 8}
PUBLIC_STATUSES = {"vigente", "historico", "a_revalidar"}
MONEY_FALSE_NCM_RE = re.compile(r"R\$\s*0[,\.]\s*\d{4}\b")


def load_ndjson(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise AssertionError(f"{path}:{lineno}: invalid JSON: {exc}") from exc
    return rows


def validate_public_row(row: dict) -> list[str]:
    errors: list[str] = []
    row_id = str(row.get("id", "<sem-id>"))
    missing = sorted(REQUIRED_TOP_LEVEL - row.keys())
    if missing:
        errors.append(f"{row_id}: missing fields {', '.join(missing)}")
    if row_id.startswith("q-"):
        errors.append(f"{row_id}: quarantine id cannot be public")
    if row.get("publishable") is not True:
        errors.append(f"{row_id}: publishable must be true")
    if row.get("validation_status") != "validado":
        errors.append(f"{row_id}: validation_status must be validado")
    if row.get("status") not in PUBLIC_STATUSES:
        errors.append(f"{row_id}: invalid public status {row.get('status')}")
    if row.get("validity_status") != row.get("status"):
        errors.append(f"{row_id}: validity_status differs from status")
    try:
        confidence = float(row.get("classification_confidence", 0))
    except (TypeError, ValueError):
        confidence = 0
    if confidence < 0.80:
        errors.append(f"{row_id}: classification_confidence below 0.80")
    ato = row.get("ato_oficial") if isinstance(row.get("ato_oficial"), dict) else {}
    if ato.get("http_status") != 200 or not ato.get("url", "").startswith("https://"):
        errors.append(f"{row_id}: official source must be HTTPS HTTP 200")
    ncm = row.get("ncm") if isinstance(row.get("ncm"), dict) else {}
    digits = re.sub(r"\D", "", str(ncm.get("digitos") or ncm.get("codigo") or ""))
    if len(digits) not in VALID_NCM_DIGIT_LENGTHS:
        errors.append(f"{row_id}: invalid NCM/TIPI digit length {digits}")
    if not row.get("publicacao") or not row.get("inicio_vigencia") or not row.get("inicio_eficacia"):
        errors.append(f"{row_id}: incomplete validity dates")
    if not isinstance(row.get("vigencia"), dict) or not row["vigencia"].get("status"):
        errors.append(f"{row_id}: missing inline vigencia envelope")
    if len(str(row.get("mercadoria_servico", "")).strip()) < 40:
        errors.append(f"{row_id}: mercadoria_servico too short for human table")
    resumo = str(row.get("resumo_operacional", "")).strip()
    if len(resumo) < 120 or "PIS/Cofins" not in resumo or str(ncm.get("codigo", "")) not in resumo:
        errors.append(f"{row_id}: resumo_operacional must be human-readable and include NCM/PIS-Cofins")
    pesquisa = str(row.get("pesquisa_texto", "")).strip()
    if len(pesquisa) < 180 or str(ncm.get("digitos", "")) not in pesquisa:
        errors.append(f"{row_id}: pesquisa_texto must support NCM search")
    leitura = row.get("leitura_humana") if isinstance(row.get("leitura_humana"), dict) else {}
    if not leitura.get("resposta_curta") or not isinstance(leitura.get("como_validar"), list) or len(leitura.get("como_validar", [])) < 3:
        errors.append(f"{row_id}: leitura_humana missing resposta_curta/como_validar")
    if not isinstance(leitura.get("nao_usar_sem"), list) or len(leitura.get("nao_usar_sem", [])) < 3:
        errors.append(f"{row_id}: leitura_humana missing nao_usar_sem safeguards")
    legal = str(row.get("trecho_legal", ""))
    if len(legal) < 120:
        errors.append(f"{row_id}: trecho_legal too short")
    if MONEY_FALSE_NCM_RE.search(legal):
        code = str(ncm.get("codigo", ""))
        if code and code in MONEY_FALSE_NCM_RE.search(legal).group(0):
            errors.append(f"{row_id}: possible money amount captured as NCM")
    transition = row.get("transicao_cbs") if isinstance(row.get("transicao_cbs"), dict) else {}
    if not transition.get("status") or not transition.get("referencia"):
        errors.append(f"{row_id}: missing transicao_cbs status/reference")
    provenance = row.get("provenance") if isinstance(row.get("provenance"), dict) else {}
    if provenance.get("origem") != "ato_oficial":
        errors.append(f"{row_id}: provenance must be ato_oficial")
    if not provenance.get("raw_sha256") or not provenance.get("normalized_sha256"):
        errors.append(f"{row_id}: missing source hashes")
    return errors


def main() -> int:
    rows = load_ndjson(PUBLIC_NDJSON)
    quarantine = load_ndjson(QUARANTINE_NDJSON)
    errors: list[str] = []
    if not rows:
        errors.append("data/pis-cofins/ncm.ndjson has no public rows")
    seen: set[str] = set()
    for row in rows:
        row_id = str(row.get("id", ""))
        if row_id in seen:
            errors.append(f"{row_id}: duplicate id")
        seen.add(row_id)
        errors.extend(validate_public_row(row))
    public_text = "\n".join(json.dumps(row, ensure_ascii=False) for row in rows)
    for row in quarantine:
        qid = str(row.get("id", ""))
        if qid and qid in public_text:
            errors.append(f"{qid}: quarantine id appears in public dataset")
    if errors:
        print("\n".join(errors))
        return 1
    print(f"OK: {len(rows)} public PIS/Cofins NCM rows; {len(quarantine)} quarantine rows isolated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
