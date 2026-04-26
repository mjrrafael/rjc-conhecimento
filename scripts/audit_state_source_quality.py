#!/usr/bin/env python3
"""Audit state ICMS source quality before publication."""

from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from state_legal_pages import (  # noqa: E402
    STATE_NAMES,
    collect_state_documents,
    normalize,
)


CURATION = ROOT / "data" / "state_curadoria.json"
OUT_JSON = ROOT / "data" / "state_source_audit.json"
OUT_MD = ROOT / "docs" / "state-source-audit.md"

NOISE_TERMS = {
    "ipva": "IPVA",
    "itcmd": "ITCMD/ITCD",
    "itcd": "ITCMD/ITCD",
    "taxa": "Taxas",
    "taxas": "Taxas",
    "emolumento": "Emolumentos",
}


def load_curation() -> dict:
    if not CURATION.exists():
        return {"statuses": {}}
    return json.loads(CURATION.read_text(encoding="utf-8"))


def quality_flags(doc: dict) -> list[str]:
    text = doc.get("text", "")
    low = normalize(text)
    flags: list[str] = []
    if doc.get("fallback_icms"):
        flags.append("fallback amplo")
    if not doc.get("named_icms"):
        flags.append("categoria não específica de ICMS")
    if "documentos fonte" in low and not re.search(r"https?://", text):
        flags.append("fonte local sem URL oficial no cabeçalho")
    if any(mark in text for mark in ("Ã", "Â", "â€", "ï")):
        flags.append("ruído de extração/encoding")
    if len(text) < 20_000:
        flags.append("texto curto para RICMS/benefícios")
    for term, label in NOISE_TERMS.items():
        if re.search(rf"\b{re.escape(term)}\b", low):
            flags.append(f"contém {label}")
    return sorted(set(flags))


def audit() -> dict:
    curation = load_curation()
    status_map = curation.get("statuses", {})
    report = {
        "generated_on": "2026-04-26",
        "summary": {},
        "states": {},
    }
    totals = Counter()
    for uf in sorted(STATE_NAMES):
        docs = list(collect_state_documents(uf)) if uf != "GO" else []
        status = status_map.get(uf, {})
        categories = Counter(doc.get("category", "") for doc in docs)
        flags_by_doc = {doc["file"]: quality_flags(doc) for doc in docs}
        all_flags = sorted({flag for flags in flags_by_doc.values() for flag in flags})
        duplicate_hashes = [
            digest for digest, count in Counter(doc.get("sha256", "") for doc in docs).items()
            if digest and count > 1
        ]
        if duplicate_hashes:
            all_flags.append("possível duplicidade de fonte")
        if uf != "GO" and status.get("publish_deep"):
            all_flags.append("publicação profunda ativa sem aprovação manual recente")
        recommendation = "manter_publicado" if uf == "GO" else "bloquear_publicacao_ate_curadoria"
        if uf != "GO" and not docs:
            recommendation = "pesquisar_fontes_oficiais_do_zero"
        report["states"][uf] = {
            "estado": STATE_NAMES[uf],
            "region": status.get("region", ""),
            "curadoria": status.get("status", "sem_status"),
            "publish_deep": bool(status.get("publish_deep")),
            "document_count": len(docs),
            "total_chars": sum(int(doc.get("chars", 0)) for doc in docs),
            "categories": dict(sorted(categories.items())),
            "flags": all_flags,
            "recommendation": recommendation,
            "next_step": status.get("next_step", ""),
            "documents": [
                {
                    "file": doc["file"],
                    "category": doc["category"],
                    "chars": doc["chars"],
                    "named_icms": bool(doc.get("named_icms")),
                    "fallback_icms": bool(doc.get("fallback_icms")),
                    "flags": flags_by_doc[doc["file"]],
                }
                for doc in docs
            ],
        }
        totals["states"] += 1
        totals["docs"] += len(docs)
        totals["blocked"] += 1 if recommendation.startswith("bloquear") else 0
    report["summary"] = dict(totals)
    return report


def write_markdown(report: dict) -> None:
    lines = [
        "# Auditoria Da Base Estadual",
        "",
        "Gerado em 26/04/2026.",
        "",
        "Esta auditoria mede qualidade editorial do acervo estadual antes de publicação profunda. Ela não aprova tese tributária; apenas aponta risco de fonte, ruído e escopo.",
        "",
        "## Resumo",
        "",
        f"- Estados avaliados: {report['summary'].get('states', 0)}",
        f"- Documentos estaduais detectados: {report['summary'].get('docs', 0)}",
        f"- Estados bloqueados para publicação profunda: {report['summary'].get('blocked', 0)}",
        "",
        "## Estados",
        "",
        "| UF | Região | Status | Docs | Recomendação | Principais alertas |",
        "| --- | --- | --- | ---: | --- | --- |",
    ]
    for uf, item in report["states"].items():
        flags = ", ".join(item["flags"][:5]) if item["flags"] else "sem alerta automatizado"
        lines.append(
            f"| {uf} | {item['region']} | {item['curadoria']} | {item['document_count']} | {item['recommendation']} | {flags} |"
        )
    lines.extend([
        "",
        "## Leitura Do Resultado",
        "",
        "- `fallback amplo` indica que o portal encontrou a palavra ICMS em categoria genérica, mas não necessariamente um RICMS ou anexo de benefício.",
        "- `ruído de extração/encoding` indica texto vindo de PDF ou HTML com caracteres corrompidos; não deve alimentar explicação didática sem limpeza.",
        "- `contém IPVA/ITCMD/Taxas` indica que o arquivo pode misturar tributos estaduais fora do escopo de ICMS.",
        "- `fonte local sem URL oficial no cabeçalho` indica que o texto pode ser aproveitado como acervo, mas precisa ser amarrado a link oficial antes de publicar.",
    ])
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    report = audit()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    write_markdown(report)
    print(f"Auditoria estadual gravada: {OUT_JSON.relative_to(ROOT)}")
    print(f"Relatorio gravado: {OUT_MD.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
